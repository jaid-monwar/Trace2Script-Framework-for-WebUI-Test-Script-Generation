import json
import logging
from typing import Any

from automate.utils.browser_config import BrowserConfig, BrowserContextConfig


class ProcessedScriptGenerator:
    """Generates a Playwright script from a processed action list."""

    def __init__(
        self,
        action_list: list[dict[str, Any]],
        sensitive_data_keys: list[str] | None = None,
        browser_config: BrowserConfig | None = None,
        context_config: BrowserContextConfig | None = None,
    ):
        self.action_list = action_list
        self.sensitive_data_keys = sensitive_data_keys or []
        self.browser_config = browser_config
        self.context_config = context_config
        self._imports_helpers_added = False

        # Simplified action handlers for processed actions
        self._action_handlers = {
            "go_to_url": self._map_go_to_url,
            "wait": self._map_wait,
            "input_text": self._map_input_text,
            "click_element_by_index": self._map_click_element,
            "click_element": self._map_click_element,
            "scroll_down": self._map_scroll_down,
            "scroll_up": self._map_scroll_up,
            "scroll_to_text": self._map_scroll_to_text,
            "send_keys": self._map_send_keys,
            "go_back": self._map_go_back,
            "open_tab": self._map_open_tab,
            "close_tab": self._map_close_tab,
            "switch_tab": self._map_switch_tab,
            "select_dropdown_option": self._map_select_dropdown_option,
            "done": self._map_done,
        }

    def _generate_browser_launch_args(self) -> str:
        """Generates the arguments string for browser launch based on BrowserConfig."""
        if not self.browser_config:
            return "headless=False"

        args_dict = {"headless": self.browser_config.headless}
        if self.browser_config.proxy:
            args_dict["proxy"] = self.browser_config.proxy.model_dump()
        args_dict = {k: v for k, v in args_dict.items() if v is not None}
        return ", ".join(f"{key}={repr(value)}" for key, value in args_dict.items())

    def _generate_context_options(self) -> str:
        """Generates the options string for context creation based on BrowserContextConfig."""
        if not self.context_config:
            return ""
        options_dict = {}

        if self.context_config.user_agent:
            options_dict["user_agent"] = self.context_config.user_agent
        if self.context_config.locale:
            options_dict["locale"] = self.context_config.locale
        if self.context_config.permissions:
            options_dict["permissions"] = self.context_config.permissions
        if self.context_config.geolocation:
            options_dict["geolocation"] = self.context_config.geolocation
        if self.context_config.timezone_id:
            options_dict["timezone_id"] = self.context_config.timezone_id
        if self.context_config.http_credentials:
            options_dict["http_credentials"] = self.context_config.http_credentials
        if self.context_config.is_mobile is not None:
            options_dict["is_mobile"] = self.context_config.is_mobile
        if self.context_config.has_touch is not None:
            options_dict["has_touch"] = self.context_config.has_touch
        if self.context_config.save_recording_path:
            options_dict["record_video_dir"] = self.context_config.save_recording_path
        if self.context_config.save_har_path:
            options_dict["record_har_path"] = self.context_config.save_har_path
        if self.context_config.no_viewport:
            options_dict["no_viewport"] = True
        elif hasattr(self.context_config, "window_width") and hasattr(
            self.context_config, "window_height"
        ):
            options_dict["viewport"] = {
                "width": self.context_config.window_width,
                "height": self.context_config.window_height,
            }
        options_dict = {k: v for k, v in options_dict.items() if v is not None}
        return ", ".join(f"{key}={repr(value)}" for key, value in options_dict.items())

    def _get_imports_and_helpers(self) -> list[str]:
        """Generates necessary import statements and helper functions."""
        return [
            "import asyncio",
            "import json",
            "import os",
            "import sys",
            "import re",
            "from playwright.async_api import async_playwright, Page, BrowserContext",
            "",
            "def get_locator_from_selector(page: Page, selector: str):",
            '    """Gets a Playwright locator based on a selector string."""',
            '    if selector.startswith("role="):',
            '        if "[name=" in selector:',
            '            role_part = selector.split("[")[0].replace("role=", "")',
            "            name_part = selector.split('[name=\"')[1].split('\"]')[0]",
            "            return page.get_by_role(role_part, name=name_part, exact=True).first",
            "        else:",
            '            role_part = selector.replace("role=", "")',
            "            return page.get_by_role(role_part, exact=True).first",
            '    elif selector.startswith("[data-testid="):',
            "        test_id = selector.split('=\"')[1].split('\"]')[0]",
            "        return page.get_by_test_id(test_id).first",
            '    elif selector.startswith("placeholder="):',
            "        placeholder = selector.split('=\"')[1].split('\"]')[0]",
            "        return page.get_by_placeholder(placeholder, exact=True).first",
            '    elif selector.startswith("text="):',
            '        match = re.search(r\'text="([^"]*)"\', selector)',
            "        text_content = match.group(1) if match else None",
            "        return page.get_by_text(text_content, exact=True).first",
            '    elif selector.startswith("label="):',
            "        label = selector.split('=\"')[1].split('\"]')[0]",
            "        return page.get_by_label(label, exact=True).first",
            "    else:",
            "        return page.locator(selector).first",
            "",
            "async def wait_for_page_stable(page: Page, timeout: int = 3000):",
            '    """Wait for the page to be stable and ready for interaction."""',
            "    try:",
            "        # Wait for the DOM to be loaded",
            '        await page.wait_for_load_state("domcontentloaded", timeout=timeout)',
            "        await asyncio.sleep(1)",
            "    except Exception:",
            "        pass",
            "",
            "async def click_and_handle_navigation(page: Page, context: BrowserContext, locator):",
            '    """Click an element and handle potential navigation or new tab/window."""',
            "    current_url = page.url",
            "    current_page_count = len(context.pages)",
            "    ",
            "    # Perform the click",
            "    await locator.click()",
            "    ",
            "    # Check if a new page/tab was opened",
            "    if len(context.pages) > current_page_count:",
            "        # New tab/window opened, switch to it",
            "        new_page = context.pages[-1]",
            "        await new_page.wait_for_load_state('domcontentloaded')",
            '        print(f"  New tab/window opened, switched to: {new_page.url}")',
            "        return new_page",
            "    elif page.url != current_url:",
            "        # Same tab navigation occurred",
            "        await page.wait_for_load_state('domcontentloaded')",
            '        print(f"  Navigated to: {page.url}")',
            "    ",
            "    return page",
            "",
            "async def scroll_to_text(page: Page, text: str):",
            '    """Scroll to an element containing the specified text."""',
            "    try:",
            "        # Try to find element with exact text match",
            "        element = page.get_by_text(text, exact=False).first",
            "        await element.scroll_into_view_if_needed(timeout=1000)",
            '        print(f"  Successfully scrolled to text: {text}")',
            "    except Exception:",
            "        # If exact text not found, try with XPath",
            "        try:",
            "            # Escape quotes in text for XPath",
            "            escaped_text = text.replace(\"'\", \"\\\\'\").replace('\"', '\\\\\"')",
            "            element = page.locator(f\"//*[contains(text(), '{escaped_text}')]\").first",
            "            await element.scroll_into_view_if_needed(timeout=1000)",
            '            print(f"  Successfully scrolled to text (XPath match): {text}")',
            "        except Exception:",
            "            # As fallback, scroll through the page looking for the text",
            '            print(f"  Could not find element with text, scrolling through page...")',
            "            for i in range(10):  # Max 10 scroll attempts",
            "                # Check if text is visible on current viewport",
            "                is_visible = await page.evaluate('''(text) => {",
            "                    const elements = Array.from(document.querySelectorAll('*'));",
            "                    return elements.some(el => {",
            "                        const rect = el.getBoundingClientRect();",
            "                        return el.textContent && el.textContent.includes(text) && ",
            "                               rect.top >= 0 && rect.bottom <= window.innerHeight;",
            "                    });",
            "                }''', text)",
            "                ",
            "                if is_visible:",
            '                    print(f"  Text found in viewport after {i} scrolls")',
            "                    break",
            "                ",
            "                # Scroll down by one viewport height",
            "                await page.evaluate('window.scrollBy(0, window.innerHeight)')",
            "                await asyncio.sleep(0.5)",
            "",
        ]

    def _get_sensitive_data_definitions(self) -> list[str]:
        """Generates the SENSITIVE_DATA dictionary definition."""
        if not self.sensitive_data_keys:
            return ["SENSITIVE_DATA = {}", ""]

        lines = ["# Sensitive data placeholders mapped to environment variables"]
        lines.append("SENSITIVE_DATA = {")
        for key in self.sensitive_data_keys:
            env_var_name = key.upper()
            default_value_placeholder = f"YOUR_{env_var_name}"
            lines.append(
                f'    "{key}": os.getenv("{env_var_name}", {json.dumps(default_value_placeholder)}),'
            )
        lines.append("}")
        lines.append("")
        return lines

    def _get_goto_timeout(self) -> int:
        """Gets the page navigation timeout in milliseconds."""
        default_timeout = 90000  # Default 90 seconds
        if self.context_config and self.context_config.maximum_wait_page_load_time:
            return int(self.context_config.maximum_wait_page_load_time * 1000)
        return default_timeout

    # --- Simplified Action Mapping Methods ---
    def _map_go_to_url(self, action: dict, step_info_str: str) -> list[str]:
        url = action.get("url")
        goto_timeout = self._get_goto_timeout()
        if url:
            escaped_url = json.dumps(url)
            return [
                f'            print(f"Navigating to: {url} ({step_info_str})")',
                f"            await page.goto({escaped_url}, timeout={goto_timeout})",
                f"            await wait_for_page_stable(page)",
            ]
        return [f"            # Skipping go_to_url ({step_info_str}): missing url"]

    def _map_wait(self, action: dict, step_info_str: str) -> list[str]:
        seconds = action.get("seconds", 3)
        return [
            f'            print(f"Waiting for {seconds} seconds... ({step_info_str})")',
            f"            await asyncio.sleep({seconds})",
        ]

    def _map_input_text(self, action: dict, step_info_str: str) -> list[str]:
        selector = action.get("selector")
        text = action.get("text", "")
        if selector:
            clean_text = f"{json.dumps(str(text))}"
            return [
                f'            print(f"Inputting text into element: {selector.replace("\"", "'").replace("\n", "")} ({step_info_str.replace("\"", "'").replace("\n", "")})")',
                f"            locator = get_locator_from_selector(page, {json.dumps(selector)})",
                f"            await locator.fill({clean_text})",
                f"            await wait_for_page_stable(page)",
            ]
        return [
            f"            # Skipping input_text ({step_info_str}): missing selector"
        ]

    def _map_click_element(self, action: dict, step_info_str: str) -> list[str]:
        selector = action.get("selector")
        if selector:
            return [
                f'            print(f"Clicking element: {selector.replace("\"", "'").replace("\n"," ")} ({step_info_str.replace("\"", "'")})")',
                f"            locator = get_locator_from_selector(page, {json.dumps(selector)})",
                "            page = await click_and_handle_navigation(page, context, locator)",
                f"            await wait_for_page_stable(page)",
            ]
        return [
            f"            # Skipping click_element ({step_info_str}): missing selector"
        ]

    def _map_scroll_down(self, action: dict, step_info_str: str) -> list[str]:
        return [
            f'            print(f"Scrolling down ({step_info_str})")',
            "            await page.evaluate('window.scrollBy(0, window.innerHeight)')",
            f"            await wait_for_page_stable(page)",
        ]

    def _map_scroll_up(self, action: dict, step_info_str: str) -> list[str]:
        return [
            f'            print(f"Scrolling up ({step_info_str})")',
            "            await page.evaluate('window.scrollBy(0, -window.innerHeight)')",
            f"            await wait_for_page_stable(page)",
        ]

    def _map_scroll_to_text(self, action: dict, step_info_str: str) -> list[str]:
        text = action.get("text", "")
        if text:
            escaped_text = json.dumps(text)
            return [
                f'            print(f"Scrolling to text: {text} ({step_info_str})")',
                f"            await scroll_to_text(page, {escaped_text})",
                f"            await wait_for_page_stable(page)",
            ]
        return [
            f"            # Skipping scroll_to_text ({step_info_str}): missing text"
        ]

    def _map_send_keys(self, action: dict, step_info_str: str) -> list[str]:
        keys = action.get("keys")
        if keys:
            # Check if it's a special key or regular text
            special_keys = ["Enter", "Tab", "Escape", "ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight", "Backspace", "Delete", "Home", "End", "PageUp", "PageDown", "Control", "Alt", "Shift", "Meta"]
            if keys in special_keys:
                return [
                    f'            print(f"Sending key: {keys} ({step_info_str})")',
                    f"            await page.keyboard.press({json.dumps(keys)})",
                    f"            await wait_for_page_stable(page)",
                ]
            else:
                return [
                    f'            print(f"Typing text: {keys} ({step_info_str})")',
                    f"            await page.keyboard.type({json.dumps(keys)})",
                    f"            await wait_for_page_stable(page)",
                ]
        return [f"            # Skipping send_keys ({step_info_str}): missing keys"]

    def _map_select_dropdown_option(self, action: dict, step_info_str: str) -> list[str]:
        selector = action.get("selector")
        text = action.get("text", "")
        if selector and text:
            return [
                f'            print(f"Selecting option \'{text}\' in dropdown: {selector.replace("\"", "\'").replace("\\n", "")} ({step_info_str.replace("\"", "\'").replace("\\n", "")})")',
                f"            locator = get_locator_from_selector(page, {json.dumps(selector)})",
                f"            await locator.select_option(label={json.dumps(text)})",
                f"            await wait_for_page_stable(page)",
            ]
        return [
            f"            # Skipping select_dropdown_option ({step_info_str}): missing selector or text"
        ]

    def _map_go_back(self, action: dict, step_info_str: str) -> list[str]:
        goto_timeout = self._get_goto_timeout()
        return [
            f'            print(f"Navigating back ({step_info_str})")',
            f"            await page.go_back(timeout={goto_timeout})",
            f"            await wait_for_page_stable(page)",
        ]

    def _map_open_tab(self, action: dict, step_info_str: str) -> list[str]:
        url = action.get("url")
        goto_timeout = self._get_goto_timeout()
        if url:
            return [
                f'            print(f"Opening new tab: {url} ({step_info_str})")',
                "            page = await context.new_page()",
                f"            await page.goto({json.dumps(url)}, timeout={goto_timeout})",
                f"            await wait_for_page_stable(page)",
            ]
        return [f"            # Skipping open_tab ({step_info_str}): missing url"]

    def _map_close_tab(self, action: dict, step_info_str: str) -> list[str]:
        page_id = action.get("page_id")
        return [
            f'            print(f"Closing tab (Note: page_id {page_id} is indicative, closing current page) ({step_info_str})")',
            "            await page.close()",
            "            if context.pages: page = context.pages[-1]",
        ]

    def _map_switch_tab(self, action: dict, step_info_str: str) -> list[str]:
        page_id = action.get("page_id")
        if page_id is not None:
            return [
                f'            print(f"Switching to tab index {page_id} ({step_info_str})")',
                f"            if {page_id} < len(context.pages):",
                f"                page = context.pages[{page_id}]",
                "                await page.bring_to_front()",
                f"                await wait_for_page_stable(page)",
                "            else:",
                f'                print(f"  Warning: Tab index {page_id} not found.")',
            ]
        return [f"            # Skipping switch_tab ({step_info_str}): missing page_id"]

    def _map_done(self, action: dict, step_info_str: str) -> list[str]:
        final_text = action.get("text", "")
        success_status = action.get("success", False)
        final_message = f"{json.dumps(str(final_text))}"
        return [
            f'            print("\\n--- Task Done ({step_info_str}) ---")',
            f'            print(f"Success: {success_status}")',
            f'            print(f"Final Message: {{ {final_message} }}")',
        ]

    def generate_script_content(self) -> str:
        """Generates the full Playwright script content as a string."""
        script_lines = []
        if not self._imports_helpers_added:
            script_lines.extend(self._get_imports_and_helpers())
            self._imports_helpers_added = True

        script_lines.extend(self._get_sensitive_data_definitions())

        browser_launch_args = self._generate_browser_launch_args()
        context_options = self._generate_context_options()
        browser_type = "chromium"
        if self.browser_config and self.browser_config.browser_class in [
            "firefox",
            "webkit",
        ]:
            browser_type = self.browser_config.browser_class

        script_lines.extend(
            [
                "async def run_processed_script():",
                "    global SENSITIVE_DATA",
                "    async with async_playwright() as p:",
                "        browser = None",
                "        context = None",
                "        page = None",
                "        try:",
                f"            print('Launching {browser_type} browser...')",
                f"            browser = await p.{browser_type}.launch({browser_launch_args})",
                f"            context = await browser.new_context({context_options})",
                "            print('Browser context created.')",
                "            page = await context.new_page()",
                "",
                "            print('--- Starting Processed Script Execution ---')",
            ]
        )

        for index, action in enumerate(self.action_list):
            script_lines.append(f"\n            # --- Step {index + 1} ---")
            action_type = action.get("action")
            handler = self._action_handlers.get(action_type)

            if handler:
                step_info_str = f"Step {index + 1}, Action: {action_type}"
                action_lines = handler(action, step_info_str)
                script_lines.extend(action_lines)
                if action_type == "done":
                    break  # Stop after 'done' action
            else:
                script_lines.append(f"            # Unsupported action: {action_type}")

        # Wait for 5 seconds after the last action
        script_lines.append(f"\n            print('End of script execution')\n")
        script_lines.append(f"            await asyncio.sleep(3)")

        script_lines.extend(
            [
                "        except Exception as e:",
                "            print(f'\\n--- An error occurred: {e} ---', file=sys.stderr)",
                "            import traceback",
                "            traceback.print_exc()",
                "        finally:",
                "            print('\\n--- Script Execution Finished ---')",
                "            if browser:",
                "                await browser.close()",
                "            print('Browser closed.')",
                "",
                "if __name__ == '__main__':",
                "    asyncio.run(run_processed_script())",
            ]
        )

        return "\n".join(script_lines)
