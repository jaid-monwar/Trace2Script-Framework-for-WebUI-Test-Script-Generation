
import argparse
import asyncio
import hashlib
import json
import logging
import os
import random
import re
import sys
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple
import fix_o3_mini

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from browser_use.agent.views import AgentHistoryList

from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextWindowSize
from dotenv import load_dotenv

from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContext, CustomBrowserContextConfig
from src.controller.custom_controller import CustomController
from src.utils import llm_provider

load_dotenv()
logger = logging.getLogger("run_tests")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _calculate_screenshot_hash(screenshot_data: str) -> str:
    return hashlib.sha256(screenshot_data.encode()).hexdigest()


def _process_agent_history_screenshots(file_path: Path) -> None:
    if not file_path.exists():
        logger.warning(f"Agent history file not found: {file_path}")
        return
    
    logger.info(f"Processing screenshots in: {file_path}")
    
    try:
        with file_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file - {e}")
        return
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return
    
    screenshot_hash_to_number = {}
    next_sequence_number = 1
    
    processed_count = 0
    total_screenshots = 0
    
    if 'history' in data and isinstance(data['history'], list):
        for entry in data['history']:
            if isinstance(entry, dict) and 'state' in entry:
                if isinstance(entry['state'], dict) and 'screenshot' in entry['state']:
                    if entry['state']['screenshot']:
                        total_screenshots += 1
    
    logger.info(f"Found {total_screenshots} screenshots to process")
    
    if 'history' in data and isinstance(data['history'], list):
        for entry_idx, entry in enumerate(data['history']):
            if isinstance(entry, dict) and 'state' in entry:
                if isinstance(entry['state'], dict) and 'screenshot' in entry['state']:
                    screenshot_data = entry['state']['screenshot']
                    
                    if screenshot_data:
                        processed_count += 1
                        
                        screenshot_hash = _calculate_screenshot_hash(str(screenshot_data))
                        
                        if screenshot_hash in screenshot_hash_to_number:
                            sequence_number = screenshot_hash_to_number[screenshot_hash]
                        else:
                            sequence_number = next_sequence_number
                            screenshot_hash_to_number[screenshot_hash] = sequence_number
                            next_sequence_number += 1
                        
                        entry['state']['screenshot'] = sequence_number
    
    processed_path = file_path.with_name(f"{file_path.stem}_processed{file_path.suffix}")
    
    try:
        with processed_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error writing processed file: {e}")
        return
    
    try:
        file_path.unlink()
        processed_path.rename(file_path)
    except Exception as e:
        logger.error(f"Error replacing original file: {e}")
        return
    
    unique_screenshots = len(screenshot_hash_to_number)
    logger.info(f"Screenshot processing complete:")
    logger.info(f"  Total screenshots processed: {processed_count}")
    logger.info(f"  Unique screenshots found: {unique_screenshots}")
    logger.info(f"  Duplicate screenshots: {processed_count - unique_screenshots}")




def _safe_name(name: str) -> str:
    return re.sub(r"[^\w\-\.]+", "_", name.strip())


def _parse_model_spec(model_spec: str) -> Tuple[str, str]:
    if '/' not in model_spec:
        raise ValueError(f"Model spec must be in format 'provider/model_name', got: {model_spec}")
    
    parts = model_spec.split('/', 1)
    provider = parts[0].strip()
    model_name = parts[1].strip()
    
    if not provider or not model_name:
        raise ValueError(f"Both provider and model_name must be non-empty, got: {model_spec}")
    
    return provider, model_name


def _compose_task(prompt: Dict) -> str:
    
    parts = [directive_prompt, prompt.get("instruction", ""), prompt.get("description", "")]
    if "input" in prompt:
        parts.append(f"Input: {json.dumps(prompt['input'], ensure_ascii=False)}")
    if "expected" in prompt:
        parts.append(f"Expected: {json.dumps(prompt['expected'], ensure_ascii=False)}")
    return "\n".join(filter(bool, parts))


