import asyncio
import json
import os
import sys
import re
from playwright.async_api import async_playwright, Page, BrowserContext

def get_locator_from_selector(page: Page, selector: str):
    """Gets a Playwright locator based on a selector string."""
    if selector.startswith("role="):
        if "[name=" in selector:
            role_part = selector.split("[")[0].replace("role=", "")
            name_part = selector.split('[name="')[1].split('"]')[0]
            return page.get_by_role(role_part, name=name_part, exact=True).first
        else:
            role_part = selector.replace("role=", "")
            return page.get_by_role(role_part, exact=True).first
    elif selector.startswith("[data-testid="):
        test_id = selector.split('="')[1].split('"]')[0]
        return page.get_by_test_id(test_id).first
    elif selector.startswith("placeholder="):
        placeholder = selector.split('="')[1].split('"]')[0]
        return page.get_by_placeholder(placeholder, exact=True).first
    elif selector.startswith("text="):
        match = re.search(r'text="([^"]*)"', selector)
        text_content = match.group(1) if match else None
        return page.get_by_text(text_content, exact=True).first
    elif selector.startswith("label="):
        label = selector.split('="')[1].split('"]')[0]
        return page.get_by_label(label, exact=True).first
    else:
        return page.locator(selector).first

async def wait_for_page_stable(page: Page, timeout: int = 3000):
    """Wait for the page to be stable and ready for interaction."""
    try:
        # Wait for the DOM to be loaded
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
        await asyncio.sleep(1)
    except Exception:
        pass

async def click_and_handle_navigation(page: Page, context: BrowserContext, locator):
    """Click an element and handle potential navigation or new tab/window."""
    current_url = page.url
    current_page_count = len(context.pages)
    
    # Perform the click
    await locator.click()
    
    # Check if a new page/tab was opened
    if len(context.pages) > current_page_count:
        # New tab/window opened, switch to it
        new_page = context.pages[-1]
        await new_page.wait_for_load_state('domcontentloaded')
        print(f"  New tab/window opened, switched to: {new_page.url}")
        return new_page
    elif page.url != current_url:
        # Same tab navigation occurred
        await page.wait_for_load_state('domcontentloaded')
        print(f"  Navigated to: {page.url}")
    
    return page

async def scroll_to_text(page: Page, text: str):
    """Scroll to an element containing the specified text."""
    try:
        # Try to find element with exact text match
        element = page.get_by_text(text, exact=False).first
        await element.scroll_into_view_if_needed(timeout=1000)
        print(f"  Successfully scrolled to text: {text}")
    except Exception:
        # If exact text not found, try with XPath
        try:
            # Escape quotes in text for XPath
            escaped_text = text.replace("'", "\\'").replace('"', '\\"')
            element = page.locator(f"//*[contains(text(), '{escaped_text}')]").first
            await element.scroll_into_view_if_needed(timeout=1000)
            print(f"  Successfully scrolled to text (XPath match): {text}")
        except Exception:
            # As fallback, scroll through the page looking for the text
            print(f"  Could not find element with text, scrolling through page...")
            for i in range(10):  # Max 10 scroll attempts
                # Check if text is visible on current viewport
                is_visible = await page.evaluate('''(text) => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    return elements.some(el => {
                        const rect = el.getBoundingClientRect();
                        return el.textContent && el.textContent.includes(text) && 
                               rect.top >= 0 && rect.bottom <= window.innerHeight;
                    });
                }''', text)
                
                if is_visible:
                    print(f"  Text found in viewport after {i} scrolls")
                    break
                
                # Scroll down by one viewport height
                await page.evaluate('window.scrollBy(0, window.innerHeight)')
                await asyncio.sleep(0.5)

SENSITIVE_DATA = {}

async def run_processed_script():
    global SENSITIVE_DATA
    async with async_playwright() as p:
        browser = None
        context = None
        page = None
        try:
            print('Launching chromium browser...')
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            print('Browser context created.')
            page = await context.new_page()

            print('--- Starting Processed Script Execution ---')

            # --- Step 1 ---
            print(f"Opening new tab: https://www.gutenberg.org/ (Step 1, Action: open_tab)")
            page = await context.new_page()
            await page.goto("https://www.gutenberg.org/", timeout=90000)
            await wait_for_page_stable(page)

            # --- Step 2 ---
            print(f"Inputting text into element: role=textbox[name='Search books'] (Step 2, Action: input_text)")
            locator = get_locator_from_selector(page, "role=textbox[name=\"Search books\"]")
            await locator.fill("Moby Dick")
            await wait_for_page_stable(page)

            # --- Step 3 ---
            print(f"Clicking element: text='Go!' (Step 3, Action: click_element_by_index)")
            locator = get_locator_from_selector(page, "text=\"Go!\"")
            page = await click_and_handle_navigation(page, context, locator)
            await wait_for_page_stable(page)

            # --- Step 4 ---
            print(f"Scrolling down (Step 4, Action: scroll_down)")
            await page.evaluate('window.scrollBy(0, window.innerHeight)')
            await wait_for_page_stable(page)

            # --- Step 5 ---
            print(f"Clicking element: a[href='/ebooks/2701'] (Step 5, Action: click_element_by_index)")
            locator = get_locator_from_selector(page, "a[href=\"/ebooks/2701\"]")
            page = await click_and_handle_navigation(page, context, locator)
            await wait_for_page_stable(page)

            # --- Step 6 ---
            print(f"Clicking element: role=link[name='Read now!'] (Step 6, Action: click_element_by_index)")
            locator = get_locator_from_selector(page, "role=link[name=\"Read now!\"]")
            page = await click_and_handle_navigation(page, context, locator)
            await wait_for_page_stable(page)

            # --- Step 7 ---
            print(f"Navigating back (Step 7, Action: go_back)")
            await page.go_back(timeout=90000)
            await wait_for_page_stable(page)

            print('End of script execution')

            await asyncio.sleep(3)
        except Exception as e:
            print(f'\n--- An error occurred: {e} ---', file=sys.stderr)
            import traceback
            traceback.print_exc()
        finally:
            print('\n--- Script Execution Finished ---')
            if browser:
                await browser.close()
            print('Browser closed.')

if __name__ == '__main__':
    asyncio.run(run_processed_script())