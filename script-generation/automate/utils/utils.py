import asyncio
import logging
import re

from playwright.async_api import Page
from automate.utils.selector_util import get_selector

logger = logging.getLogger(__name__)


async def wait_for_page_stable(page: Page, timeout: int = 3000):
    """Wait for the page to be stable (no network activity, no animations)."""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
        await asyncio.sleep(1)
    except Exception as e:
        logger.debug(f"Timeout waiting for page to stabilize: {e}")


async def go_to_url(url: str, page: Page):
    await page.goto(url)
    await wait_for_page_stable(page)
    msg = f"🔗  Navigated to {url}"
    logger.info(msg)


async def scroll_to_text(text: str, page: Page):
    try:
        # Try different locator strategies
        locators = [
            page.get_by_text(text, exact=False),
            page.locator(f"text={text}"),
            page.locator(f"//*[contains(text(), '{text}')]"),
        ]

        for locator in locators:
            try:
                if await locator.count() == 0:
                    continue

                element = await locator.first
                is_visible = await element.is_visible()
                bbox = await element.bounding_box()

                if (
                    is_visible
                    and bbox is not None
                    and bbox["width"] > 0
                    and bbox["height"] > 0
                ):
                    await element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    msg = f"🔍  Scrolled to text: {text}"
                    logger.info(msg)
                    return

            except Exception as e:
                logger.debug(f"Locator attempt failed: {str(e)}")
                continue

        msg = f"Text '{text}' not found or not visible on page"
        logger.info(msg)

    except Exception as e:
        msg = f"Failed to scroll to text '{text}': {str(e)}"
        logger.error(msg)


async def wait(seconds: int = 3):
    msg = f"🕒  Waiting for {seconds} seconds"
    logger.info(msg)
    await asyncio.sleep(seconds)


class PlaywrightActionError(Exception):
    """Custom exception for errors during Playwright script action execution."""

    pass


async def go_back(page: Page):
    """Navigate the agent's tab back in browser history"""
    try:
        await page.go_back(timeout=3000, wait_until="domcontentloaded")
        msg = f"⏮️  Navigated back"
        logger.info(msg)
    except Exception as e:
        # Continue even if its not fully loaded, because we wait later for the page to load
        logger.debug(f"⏮️  Error during go_back: {e}")


async def scroll_down(page: Page):
    dy = await page.evaluate("() => window.innerHeight")
    try:
        await page._scroll_container(dy)
        msg = f"🔍 Scrolled down the page by {dy} pixels"
        logger.info(msg)
    except Exception as e:
        # Hard fallback: always works on root scroller
        await page.evaluate("(y) => window.scrollBy(0, y)", dy)
        logger.debug("Smart scroll failed; used window.scrollBy fallback", exc_info=e)


async def scroll_up(page: Page):
    dy = await page.evaluate("() => window.innerHeight")
    try:
        await page._scroll_container(-dy)
        msg = f"🔍 Scrolled up the page by {dy} pixels"
        logger.info(msg)
    except Exception as e:
        # Hard fallback: always works on root scroller
        await page.evaluate("(y) => window.scrollBy(0, y)", -dy)
        logger.debug("Smart scroll failed; used window.scrollBy fallback", exc_info=e)


async def open_tab(url: str, page: Page) -> Page:
    """Open a new tab and navigate to the specified URL"""
    new_page = await page.context.new_page()
    await new_page.goto(url)
    await wait_for_page_stable(new_page)
    # Bring the new page to front
    await new_page.bring_to_front()
    msg = f"🔗  Opened new tab with {url}"
    logger.info(msg)
    return new_page


async def switch_tab(tab_index: int, page: Page) -> Page:
    pages = page.context.pages
    print(pages)
    if not pages or tab_index >= len(pages):
        raise IndexError("Tab index out of range")
    new_page = pages[tab_index]
    # Bring the page to front
    await new_page.bring_to_front()
    logger.info(f"Switched to tab {tab_index}")
    return new_page