async def _run_single_test(
        prompt: Dict,
        root_out: Path,
        provider: str,
        model_name: str,
        *,
        headless: bool = False,
        max_steps: int = 30,
        window_w: int = 1280,
        window_h: int = 720,
):
    testcase_name = _safe_name(prompt.get("name", f"case_{uuid.uuid4().hex[:6]}"))
    out_dir = root_out / testcase_name
    trace_dir = out_dir / "traces"
    video_dir = out_dir / "videos"
    downloads_dir = out_dir / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.mkdir(exist_ok=True)
    video_dir.mkdir(exist_ok=True)
    downloads_dir.mkdir(exist_ok=True)

    llm = None
    try:
        llm_kwargs = {
            "provider": provider,
            "model_name": model_name,
            "temperature": 0.6,
        }
        
        if provider == "openai":
            llm_kwargs.update({
                "base_url": os.getenv("OPENAI_ENDPOINT", ""),
                "api_key": os.getenv("OPENAI_API_KEY", ""),
            })
        elif provider == "ollama":
            llm_kwargs.update({
                "base_url": os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434"),
                "num_ctx": 16000,
            })
        elif provider == "anthropic":
            llm_kwargs.update({
                "base_url": os.getenv("ANTHROPIC_ENDPOINT", ""),
                "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            })
        elif provider == "google":
            llm_kwargs.update({
                "api_key": os.getenv("GOOGLE_API_KEY", ""),
            })
        elif provider == "deepseek":
            llm_kwargs.update({
                "base_url": os.getenv("DEEPSEEK_ENDPOINT", ""),
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            })
        
        llm = llm_provider.get_llm_model(**llm_kwargs)
        
    except Exception as e:
        logger.warning("LLM initialisation failed – running agent without LLM: %s", e)

    extra_args = [f"--window-size={window_w},{window_h}"]
    browser = CustomBrowser(
        config=BrowserConfig(
            headless=headless,
            disable_security=True,
            browser_binary_path=None,
            extra_browser_args=extra_args,
        )
    )
    context: Optional[CustomBrowserContext] = None
    controller: Optional[CustomController] = None
    agent: Optional[BrowserUseAgent] = None
    history_file = out_dir / "agent_history.json"
    
    try:
        context = await browser.new_context(
            config=CustomBrowserContextConfig(
                trace_path=str(trace_dir),
                save_recording_path=str(video_dir),
                save_downloads_path=str(downloads_dir),
                browser_window_size=BrowserContextWindowSize(width=window_w, height=window_h),
                force_new_context=True,
            )
        )

        controller = CustomController()
        task_text = _compose_task(prompt)

        print(f"PROMPT FOR TEST CASE: {task_text}")

        agent = BrowserUseAgent(
            task=task_text,
            llm=llm,
            browser=browser,
            browser_context=context,
            controller=controller,
            use_vision=False,
            max_actions_per_step=10,
            max_input_tokens=128000,
        )
        agent.settings.generate_gif = str(out_dir / "recording.gif")
        agent.state.agent_id = uuid.uuid4().hex

        TIMEOUT_SECONDS = 10 * 60
        try:
            history: AgentHistoryList = await asyncio.wait_for(
                agent.run(max_steps=max_steps),
                timeout=TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "⏰  Time limit (%s s) reached for '%s' – stopping the agent.",
                TIMEOUT_SECONDS,
                testcase_name,
            )
            if agent and not agent.state.stopped:
                agent.stop()
            history = agent.state.history

        agent.save_history(str(history_file))
        logger.info("✓  Completed '%s' – success: %s", testcase_name, history.is_successful())
        
    finally:
        for _ in range(2):
            if agent and not agent.state.stopped:
                agent.stop()
            if context:
                await context.close()
                context = None
            if browser:
                await browser.close()
                browser = None
        if controller:
            await controller.close_mcp_client()
    
    if history_file.exists():
        _process_agent_history_screenshots(history_file)




async def _main(json_path: Path, headless: bool = False, model_spec: str = "openai/gpt-4o"):
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "testcases" not in data or not isinstance(data["testcases"], list):
        raise ValueError("JSON must contain a 'testcases' array.")

    try:
        provider, model_name = _parse_model_spec(model_spec)
    except ValueError as e:
        logger.error(f"Invalid model specification: {e}")
        sys.exit(1)

    safe_provider = _safe_name(provider)
    safe_model_name = _safe_name(model_name)
    model_dir_name = f"{safe_provider}_{safe_model_name}"
    json_name = json_path.stem
    root_output_dir = json_path.parent / model_dir_name / json_name
    
    logger.info("Results will be stored under '%s/'", root_output_dir)
    logger.info("Using LLM: %s/%s", provider, model_name)
    
    for idx, case in enumerate(data["testcases"], start=1):
        prompt = case.get("prompt", {})
        logger.info("┌─ Test-case %d/%d: %s", idx, len(data["testcases"]), prompt.get("name", "Unnamed"))
        await _run_single_test(prompt, root_output_dir, provider, model_name, headless=headless)
        logger.info("└─ Finished test-case %d/%d\n", idx, len(data["testcases"]))
        
        if idx < len(data["testcases"]):
            delay_minutes = random.uniform(0, 1)
            delay_seconds = delay_minutes * 60
            logger.info("⏳ Waiting %.1f minutes before next test case to avoid rate limiting...", delay_minutes)
            await asyncio.sleep(delay_seconds)
            logger.info("✅ Resuming test execution")


async def _run_all_json_files(headless: bool, model_spec: str) -> None:
    dataset_dir = ROOT_DIR / "dataset"
    json_files = sorted(dataset_dir.glob("*.json"))
    if not json_files:
        logger.error("No JSON files found in '%s' – nothing to run.", dataset_dir)
        return

    logger.info("Discovered %d dataset files under '%s'", len(json_files), dataset_dir)
    for idx, json_path in enumerate(json_files, start=1):
        logger.info("=== [%d/%d] Running dataset file: %s ===", idx, len(json_files), json_path.name)
        await _main(json_path, headless=headless, model_spec=model_spec)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Browser-Use test-cases from a JSON spec.")
    parser.add_argument(
        "json_target",
        type=str,
        help=(
            "Path to a test-case definition JSON, OR the literal string 'all' "
            "to run every *.json file inside the dataset/ folder."
        ),
    )
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode.")
    parser.add_argument(
        "--model", 
        type=str, 
        default="openai/gpt-4o", 
        help="LLM model specification in format 'provider/model_name' (e.g., 'openai/gpt-4o', 'ollama/qwen2.5:7b')"
    )
    args = parser.parse_args()

    if args.json_target.lower() == "all":
        asyncio.run(_run_all_json_files(headless=args.headless, model_spec=args.model))
    else:
        asyncio.run(
            _main(Path(args.json_target).resolve(), headless=args.headless, model_spec=args.model)
        )