import json
import asyncio
import os
from playwright.async_api import async_playwright
from automate.parser import process_file
from automate.refiner import process_action_list
from automate.utils.generator import ProcessedScriptGenerator

AGENT_HISTORY_PATH =  "test-scripts/agent_history.json"

async def main():
    try:
        print(f"Processing {AGENT_HISTORY_PATH}")
        parsed_history, action_list = process_file(AGENT_HISTORY_PATH)

        with open("test-scripts/parsed_action_list.json", "w") as f:
            json.dump(action_list, f, indent=4)
        # return

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-web-security',
                    '--disable-features=BlockInsecurePrivateNetworkRequests'
                ]
            )
            context = await browser.new_context(viewport={"width": 1280, "height": 720})
            page = await context.new_page()

            refined_agent_list = await process_action_list(page, action_list)

            # Close browser
            await asyncio.sleep(2)
            await browser.close()

        with open("test-scripts/refined_agent_list.json", "w") as f:
            json.dump(refined_agent_list, f, indent=4)
        print(f"Refined agent history saved to: test-scripts/refined_agent_list.json")

        # Generate the script
        playwright_processed_script_generator = ProcessedScriptGenerator(refined_agent_list)
        playwright_script_content = playwright_processed_script_generator.generate_script_content()

        # Save the script
        with open("test-scripts/test_script.py", "w") as f:
            f.write(playwright_script_content)
        print(f"Playwright script saved to: test-scripts/test_script.py")

    except Exception as e:
        print(f"Error processing {AGENT_HISTORY_PATH}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())