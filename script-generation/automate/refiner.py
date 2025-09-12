import json
import asyncio
from playwright.async_api import Page
from automate.utils.utils import (
    go_back,
    go_to_url,
    open_tab,
    send_keys,
    wait,
    wait_for_page_stable,
    scroll_down,
    scroll_up,
    scroll_to_text,
    switch_tab,
    select_dropdown_option,
)
from automate.utils.selector_util import get_selector
import re

async def execute_action_with_selector(
    page: Page, xpath: str, action: str, text: str = None, css_selector: str = None, attributes: dict = None
) -> tuple[str, Page, bool]:
    """Helper function to get codegen selector and execute action using modern Playwright methods
    
    Returns:
        tuple: (selector, page, new_tab_opened)
    """
    await wait_for_page_stable(page)
    
    # Try to get selector with xpath first, passing attributes if available
    selector, strategy_name = await get_selector(page, xpath, action, attributes)
    
    # Check if the selector is valid by trying to count elements
    try:
        count = await page.locator(selector).count()
        if count == 0:
            raise Exception(f"No elements found with selector: {selector}")
    except Exception as e:
        print(f"  Failed to use selector '{selector}': {e}")
        # If xpath-based selector fails and css_selector is provided, try with css_selector
        if css_selector:
            print(f"  Trying with CSS selector: {css_selector}")
            try:
                # Get selector using CSS
                selector, strategy_name = await get_selector(page, f"css={css_selector}", action, attributes)
                # Validate the CSS-based selector
                count = await page.locator(selector).count()
                if count == 0:
                    raise Exception(f"No elements found with CSS selector: {selector}")
            except Exception as css_e:
                print(f"  Failed to use CSS selector: {css_e}")
                # As a last resort, try using the CSS selector directly
                selector = css_selector
                print(f"  Trying raw CSS selector: {selector}")

    context = page.context
    pages_before = context.pages.copy()  # Create a copy of the pages list
    new_tab_opened = False

    # Current page
    # print("Current page:", page.url, "Xpath:", xpath)
    # with open(f"source.html", "w") as f:
    #     f.write(await page.content())

    try:
        if selector.startswith("role="):
            if "[name=" in selector:
                role_part = selector.split("[")[0].replace("role=", "")
                name_part = selector.split('[name="')[1].split('"]')[0]
                locator = page.get_by_role(role_part, name=name_part, exact=True)
            else:
                role_part = selector.replace("role=", "")
                locator = page.get_by_role(role_part, exact=True)
        elif selector.startswith("[data-testid="):
            test_id = selector.split('="')[1].split('"]')[0]
            locator = page.get_by_test_id(test_id)
        elif selector.startswith("placeholder="):
            placeholder = selector.split('="')[1].split('"]')[0]
            locator = page.get_by_placeholder(placeholder, exact=True)
        elif selector.startswith("text="):
            match = re.search(r'text="([^"]*)"', selector)
            text_content = match.group(1) if match else None
            locator = page.get_by_text(text_content, exact=True)
        elif selector.startswith("label="):
            label = selector.split('="')[1].split('"]')[0]
            locator = page.get_by_label(label, exact=True)
        else:
            locator = page.locator(selector).first

        # Execute the action
        if action == "click":
            # Store the current URL before clicking
            current_url = page.url
            
            # Try to use expect_page if we might get a new page
            new_page_promise = None
            try:
                # Check if the element has target="_blank" or similar
                target = await locator.get_attribute("target")
                if target == "_blank":
                    new_page_promise = context.wait_for_event("page")
            except:
                pass
            
            # Set up navigation promise for same-tab navigation
            navigation_promise = None
            try:
                # Create a promise that will resolve when navigation occurs
                navigation_promise = page.wait_for_navigation(timeout=5000)
            except:
                pass
            
            # Perform the click
            await locator.click(force=True, timeout=5000)
            
            # Check if navigation occurred in the same tab
            navigation_occurred = False
            if navigation_promise:
                try:
                    # Wait a short time to see if navigation starts
                    await asyncio.wait_for(navigation_promise, timeout=2.0)
                    navigation_occurred = True
                    print(f"  Navigation detected to: {page.url}")
                    await page.wait_for_load_state("domcontentloaded")
                except asyncio.TimeoutError:
                    # No navigation occurred within timeout
                    pass
                except Exception as e:
                    # Navigation might have already completed or other error
                    if page.url != current_url:
                        navigation_occurred = True
                        print(f"  Navigation detected to: {page.url}")
            
            # If no navigation in same tab, check for new page/tab
            if not navigation_occurred and new_page_promise:
                try:
                    new_page = await asyncio.wait_for(new_page_promise, timeout=3.0)
                    await new_page.wait_for_load_state("domcontentloaded")
                    print(f"  New tab/window detected, switching to new page: {new_page.url}")
                    new_tab_opened = True
                    return selector, new_page, new_tab_opened
                except asyncio.TimeoutError:
                    pass
            
            # If still no navigation detected, wait a moment and check for new pages
            if not navigation_occurred:
                await asyncio.sleep(1)
                pages_after = context.pages
                new_pages = [p for p in pages_after if p not in pages_before]
                
                if new_pages:
                    new_page = new_pages[-1]
                    await new_page.wait_for_load_state("domcontentloaded")
                    print(f"  New tab/window detected, switching to new page: {new_page.url}")
                    new_tab_opened = True
                    return selector, new_page, new_tab_opened
            
            # Final check: if URL changed but we didn't detect it earlier
            if page.url != current_url:
                print(f"  Page navigated from {current_url} to {page.url}")
                await page.wait_for_load_state("domcontentloaded")

        elif action == "fill":
            await locator.fill(text)

        print(f"  Action '{action}' successful with generated selector")

    except Exception as e:
        print(f"  Error with generated selector: {e}")
        # Even if there's an error, check if a new page was opened
        pages_after = context.pages
        new_pages = [p for p in pages_after if p not in pages_before]
        
        if new_pages:
            new_page = new_pages[-1]  # Get the most recent new page
            try:
                await new_page.wait_for_load_state("domcontentloaded", timeout=5000)
                print(f"  New tab/window detected after error, switching to new page: {new_page.url}")
                new_tab_opened = True
                return selector, new_page, new_tab_opened
            except Exception:
                pass
        
        raise e

    return selector, page, new_tab_opened, strategy_name