async def send_keys(keys: str, page: Page):
    try:
        await page.keyboard.press(keys)
    except Exception as e:
        if "Unknown key" in str(e):
            # loop over the keys and try to send each one
            for key in keys:
                try:
                    await page.keyboard.press(key)
                except Exception as e:
                    logger.debug(f"Error sending key {key}: {str(e)}")
                    raise e
        else:
            raise e
    msg = f"⌨️  Sent keys: {keys}"
    logger.info(msg)
    return msg


async def save_pdf(page: Page):
    short_url = re.sub(r"^https?://(?:www\.)?|/$", "", page.url)
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", short_url).strip("-").lower()
    sanitized_filename = f"{slug}.pdf"

    await page.emulate_media(media="screen")
    await page.pdf(path=sanitized_filename, format="A4", print_background=False)
    msg = f"Saving page with URL {page.url} as PDF to ./{sanitized_filename}"
    logger.info(msg)
    return msg

async def select_dropdown_option(xpath: str, text: str, page: Page):
    """Select an option from a dropdown by its visible text.
    
    This function converts the provided XPath to a modern Playwright selector
    using the selector_util.get_selector function, then selects the option
    with the specified visible text.
    
    Parameters
    ----------
    xpath : str
        The XPath to the <select> element (will be converted to a modern selector)
    text : str
        The visible text of the option to select
    page : Page
        The Playwright Page object
    
    Returns
    -------
    str
        A message describing the result of the operation
    """
    await wait_for_page_stable(page)
    
    # Convert XPath to a modern selector using the same approach as other actions
    selector, strategy_name = await get_selector(page, f"xpath={xpath}")
    
    try:
        # Get the locator based on the selector type
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
            locator = page.get_by_test_id(test_id, exact=True)
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
            
        # Verify it's a select element
        tag_name = await locator.evaluate("el => el.tagName.toLowerCase()")
        if tag_name != "select":
            msg = f"⚠️ Element with selector '{selector}' is a {tag_name}, not a select element"
            logger.warning(msg)
            return msg
            
        # Select the option by visible text (label)
        selected_values = await locator.select_option(label=text, timeout=3000)
        
        msg = f"✅ Selected option '{text}' (value={selected_values}) in dropdown with selector '{selector}'"
        logger.info(msg)
        
        # Give the page a moment to process any resulting changes
        await wait_for_page_stable(page)
        return msg
        
    except Exception as e:
        msg = f"❌ Failed to select option '{text}' in dropdown: {e}"
        logger.error(msg)
        return msg

# async def _try_locate_and_act(
#     page: Page,
#     selector: str,
#     action_type: str,
#     text: str | None = None,
#     step_info: str = "",
# ) -> None:
#     """
#     Attempts an action (click/fill) with XPath fallback by trimming prefixes.
#     Raises PlaywrightActionError if the action fails after all fallbacks.
#     """
#     print(f"Attempting {action_type} ({step_info}) using selector: {repr(selector)}")
#     original_selector = selector
#     MAX_FALLBACKS = 10  # Increased fallbacks
#     # Increased timeouts for potentially slow pages
#     INITIAL_TIMEOUT = 3000  # Milliseconds for the first attempt (3 seconds)
#     FALLBACK_TIMEOUT = 1000  # Shorter timeout for fallback attempts (0.5 seconds)

#     try:
#         locator = page.locator(selector).first
#         if action_type == "click":
#             await locator.click(timeout=INITIAL_TIMEOUT)
#         elif action_type == "fill" and text is not None:
#             await locator.fill(text, timeout=INITIAL_TIMEOUT)
#         else:
#             # This case should ideally not happen if called correctly
#             raise PlaywrightActionError(
#                 f"Invalid action_type '{action_type}' or missing text for fill. ({step_info})"
#             )
#         print(f"  Action '{action_type}' successful with original selector.")
#         await page.wait_for_timeout(500)  # Wait after successful action
#         return  # Successful exit
#     except Exception as e:
#         print(
#             f"  Warning: Action '{action_type}' failed with original selector ({repr(selector)}): {e}. Starting fallback..."
#         )

#         # Fallback only works for XPath selectors
#         if not selector.startswith("xpath="):
#             # Raise error immediately if not XPath, as fallback won't work
#             raise PlaywrightActionError(
#                 f"Action '{action_type}' failed. Fallback not possible for non-XPath selector: {repr(selector)}. ({step_info})"
#             )

