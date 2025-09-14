# Script Generation Module

A standalone Python module for converting browser agent history into executable Playwright test scripts. This module processes JSON files containing browser automation sequences and generates robust, maintainable test scripts.

## Quick Start

This module takes browser agent history files and converts them into executable Playwright scripts through a three-stage pipeline: Parse → Refine → Generate.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** (required for the project)
- **Playwright** (for browser automation)
- **uv** (recommended) or **pip** for dependency management

## Setup Instructions

### Step 1: Navigate to Script Generation Directory

```bash
cd script-generation/
```

### Step 2: Install Dependencies

#### Option A: Using uv (Recommended)
```bash
# Install dependencies with uv
uv sync

# This will install all dependencies including Playwright
```

#### Option B: Using pip
```bash
# Install dependencies from the fullstack server requirements
pip install -r ../fullstack/server/requirements.txt

# Install Playwright specifically
pip install playwright>=1.55.0

# Install Playwright browsers
playwright install
```

### Step 3: Prepare Input Files

Place your browser agent history JSON file in the `test-scripts/` directory:

```bash
# Your input file should be at:
test-scripts/agent_history.json
```

## Usage

### Quick Script Generation

The simplest way to generate a test script:

```bash
python main.py
```

This will:
1. Parse `test-scripts/agent_history.json`
2. Refine actions by validating against live web pages
3. Generate `test-scripts/test_script.py`

### Manual Pipeline Execution

For more control over the process, you can run each stage manually:

```python
import json
import asyncio
from playwright.async_api import async_playwright
from automate.parser import process_file
from automate.refiner import process_action_list
from automate.utils.generator import ProcessedScriptGenerator

async def manual_pipeline():
    # Stage 1: Parse the agent history
    print("Stage 1: Parsing agent history...")
    parsed_history, action_list = process_file("test-scripts/agent_history.json")

    # Save parsed actions (optional)
    with open("test-scripts/parsed_action_list.json", "w") as f:
        json.dump(action_list, f, indent=4)

    # Stage 2: Refine actions with live browser validation
    print("Stage 2: Refining actions...")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        refined_action_list = await process_action_list(page, action_list)
        await browser.close()

    # Save refined actions (optional)
    with open("test-scripts/refined_agent_list.json", "w") as f:
        json.dump(refined_action_list, f, indent=4)

    # Stage 3: Generate executable script
    print("Stage 3: Generating script...")
    script_generator = ProcessedScriptGenerator(refined_action_list)
    script_content = script_generator.generate_script_content()

    # Save the final script
    with open("test-scripts/test_script.py", "w") as f:
        f.write(script_content)

    print("Pipeline completed successfully!")

# Run the manual pipeline
if __name__ == "__main__":
    asyncio.run(manual_pipeline())
```

## Directory Structure

```
script-generation/
├── main.py                    # Main script for automated pipeline
├── pyproject.toml            # Python project configuration
├── uv.lock                   # Dependency lock file
├── automate/                 # Core processing modules
│   ├── __init__.py
│   ├── parser.py            # Stage 1: Parse agent history
│   ├── refiner.py           # Stage 2: Refine actions with browser
│   └── utils/               # Utility modules
│       ├── __init__.py
│       ├── browser_config.py # Browser configuration utilities
│       ├── generator.py     # Stage 3: Script generation
│       ├── selector_util.py # CSS/XPath selector handling
│       └── utils.py         # Common browser automation utilities
└── test-scripts/            # Input/output files
    ├── agent_history.json   # Input: Browser agent history
    ├── parsed_action_list.json    # Intermediate: Parsed actions
    ├── refined_agent_list.json    # Intermediate: Refined actions
    └── test_script.py       # Output: Generated Playwright script
```

## Processing Pipeline Explained

### Stage 1: Parser (automate/parser.py)

The parser extracts and processes raw browser actions from the agent history JSON file.

**Input:** `agent_history.json` - Contains browser interaction history with metadata
**Output:** `parsed_action_list.json` - Cleaned and structured action list

**What it does:**
- Extracts actions from model outputs
- Associates actions with DOM element information (XPath, CSS selectors)
- Filters duplicate and invalid actions
- Adds element attributes for better selector generation

**Example Input Structure:**
```json
{
  "history": [
    {
      "model_output": {
        "action": [
          {
            "click_element_by_index": {
              "index": 0
            }
          }
        ]
      },
      "state": {
        "interacted_element": [
          {
            "xpath": "//button[@id='submit']",
            "css_selector": "button#submit",
            "attributes": {"class": "btn-primary", "type": "submit"}
          }
        ]
      }
    }
  ]
}
```

### Stage 2: Refiner (automate/refiner.py)

The refiner validates and improves actions by testing them against live web pages.

**Input:** Parsed action list
**Output:** `refined_agent_list.json` - Validated actions with modern selectors