async def process_action_list(page, action_list):
    """Process a single action list and return the processed actions"""
    processed_action_list = []
    context = page.context  # Get context from page

    for index, action in enumerate(action_list):
        print("------------------------------------")
        print("index:", index)
        print("action:", action)
        try:
            for key, value in action.items():
                # Check if the current page is still valid before each action
                try:
                    # Quick check to see if page is still accessible
                    await page.evaluate("() => true")
                except Exception:
                    # If page is closed, try to get the latest page from context
                    if context.pages:
                        page = context.pages[-1]  # Get the most recent page
                        await page.wait_for_load_state("networkidle")
                        print(f"  Switched to most recent page: {page.url}")
                    else:
                        print("  No valid pages found in context")
                        break
                
                await wait_for_page_stable(page)
                print(key, value)
                if key == "go_to_url":
                    await go_to_url(value["url"], page)
                    processed_action_list.append({
                        "action": key,
                        "url": value["url"]
                    })

                elif key == "click_element_by_index":
                    css_selector = value.get('css_selector', None)  # Get CSS selector if available
                    attributes = value.get('attributes', None)  # Get attributes if available
                    selector, new_page, new_tab_opened, strategy_name = await execute_action_with_selector(
                        page, f"xpath={value['xpath']}", "click", css_selector=css_selector, attributes=attributes
                    )
                    # Update the page reference if a new page was returned
                    if new_page != page:
                        page = new_page
                    
                    processed_action_list.append({
                        "action": key,
                        "selector": selector,
                        "strategy_name": strategy_name
                    })
                    
                    # If a new tab was opened, add a switch_tab action
                    if new_tab_opened:
                        # Find the index of the new page
                        page_index = context.pages.index(page)
                        processed_action_list.append({
                            "action": "switch_tab",
                            "page_id": page_index
                        })

                elif key == "wait":
                    await wait(value["seconds"])
                    processed_action_list.append({
                        "action": key,
                        "seconds": value["seconds"]
                    })

                elif key == "input_text":
                    css_selector = value.get('css_selector', None)  # Get CSS selector if available
                    attributes = value.get('attributes', None)  # Get attributes if available
                    selector, new_page, new_tab_opened, strategy_name = await execute_action_with_selector(
                        page, f"xpath={value['xpath']}", "fill", value["text"], css_selector=css_selector, attributes=attributes
                    )
                    # Update the page reference if a new page was returned
                    if new_page != page:
                        page = new_page
                    processed_action_list.append({
                        "action": key,
                        "selector": selector,
                        "strategy_name": strategy_name,
                        "text": value["text"]
                    })

                elif key == "scroll_to_text":
                    await scroll_to_text(value["text"], page)
                    processed_action_list.append({
                        "action": key,
                        "text": value["text"]
                    })

                elif key == "go_back":
                    await go_back(page)
                    processed_action_list.append({
                        "action": key,
                    })

                elif key == "scroll_down":
                    await scroll_down(page)
                    processed_action_list.append({
                        "action": key,
                    })

                elif key == "scroll_up":
                    await scroll_up(page)
                    processed_action_list.append({
                        "action": key,
                    })

                elif key == "open_tab":
                    page = await open_tab(value["url"], page)
                    processed_action_list.append({
                        "action": key,
                        "url": value["url"]
                    })

                elif key == "switch_tab":
                    page = await switch_tab(value["page_id"], page)
                    processed_action_list.append({
                        "action": key,
                        "page_id": value["page_id"]
                    })

                elif key == "send_keys":
                    await send_keys(value["keys"], page)
                    processed_action_list.append({
                        "action": key,
                        "keys": value["keys"]
                    })

                elif key == "select_dropdown_option":
                    css_selector = value.get('css_selector', None)  # Get CSS selector if available
                    attributes = value.get('attributes', None)  # Get attributes if available
                    # Try to get selector with xpath first, fallback to css if needed
                    try:
                        selector, strategy_name = await get_selector(page, f"xpath={value['xpath']}", "select", attributes)
                    except Exception as e:
                        if css_selector:
                            print(f"  Failed to get selector with xpath, trying CSS: {css_selector}")
                            selector, strategy_name = await get_selector(page, f"css={css_selector}", "select", attributes)
                        else:
                            raise e
                    
                    await select_dropdown_option(value["xpath"], value["text"], page)
                    processed_action_list.append({
                        "action": key,
                        "selector": selector,
                        "strategy_name": strategy_name,
                        "text": value["text"]
                    })
                # elif key == "save_pdf":
                #     await save_pdf(page)
                #     processed_action_list.append({
                #         "action": key,
                #     })

        except Exception as e:
            print(f"Error executing action {index}: {str(e)}")
            print("Skipping to next action...")
            # Try to recover by getting the latest page
            context = page.context if hasattr(page, 'context') else None
            if context and context.pages:
                page = context.pages[-1]
                print(f"  Recovered with page: {page.url}")
            continue
    
    return processed_action_list