#         xpath_parts = selector.split("=", 1)
#         if len(xpath_parts) < 2:
#             raise PlaywrightActionError(
#                 f"Action '{action_type}' failed. Could not extract XPath string from selector: {repr(selector)}. ({step_info})"
#             )
#         xpath = xpath_parts[1]  # Correctly get the XPath string

#         segments = [seg for seg in xpath.split("/") if seg]

#         for i in range(1, min(MAX_FALLBACKS + 1, len(segments))):
#             trimmed_xpath_raw = "/".join(segments[i:])
#             fallback_xpath = f"xpath=//{trimmed_xpath_raw}"

#             print(
#                 f"    Fallback attempt {i}/{MAX_FALLBACKS}: Trying selector: {repr(fallback_xpath)}"
#             )
#             try:
#                 locator = page.locator(fallback_xpath).first
#                 if action_type == "click":
#                     await locator.click(timeout=FALLBACK_TIMEOUT)
#                 elif action_type == "fill" and text is not None:
#                     try:
#                         await locator.clear(timeout=FALLBACK_TIMEOUT)
#                         await page.wait_for_timeout(100)
#                     except Exception as clear_error:
#                         print(
#                             f"    Warning: Failed to clear field during fallback ({step_info}): {clear_error}"
#                         )
#                     await locator.fill(text, timeout=FALLBACK_TIMEOUT)

#                 print(
#                     f"    Action '{action_type}' successful with fallback selector: {repr(fallback_xpath)}"
#                 )
#                 await page.wait_for_timeout(500)
#                 return  # Successful exit after fallback
#             except Exception as fallback_e:
#                 print(f"    Fallback attempt {i} failed: {fallback_e}")
#                 if i == MAX_FALLBACKS:
#                     # Raise exception after exhausting fallbacks
#                     raise PlaywrightActionError(
#                         f"Action '{action_type}' failed after {MAX_FALLBACKS} fallback attempts. Original selector: {repr(original_selector)}. ({step_info})"
#                     )

#     # This part should not be reachable if logic is correct, but added as safeguard
#     raise PlaywrightActionError(
#         f"Action '{action_type}' failed unexpectedly for {repr(original_selector)}. ({step_info})"
#     )


# async def click_element_by_index(xpath: str, page: Page):
#     try:
#         await wait_for_page_stable(page)

#         # First try using Playwright's locator API
#         try:
#             element = page.locator(xpath)
#             if await element.count() > 0:
#                 await element.click()
#                 msg = f'🖱️  Clicked element with xpath {xpath}'
#                 logger.info(msg)
#                 logger.debug(f'Element xpath: {xpath}')
#                 await wait_for_page_stable(page)
#                 return
#         except Exception as e:
#             logger.debug(f'Playwright locator failed: {e}')

#         # Fallback to JavaScript evaluation if locator fails
#         try:
#             element_handle = await page.evaluate_handle(f'document.evaluate("{xpath}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue')
#             if element_handle:
#                 await element_handle.click()
#                 msg = f'🖱️  Clicked element with xpath {xpath}'
#                 logger.info(msg)
#                 logger.debug(f'Element xpath: {xpath}')
#                 await wait_for_page_stable(page)
#                 return
#         except Exception as e:
#             logger.debug(f'JavaScript evaluation failed: {e}')

#         logger.warning(f'Element not clickable with xpath {xpath} - skipping action')
#         return

#     except Exception as e:
#         logger.warning(f'Failed to click element with xpath {xpath} - skipping action - {e}')
#         return

# async def input_text(xpath: str, text: str, page: Page):
#     try:
#         await wait_for_page_stable(page)

#         element_handle = await page.evaluate_handle(f'document.evaluate("{xpath}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue')
#         if element_handle:
#             await element_handle.fill(text)
#             msg = f'⌨️  Input {text} into xpath {xpath}'
#             logger.info(msg)
#             logger.debug(f'Element xpath: {xpath}')
#             await wait_for_page_stable(page)
#             return
#     except Exception as e:
#         logger.warning(f'Failed to input text into element {xpath} - skipping action - {e}')
#         return