**What it does:**
- Launches a live browser session
- Tests each action against the actual web page
- Converts XPath selectors to modern Playwright selectors
- Handles dynamic page changes (new tabs, navigation)
- Validates element availability and visibility

**Selector Conversion Examples:**
- XPath: `//input[@placeholder='Search']` → Playwright: `placeholder="Search"`
- XPath: `//button[text()='Submit']` → Playwright: `role=button[name="Submit"]`
- XPath: `//div[@data-testid='modal']` → Playwright: `[data-testid="modal"]`

### Stage 3: Generator (automate/utils/generator.py)

The generator creates executable Playwright test scripts from refined actions.

**Input:** Refined action list
**Output:** `test_script.py` - Complete Playwright test script

**What it does:**
- Generates Python imports and helper functions
- Creates browser launch and context setup code
- Converts actions to Playwright API calls
- Adds error handling and logging
- Includes page stability checks and navigation handling

**Generated Script Features:**
- Modern Playwright selectors (role-based, test-id, etc.)
- Automatic page navigation handling
- New tab/window detection and switching
- Robust element waiting and interaction
- Comprehensive error handling and logging

## Input File Format

### Agent History JSON Structure

Your `agent_history.json` should follow this structure:

```json
{
  "history": [
    {
      "model_output": {
        "current_state": {
          "evaluation_previous_goal": "Success - Page loaded successfully",
          "memory": "I need to click the login button",
          "next_goal": "Click the login button to proceed"
        },
        "action": [
          {
            "go_to_url": {
              "url": "https://example.com"
            }
          },
          {
            "click_element_by_index": {
              "index": 0
            }
          },
          {
            "input_text": {
              "text": "user@example.com"
            }
          }
        ]
      },
      "result": [
        {
          "is_done": false,
          "extracted_content": "Navigation successful",
          "include_in_memory": true
        }
      ],
      "state": {
        "interacted_element": [
          null,
          {
            "xpath": "//button[@id='login-btn']",
            "css_selector": "#login-btn",
            "attributes": {
              "class": "btn btn-primary",
              "type": "button",
              "aria-label": "Login"
            }
          },
          {
            "xpath": "//input[@name='email']",
            "css_selector": "input[name='email']",
            "attributes": {
              "type": "email",
              "placeholder": "Enter your email",
              "name": "email"
            }
          }
        ]
      }
    }
  ]
}
```

### Supported Actions

The pipeline supports these browser actions:

#### Navigation Actions
- `go_to_url`: Navigate to a specific URL
- `go_back`: Navigate back in browser history
- `open_tab`: Open a new browser tab
- `switch_tab`: Switch between browser tabs

#### Interaction Actions
- `click_element_by_index`: Click on an element
- `input_text`: Enter text into form fields
- `select_dropdown_option`: Select options from dropdowns
- `send_keys`: Send keyboard keys (Enter, Tab, etc.)

#### Page Actions
- `scroll_down`: Scroll down the page
- `scroll_up`: Scroll up the page
- `scroll_to_text`: Scroll to element containing specific text
- `wait`: Pause execution for specified seconds

#### Completion Actions
- `done`: Mark task completion with success status

## Running Generated Scripts

Once you have generated a script, you can run it:

```bash
# Navigate to test-scripts directory
cd test-scripts/

# Run the generated script
python test_script.py
```

### Generated Script Features

The generated scripts include:

- **Modern Playwright API usage**
- **Automatic browser management** (launch, close)
- **Context and page handling**
- **Robust element selection** using multiple strategies
- **Navigation and new tab handling**
- **Comprehensive logging** of all actions
- **Error handling** with detailed messages

### Example Generated Script Structure

```python
import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext

def get_locator_from_selector(page: Page, selector: str):
    """Gets a Playwright locator based on a selector string."""
    if selector.startswith("role="):
        # Handle role-based selectors
        return page.get_by_role(role, name=name, exact=True).first
    elif selector.startswith("[data-testid="):
        # Handle test ID selectors
        return page.get_by_test_id(test_id).first
    else:
        return page.locator(selector).first

async def run_processed_script():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Generated test steps here
            print("Navigating to: https://example.com")
            await page.goto("https://example.com")

            print("Clicking element: role=button[name=\"Login\"]")
            locator = get_locator_from_selector(page, 'role=button[name="Login"]')
            await locator.click()

        except Exception as e:
            print(f'An error occurred: {e}')
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(run_processed_script())
```

## Configuration Options

### Browser Configuration

You can customize browser behavior by modifying the browser launch parameters in `main.py`:

```python
browser = await playwright.chromium.launch(
    headless=False,  # Set to True for headless mode
    args=[
        '--disable-blink-features=AutomationControlled',
        '--disable-features=IsolateOrigins,site-per-process',
        '--disable-site-isolation-trials',
        '--disable-web-security',
        '--disable-features=BlockInsecurePrivateNetworkRequests'
    ]
)

context = await browser.new_context(
    viewport={"width": 1280, "height": 720},  # Custom viewport size
    # Add other context options as needed
)
```

### Selector Strategy Priority

The selector utility (`automate/utils/selector_util.py`) uses this priority order:

1. **Test ID selectors** (`data-testid`, `data-test-id`, etc.)
2. **Role-based selectors** (`role=button[name="Submit"]`)
3. **ARIA label selectors** (`[aria-label="Close"]`)
4. **Form-specific selectors** (`placeholder="Email"`, `label="Username"`)
5. **Text content selectors** (`text="Click here"`)
6. **ID selectors** (`#unique-id`)
7. **Name attribute selectors** (`[name="email"]`)
8. **Value attribute selectors** (`[value="submit"]`)
9. **CSS class selectors** (`.stable-class`)
10. **Combined selectors** (tag + class + attributes)
11. **Parent context selectors**
12. **nth-child selectors** (last resort)

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Error: ModuleNotFoundError: No module named 'playwright'
# Solution: Install Playwright
pip install playwright>=1.55.0
playwright install
```

#### 2. Agent History File Not Found
```bash
# Error: FileNotFoundError: agent_history.json not found
# Solution: Ensure the file exists in test-scripts/
ls test-scripts/agent_history.json
```

#### 3. Browser Launch Fails
```bash
# Error: Browser launch failed
# Solution: Install browser dependencies
playwright install-deps
```

#### 4. Element Not Found During Refinement
```
# Warning: Element with xpath '...' not found
# This is normal - the refiner will skip invalid actions
# Check the refined_agent_list.json for successfully processed actions
```

#### 5. Generated Script Fails to Run
```python
# Common issues and solutions:

# Issue: Selector not found
# Solution: The element might be dynamic or changed
# Check the browser console and update selectors manually if needed

# Issue: Page navigation timeout
# Solution: Increase timeout or check network connectivity
await page.goto("https://example.com", timeout=60000)

# Issue: Element not clickable
# Solution: Add wait conditions
await page.wait_for_selector("button", state="visible")
await page.wait_for_load_state("networkidle")
```

### Debug Mode

To run with detailed logging:

```python
import logging

# Add to the beginning of main.py
logging.basicConfig(level=logging.DEBUG)
```

### Manual Selector Testing

To test selectors manually:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://example.com")

    # Test your selector
    element = page.locator("role=button[name='Submit']")
    print(f"Element count: {element.count()}")
    print(f"Element visible: {element.is_visible()}")

    browser.close()
```

### Performance Optimization

For faster processing:

1. **Use headless mode** in refinement stage:
   ```python
   browser = await playwright.chromium.launch(headless=True)
   ```

2. **Skip refinement** for trusted agent histories:
   ```python
   # Skip stage 2 and go directly to generation
   action_list = process_file("agent_history.json")[1]
   script_generator = ProcessedScriptGenerator(action_list)
   ```

3. **Reduce browser arguments** for simpler scenarios:
   ```python
   browser = await playwright.chromium.launch(headless=False)  # Minimal args
   ```

## Advanced Usage

### Custom Action Handlers

Extend the generator with custom action handlers:

```python
from automate.utils.generator import ProcessedScriptGenerator

class CustomScriptGenerator(ProcessedScriptGenerator):
    def _map_custom_action(self, action: dict, step_info_str: str) -> list[str]:
        # Implement your custom action
        return [
            f'print("Executing custom action: {step_info_str}")',
            "# Add your custom logic here"
        ]

# Use your custom generator
generator = CustomScriptGenerator(refined_actions)
script_content = generator.generate_script_content()
```

### Batch Processing

Process multiple agent histories:

```python
import os
import json
from pathlib import Path

async def batch_process(input_dir: str, output_dir: str):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    for json_file in input_path.glob("*.json"):
        print(f"Processing {json_file.name}...")

        # Process the file
        parsed_history, action_list = process_file(str(json_file))

        # Generate script
        script_generator = ProcessedScriptGenerator(action_list)
        script_content = script_generator.generate_script_content()

        # Save output
        output_file = output_path / f"{json_file.stem}_test.py"
        with open(output_file, "w") as f:
            f.write(script_content)

        print(f"Generated {output_file}")

# Usage
# asyncio.run(batch_process("input_histories/", "output_scripts/"))
```

## Contributing

When contributing to this module:

1. **Test with various agent histories** to ensure compatibility
2. **Add new selector strategies** to `selector_util.py` for better element detection
3. **Extend action handlers** in `generator.py` for new action types
4. **Improve error handling** in `refiner.py` for edge cases
5. **Update documentation** when adding new features

## Tips for Best Results

1. **Clean agent histories** produce better scripts - remove unnecessary actions
2. **Stable selectors** are preferred - avoid dynamic IDs and classes
3. **Test generated scripts** in different environments before production use
4. **Monitor for page changes** - websites evolve and selectors may need updates
5. **Use the refinement stage** - it significantly improves script reliability

Happy test automation!