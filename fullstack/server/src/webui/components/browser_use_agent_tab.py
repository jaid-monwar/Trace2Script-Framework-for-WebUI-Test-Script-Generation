import asyncio
import base64
import json
import logging
import os
import pdb
import uuid
from collections.abc import Awaitable
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional, Set, Union

import gradio as gr

from browser_use.agent.views import ToolCallingMethod
from browser_use.agent.views import (
    REQUIRED_LLM_API_ENV_VARS,
    ActionResult,
    AgentError,
    AgentHistory,
    AgentHistoryList,
    AgentOutput,
    AgentSettings,
    AgentState,
    AgentStepInfo,
    StepMetadata,
)
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import (
    BrowserContext,
    BrowserContextConfig,
    BrowserContextWindowSize,
)
from browser_use.browser.views import BrowserState, BrowserStateHistory
from gradio.components import Component
from langchain_core.language_models.chat_models import BaseChatModel

from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContext, CustomBrowserContextConfig
from src.controller.custom_controller import CustomController
from src.utils import llm_provider
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)




def _compose_task(prompt: Dict) -> str:

    parts = [
        directive_prompt,
        prompt.get("instruction", ""),
        prompt.get("description", ""),
    ]
    if "input" in prompt:
        parts.append(f"Input: {json.dumps(prompt['input'], ensure_ascii=False)}")
    if "expected" in prompt:
        parts.append(f"Expected: {json.dumps(prompt['expected'], ensure_ascii=False)}")
    return "\n".join(filter(bool, parts))


async def _initialize_llm(
    provider: Optional[str],
    model_name: Optional[str],
    temperature: float,
    base_url: Optional[str],
    api_key: Optional[str],
    num_ctx: Optional[int] = None,
) -> Optional[BaseChatModel]:
    if not provider or not model_name:
        logger.info("LLM Provider or Model Name not specified, LLM will be None.")
        return None
    try:
        logger.info(
            f"Initializing LLM: Provider={provider}, Model={model_name}, Temp={temperature}"
        )
        llm = llm_provider.get_llm_model(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            base_url=base_url or None,
            api_key=api_key or None,
            num_ctx=num_ctx if provider == "ollama" else None,
        )
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}", exc_info=True)
        gr.Warning(
            f"Failed to initialize LLM '{model_name}' for provider '{provider}'. Please check settings. Error: {e}"
        )
        return None


def _get_config_value(
    webui_manager: WebuiManager,
    comp_dict: Dict[gr.components.Component, Any],
    comp_id_suffix: str,
    default: Any = None,
) -> Any:
    tab_name = "browser_use_agent"
    comp_id = f"{tab_name}.{comp_id_suffix}"
    try:
        comp = webui_manager.get_component_by_id(comp_id)
        return comp_dict.get(comp, default)
    except KeyError:
        for prefix in ["agent_settings", "browser_settings"]:
            try:
                comp_id = f"{prefix}.{comp_id_suffix}"
                comp = webui_manager.get_component_by_id(comp_id)
                return comp_dict.get(comp, default)
            except KeyError:
                continue
        logger.warning(
            f"Component with suffix '{comp_id_suffix}' not found in manager for value lookup."
        )
        return default


def _format_agent_output(model_output: AgentOutput) -> str:
    content = ""
    if model_output:
        try:
            action_dump = [
                action.model_dump(exclude_none=True) for action in model_output.action
            ]

            state_dump = model_output.current_state.model_dump(exclude_none=True)
            model_output_dump = {
                "current_state": state_dump,
                "action": action_dump,
            }
            json_string = json.dumps(model_output_dump, indent=4, ensure_ascii=False)
            content = f"<pre><code class='language-json'>{json_string}</code></pre>"

        except AttributeError as ae:
            logger.error(
                f"AttributeError during model dump: {ae}. Check if 'action' or 'current_state' or their items support 'model_dump'."
            )
            content = f"<pre><code>Error: Could not format agent output (AttributeError: {ae}).\nRaw output: {str(model_output)}</code></pre>"
        except Exception as e:
            logger.error(f"Error formatting agent output: {e}", exc_info=True)
            content = f"<pre><code>Error formatting agent output.\nRaw output:\n{str(model_output)}</code></pre>"

    return content.strip()




async def _handle_new_step(
    webui_manager: WebuiManager, state: BrowserState, output: AgentOutput, step_num: int
):

    if not hasattr(webui_manager, "bu_chat_history"):
        logger.error(
            "Attribute 'bu_chat_history' not found in webui_manager! Cannot add chat message."
        )
        webui_manager.bu_chat_history = (
            []
        )
    step_num -= 1
    logger.info(f"Step {step_num} completed.")

    screenshot_html = ""
    screenshot_data = getattr(state, "screenshot", None)
    if screenshot_data:
        try:
            if (
                isinstance(screenshot_data, str) and len(screenshot_data) > 100
            ):
                img_tag = f'<img src="data:image/jpeg;base64,{screenshot_data}" alt="Step {step_num} Screenshot" style="max-width: 800px; max-height: 600px; object-fit:contain;" />'
                screenshot_html = (
                    img_tag + "<br/>"
                )
            else:
                logger.warning(
                    f"Screenshot for step {step_num} seems invalid (type: {type(screenshot_data)}, len: {len(screenshot_data) if isinstance(screenshot_data, str) else 'N/A'})."
                )
                screenshot_html = "**[Invalid screenshot data]**<br/>"

        except Exception as e:
            logger.error(
                f"Error processing or formatting screenshot for step {step_num}: {e}",
                exc_info=True,
            )
            screenshot_html = "**[Error displaying screenshot]**<br/>"
    else:
        logger.debug(f"No screenshot available for step {step_num}.")

    formatted_output = _format_agent_output(output)

    step_header = f"--- **Step {step_num}** ---"
    final_content = step_header + "<br/>" + screenshot_html + formatted_output

    chat_message = {
        "role": "assistant",
        "content": final_content.strip(),
    }

    webui_manager.bu_chat_history.append(chat_message)

    await asyncio.sleep(0.05)


def _handle_done(webui_manager: WebuiManager, history: AgentHistoryList):
    logger.info(
        f"Agent task finished. Duration: {history.total_duration_seconds():.2f}s, Tokens: {history.total_input_tokens()}"
    )
    final_summary = f"**Task Completed**\n"
    final_summary += f"- Duration: {history.total_duration_seconds():.2f} seconds\n"
    final_summary += f"- Total Input Tokens: {history.total_input_tokens()}\n"

    final_result = history.final_result()
    if final_result:
        final_summary += f"- Final Result: {final_result}\n"

    errors = history.errors()
    if errors and any(errors):
        final_summary += f"- **Errors:**\n```\n{errors}\n```\n"
    else:
        final_summary += "- Status: Success\n"

    webui_manager.bu_chat_history.append(
        {"role": "assistant", "content": final_summary}
    )


async def _ask_assistant_callback(
    webui_manager: WebuiManager, query: str, browser_context: BrowserContext
) -> Dict[str, Any]:
    logger.info("Agent requires assistance. Waiting for user input.")

    if not hasattr(webui_manager, "_chat_history"):
        logger.error("Chat history not found in webui_manager during ask_assistant!")
        return {"response": "Internal Error: Cannot display help request."}

    webui_manager.bu_chat_history.append(
        {
            "role": "assistant",
            "content": f"**Need Help:** {query}\nPlease provide information or perform the required action in the browser, then type your response/confirmation below and click 'Submit Response'.",
        }
    )

    webui_manager.bu_response_event = asyncio.Event()
    webui_manager.bu_user_help_response = None

    try:
        logger.info("Waiting for user response event...")
        await asyncio.wait_for(
            webui_manager.bu_response_event.wait(), timeout=3600.0
        )
        logger.info("User response event received.")
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for user assistance.")
        webui_manager.bu_chat_history.append(
            {
                "role": "assistant",
                "content": "**Timeout:** No response received. Trying to proceed.",
            }
        )
        webui_manager.bu_response_event = None
        return {"response": "Timeout: User did not respond."}

    response = webui_manager.bu_user_help_response
    webui_manager.bu_chat_history.append(
        {"role": "user", "content": response}
    )
    webui_manager.bu_response_event = (
        None
    )
    return {"response": response}




async def run_agent_task(
    webui_manager: WebuiManager, components: Dict[gr.components.Component, Any]
) -> AsyncGenerator[Dict[gr.components.Component, Any], None]:

    user_input_comp = webui_manager.get_component_by_id("browser_use_agent.user_input")
    run_button_comp = webui_manager.get_component_by_id("browser_use_agent.run_button")
    stop_button_comp = webui_manager.get_component_by_id(
        "browser_use_agent.stop_button"
    )
    pause_resume_button_comp = webui_manager.get_component_by_id(
        "browser_use_agent.pause_resume_button"
    )
    clear_button_comp = webui_manager.get_component_by_id(
        "browser_use_agent.clear_button"
    )
    chatbot_comp = webui_manager.get_component_by_id("browser_use_agent.chatbot")
    history_file_comp = webui_manager.get_component_by_id(
        "browser_use_agent.agent_history_file"
    )
    gif_comp = webui_manager.get_component_by_id("browser_use_agent.recording_gif")
    browser_view_comp = webui_manager.get_component_by_id(
        "browser_use_agent.browser_view"
    )

    def get_form_field(field_name):
        comp = webui_manager.get_component_by_id(f"browser_use_agent.{field_name}")
        return components.get(comp, "").strip()

    task_name = get_form_field("task_name")
    task_instruction = get_form_field("task_instruction")
    task_description = get_form_field("task_description")
    input_search_input = get_form_field("input_search_input")
    input_action = get_form_field("input_action")
    expected_outcome = get_form_field("expected_outcome")
    expected_status = get_form_field("expected_status")

    if not task_name or not task_instruction:
        gr.Warning("Please enter at least a task name and instruction.")
        yield {
            webui_manager.get_component_by_id(
                "browser_use_agent.run_button"
            ): gr.update(interactive=True)
        }
        return

    prompt_obj = {
        "name": task_name,
        "instruction": task_instruction,
        "description": task_description,
        "input": {"search_input": input_search_input or "N/A", "action": input_action},
        "expected": {"outcome": expected_outcome, "status": expected_status},
    }

    task = _compose_task(prompt_obj)

    webui_manager.bu_chat_history.append(
        {"role": "user", "content": f"Task: {task_name}"}
    )

    yield {
        user_input_comp: gr.Textbox(
            value="", interactive=False, placeholder="Agent is running..."
        ),
        run_button_comp: gr.Button(value="⏳ Running...", interactive=False),
        stop_button_comp: gr.Button(interactive=True),
        pause_resume_button_comp: gr.Button(value="⏸️ Pause", interactive=True),
        clear_button_comp: gr.Button(interactive=False),
        chatbot_comp: gr.update(value=webui_manager.bu_chat_history),
        history_file_comp: gr.update(value=None),
        gif_comp: gr.update(value=None),
    }

    def get_setting(key, default=None):
        comp = webui_manager.id_to_component.get(f"agent_settings.{key}")
        return components.get(comp, default) if comp else default

    override_system_prompt = None
    extend_system_prompt = None
    max_steps = 50
    max_actions = 10
    max_input_tokens = 128000
    tool_calling_method = "auto"
    mcp_server_config = None

    llm_provider_name = get_setting(
        "llm_provider", None
    )
    llm_model_name = get_setting("llm_model_name", None)
    llm_temperature = get_setting("llm_temperature", 0.6)
    use_vision = get_setting("use_vision", False)
    ollama_num_ctx = get_setting("ollama_num_ctx", 16000)
    llm_base_url = get_setting("llm_base_url") or None
    llm_api_key = get_setting("llm_api_key") or None

    def get_browser_setting(key, default=None):
        comp = webui_manager.id_to_component.get(f"browser_settings.{key}")
        return components.get(comp, default) if comp else default

    browser_binary_path = None
    browser_user_data_dir = None
    use_own_browser = False
    cdp_url = None
    wss_url = None
    save_recording_path = "./tmp/videos"
    save_trace_path = None
    save_agent_history_path = "./tmp/agent_history"
    save_download_path = None

    keep_browser_open = get_browser_setting("keep_browser_open", False)
    headless = get_browser_setting("headless", False)
    disable_security = get_browser_setting("disable_security", True)
    window_w = int(get_browser_setting("window_w", 1280))
    window_h = int(get_browser_setting("window_h", 720))

    stream_vw = 70
    stream_vh = int(70 * window_h // window_w)

    os.makedirs(save_agent_history_path, exist_ok=True)
    if save_recording_path:
        os.makedirs(save_recording_path, exist_ok=True)

    main_llm = await _initialize_llm(
        llm_provider_name,
        llm_model_name,
        llm_temperature,
        llm_base_url,
        llm_api_key,
        ollama_num_ctx if llm_provider_name == "ollama" else None,
    )

    async def ask_callback_wrapper(
        query: str, browser_context: BrowserContext
    ) -> Dict[str, Any]:
        return await _ask_assistant_callback(webui_manager, query, browser_context)

    if not webui_manager.bu_controller:
        webui_manager.bu_controller = CustomController(
            ask_assistant_callback=ask_callback_wrapper
        )

    should_close_browser_on_finish = not keep_browser_open

    try:
        if not keep_browser_open:
            if webui_manager.bu_browser_context:
                logger.info("Closing previous browser context.")
                await webui_manager.bu_browser_context.close()
                webui_manager.bu_browser_context = None
            if webui_manager.bu_browser:
                logger.info("Closing previous browser.")
                await webui_manager.bu_browser.close()
                webui_manager.bu_browser = None

        if not webui_manager.bu_browser:
            logger.info("Launching new browser instance.")
            extra_args = [f"--window-size={window_w},{window_h}"]

            webui_manager.bu_browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=disable_security,
                    browser_binary_path=None,
                    extra_browser_args=extra_args,
                    wss_url=None,
                    cdp_url=None,
                )
            )

        if not webui_manager.bu_browser_context:
            logger.info("Creating new browser context.")
            context_config = CustomBrowserContextConfig(
                trace_path=None,
                save_recording_path=save_recording_path,
                save_downloads_path=None,
                browser_window_size=BrowserContextWindowSize(
                    width=window_w, height=window_h
                ),
            )
            if not webui_manager.bu_browser:
                raise ValueError("Browser not initialized, cannot create context.")
            webui_manager.bu_browser_context = (
                await webui_manager.bu_browser.new_context(config=context_config)
            )

        if not webui_manager.bu_agent_task_id:
            webui_manager.bu_agent_task_id = str(uuid.uuid4())
        
        os.makedirs(
            os.path.join(save_agent_history_path, webui_manager.bu_agent_task_id),
            exist_ok=True,
        )
        history_file = os.path.join(
            save_agent_history_path,
            webui_manager.bu_agent_task_id,
            f"{webui_manager.bu_agent_task_id}.json",
        )
        gif_path = os.path.join(
            save_agent_history_path,
            webui_manager.bu_agent_task_id,
            f"{webui_manager.bu_agent_task_id}.gif",
        )

        async def step_callback_wrapper(
            state: BrowserState, output: AgentOutput, step_num: int
        ):
            await _handle_new_step(webui_manager, state, output, step_num)

        def done_callback_wrapper(history: AgentHistoryList):
            _handle_done(webui_manager, history)

        if not webui_manager.bu_agent:
            logger.info(f"Initializing new agent for task: {task}")
            if not webui_manager.bu_browser or not webui_manager.bu_browser_context:
                raise ValueError(
                    "Browser or Context not initialized, cannot create agent."
                )
            webui_manager.bu_agent = BrowserUseAgent(
                task=task,
                llm=main_llm,
                browser=webui_manager.bu_browser,
                browser_context=webui_manager.bu_browser_context,
                controller=webui_manager.bu_controller,
                register_new_step_callback=step_callback_wrapper,
                register_done_callback=done_callback_wrapper,
                use_vision=use_vision,
                override_system_message=override_system_prompt,
                extend_system_message=extend_system_prompt,
                max_input_tokens=max_input_tokens,
                max_actions_per_step=max_actions,
                tool_calling_method=tool_calling_method,
            )
            webui_manager.bu_agent.state.agent_id = webui_manager.bu_agent_task_id
            webui_manager.bu_agent.settings.generate_gif = gif_path
        else:
            webui_manager.bu_agent.state.agent_id = webui_manager.bu_agent_task_id
            webui_manager.bu_agent.add_new_task(task)
            webui_manager.bu_agent.settings.generate_gif = gif_path
            webui_manager.bu_agent.browser = webui_manager.bu_browser
            webui_manager.bu_agent.browser_context = webui_manager.bu_browser_context
            webui_manager.bu_agent.controller = webui_manager.bu_controller

        agent_run_coro = webui_manager.bu_agent.run(max_steps=max_steps)
        agent_task = asyncio.create_task(agent_run_coro)
        webui_manager.bu_current_task = agent_task

        last_chat_len = len(webui_manager.bu_chat_history)
        while not agent_task.done():
            is_paused = webui_manager.bu_agent.state.paused
            is_stopped = webui_manager.bu_agent.state.stopped

            if is_paused:
                yield {
                    pause_resume_button_comp: gr.update(
                        value="▶️ Resume", interactive=True
                    ),
                    stop_button_comp: gr.update(interactive=True),
                }
                while is_paused and not agent_task.done():
                    is_paused = webui_manager.bu_agent.state.paused
                    is_stopped = webui_manager.bu_agent.state.stopped
                    if is_stopped:
                        break
                    await asyncio.sleep(0.2)

                if (
                    agent_task.done() or is_stopped
                ):
                    break

                yield {
                    pause_resume_button_comp: gr.update(
                        value="⏸️ Pause", interactive=True
                    ),
                    run_button_comp: gr.update(
                        value="⏳ Running...", interactive=False
                    ),
                }

            if is_stopped:
                logger.info("Agent has stopped (internally or via stop button).")
                if not agent_task.done():
                    try:
                        await asyncio.wait_for(
                            agent_task, timeout=1.0
                        )
                    except asyncio.TimeoutError:
                        logger.warning(
                            "Agent task did not finish quickly after stop signal, cancelling."
                        )
                        agent_task.cancel()
                    except Exception:
                        pass
                break

            update_dict = {}
            if webui_manager.bu_response_event is not None:
                update_dict = {
                    user_input_comp: gr.update(
                        placeholder="Agent needs help. Enter response and submit.",
                        interactive=True,
                    ),
                    run_button_comp: gr.update(
                        value="✔️ Submit Response", interactive=True
                    ),
                    pause_resume_button_comp: gr.update(interactive=False),
                    stop_button_comp: gr.update(interactive=False),
                    chatbot_comp: gr.update(value=webui_manager.bu_chat_history),
                }
                last_chat_len = len(webui_manager.bu_chat_history)
                yield update_dict
                while (
                    webui_manager.bu_response_event is not None
                    and not agent_task.done()
                ):
                    await asyncio.sleep(0.2)
                if not agent_task.done():
                    yield {
                        user_input_comp: gr.update(
                            placeholder="Agent is running...", interactive=False
                        ),
                        run_button_comp: gr.update(
                            value="⏳ Running...", interactive=False
                        ),
                        pause_resume_button_comp: gr.update(interactive=True),
                        stop_button_comp: gr.update(interactive=True),
                    }
                else:
                    break

            if len(webui_manager.bu_chat_history) > last_chat_len:
                update_dict[chatbot_comp] = gr.update(
                    value=webui_manager.bu_chat_history
                )
                last_chat_len = len(webui_manager.bu_chat_history)

            if headless and webui_manager.bu_browser_context:
                try:
                    screenshot_b64 = (
                        await webui_manager.bu_browser_context.take_screenshot()
                    )
                    if screenshot_b64:
                        html_content = f'<img src="data:image/jpeg;base64,{screenshot_b64}" style="width:{stream_vw}vw; height:{stream_vh}vh ; border:1px solid #ccc;">'
                        update_dict[browser_view_comp] = gr.update(
                            value=html_content, visible=True
                        )
                    else:
                        html_content = f"<h1 style='width:{stream_vw}vw; height:{stream_vh}vh'>Waiting for browser session...</h1>"
                        update_dict[browser_view_comp] = gr.update(
                            value=html_content, visible=True
                        )
                except Exception as e:
                    logger.debug(f"Failed to capture screenshot: {e}")
                    update_dict[browser_view_comp] = gr.update(
                        value="<div style='...'>Error loading view...</div>",
                        visible=True,
                    )
            else:
                update_dict[browser_view_comp] = gr.update(visible=False)

            if update_dict:
                yield update_dict

            await asyncio.sleep(0.1)

        webui_manager.bu_agent.state.paused = False
        webui_manager.bu_agent.state.stopped = False
        final_update = {}
        try:
            logger.info("Agent task completing...")
            if not agent_task.done():
                await agent_task
            elif agent_task.exception():
                agent_task.result()
            logger.info("Agent task completed processing.")

            logger.info(f"Explicitly saving agent history to: {history_file}")
            webui_manager.bu_agent.save_history(history_file)

            if os.path.exists(history_file):
                final_update[history_file_comp] = gr.File(value=history_file)

            if gif_path and os.path.exists(gif_path):
                logger.info(f"GIF found at: {gif_path}")
                final_update[gif_comp] = gr.Image(value=gif_path)

        except asyncio.CancelledError:
            logger.info("Agent task was cancelled.")
            if not any(
                "Cancelled" in msg.get("content", "")
                for msg in webui_manager.bu_chat_history
                if msg.get("role") == "assistant"
            ):
                webui_manager.bu_chat_history.append(
                    {"role": "assistant", "content": "**Task Cancelled**."}
                )
            final_update[chatbot_comp] = gr.update(value=webui_manager.bu_chat_history)
        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            error_message = (
                f"**Agent Execution Error:**\n```\n{type(e).__name__}: {e}\n```"
            )
            if not any(
                error_message in msg.get("content", "")
                for msg in webui_manager.bu_chat_history
                if msg.get("role") == "assistant"
            ):
                webui_manager.bu_chat_history.append(
                    {"role": "assistant", "content": error_message}
                )
            final_update[chatbot_comp] = gr.update(value=webui_manager.bu_chat_history)
            gr.Error(f"Agent execution failed: {e}")

        finally:
            webui_manager.bu_current_task = None

            if should_close_browser_on_finish:
                if webui_manager.bu_browser_context:
                    logger.info("Closing browser context after task.")
                    await webui_manager.bu_browser_context.close()
                    webui_manager.bu_browser_context = None
                if webui_manager.bu_browser:
                    logger.info("Closing browser after task.")
                    await webui_manager.bu_browser.close()
                    webui_manager.bu_browser = None

            final_update.update(
                {
                    user_input_comp: gr.update(
                        value="",
                        interactive=True,
                        placeholder="Enter your next task...",
                    ),
                    run_button_comp: gr.update(value="▶️ Submit Task", interactive=True),
                    stop_button_comp: gr.update(value="⏹️ Stop", interactive=False),
                    pause_resume_button_comp: gr.update(
                        value="⏸️ Pause", interactive=False
                    ),
                    clear_button_comp: gr.update(interactive=True),
                    chatbot_comp: gr.update(value=webui_manager.bu_chat_history),
                }
            )
            yield final_update

    except Exception as e:
        logger.error(f"Error setting up agent task: {e}", exc_info=True)
        webui_manager.bu_current_task = None
        yield {
            user_input_comp: gr.update(
                interactive=True, placeholder="Error during setup. Enter task..."
            ),
            run_button_comp: gr.update(value="▶️ Submit Task", interactive=True),
            stop_button_comp: gr.update(value="⏹️ Stop", interactive=False),
            pause_resume_button_comp: gr.update(value="⏸️ Pause", interactive=False),
            clear_button_comp: gr.update(interactive=True),
            chatbot_comp: gr.update(
                value=webui_manager.bu_chat_history
                + [{"role": "assistant", "content": f"**Setup Error:** {e}"}]
            ),
        }




async def handle_submit(
    webui_manager: WebuiManager, components: Dict[gr.components.Component, Any]
):
    user_input_comp = webui_manager.get_component_by_id("browser_use_agent.user_input")
    user_input_value = components.get(user_input_comp, "").strip()

    if webui_manager.bu_response_event and not webui_manager.bu_response_event.is_set():
        logger.info(f"User submitted assistance: {user_input_value}")
        webui_manager.bu_user_help_response = (
            user_input_value if user_input_value else "User provided no text response."
        )
        webui_manager.bu_response_event.set()
        yield {
            user_input_comp: gr.update(
                value="",
                interactive=False,
                placeholder="Waiting for agent to continue...",
            ),
            webui_manager.get_component_by_id(
                "browser_use_agent.run_button"
            ): gr.update(value="⏳ Running...", interactive=False),
        }
    elif webui_manager.bu_current_task and not webui_manager.bu_current_task.done():
        logger.warning(
            "Submit button clicked while agent is already running and not asking for help."
        )
        gr.Info("Agent is currently running. Please wait or use Stop/Pause.")
        yield {}
    else:
        logger.info("Submit button clicked for new task.")
        async for update in run_agent_task(webui_manager, components):
            yield update


async def handle_stop(webui_manager: WebuiManager):
    logger.info("Stop button clicked.")
    agent = webui_manager.bu_agent
    task = webui_manager.bu_current_task

    if agent and task and not task.done():
        agent.state.stopped = True
        agent.state.paused = False
        return {
            webui_manager.get_component_by_id(
                "browser_use_agent.stop_button"
            ): gr.update(interactive=False, value="⏹️ Stopping..."),
            webui_manager.get_component_by_id(
                "browser_use_agent.pause_resume_button"
            ): gr.update(interactive=False),
            webui_manager.get_component_by_id(
                "browser_use_agent.run_button"
            ): gr.update(interactive=False),
        }
    else:
        logger.warning("Stop clicked but agent is not running or task is already done.")
        return {
            webui_manager.get_component_by_id(
                "browser_use_agent.run_button"
            ): gr.update(interactive=True),
            webui_manager.get_component_by_id(
                "browser_use_agent.stop_button"
            ): gr.update(interactive=False),
            webui_manager.get_component_by_id(
                "browser_use_agent.pause_resume_button"
            ): gr.update(interactive=False),
            webui_manager.get_component_by_id(
                "browser_use_agent.clear_button"
            ): gr.update(interactive=True),
        }


async def handle_pause_resume(webui_manager: WebuiManager):
    agent = webui_manager.bu_agent
    task = webui_manager.bu_current_task

    if agent and task and not task.done():
        if agent.state.paused:
            logger.info("Resume button clicked.")
            agent.resume()
            return {
                webui_manager.get_component_by_id(
                    "browser_use_agent.pause_resume_button"
                ): gr.update(value="⏸️ Pause", interactive=True)
            }
        else:
            logger.info("Pause button clicked.")
            agent.pause()
            return {
                webui_manager.get_component_by_id(
                    "browser_use_agent.pause_resume_button"
                ): gr.update(value="▶️ Resume", interactive=True)
            }
    else:
        logger.warning(
            "Pause/Resume clicked but agent is not running or doesn't support state."
        )
        return {}


async def handle_clear(webui_manager: WebuiManager):
    logger.info("Clear button clicked.")

    task = webui_manager.bu_current_task
    if task and not task.done():
        logger.info("Clearing requires stopping the current task.")
        webui_manager.bu_agent.stop()
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        except Exception as e:
            logger.warning(f"Error stopping task on clear: {e}")
    webui_manager.bu_current_task = None

    if webui_manager.bu_controller:
        await webui_manager.bu_controller.close_mcp_client()
        webui_manager.bu_controller = None
    webui_manager.bu_agent = None

    webui_manager.bu_chat_history = []
    webui_manager.bu_response_event = None
    webui_manager.bu_user_help_response = None
    webui_manager.bu_agent_task_id = None

    logger.info("Agent state and browser resources cleared.")

    return {
        webui_manager.get_component_by_id("browser_use_agent.chatbot"): gr.update(
            value=[]
        ),
        webui_manager.get_component_by_id("browser_use_agent.task_name"): gr.update(
            value=""
        ),
        webui_manager.get_component_by_id(
            "browser_use_agent.task_instruction"
        ): gr.update(value=""),
        webui_manager.get_component_by_id(
            "browser_use_agent.task_description"
        ): gr.update(value=""),
        webui_manager.get_component_by_id(
            "browser_use_agent.input_search_input"
        ): gr.update(value=""),
        webui_manager.get_component_by_id("browser_use_agent.input_action"): gr.update(
            value=""
        ),
        webui_manager.get_component_by_id(
            "browser_use_agent.expected_outcome"
        ): gr.update(value=""),
        webui_manager.get_component_by_id(
            "browser_use_agent.expected_status"
        ): gr.update(value=""),
        webui_manager.get_component_by_id(
            "browser_use_agent.agent_history_file"
        ): gr.update(value=None),
        webui_manager.get_component_by_id("browser_use_agent.recording_gif"): gr.update(
            value=None
        ),
        webui_manager.get_component_by_id(
            "browser_use_agent.script_download_file"
        ): gr.update(
            value=None, visible=False
        ),
        webui_manager.get_component_by_id("browser_use_agent.browser_view"): gr.update(
            value="<div style='...'>Browser Cleared</div>"
        ),
        webui_manager.get_component_by_id("browser_use_agent.run_button"): gr.update(
            value="▶️ Submit Task", interactive=True
        ),
        webui_manager.get_component_by_id("browser_use_agent.stop_button"): gr.update(
            interactive=False
        ),
        webui_manager.get_component_by_id(
            "browser_use_agent.pause_resume_button"
        ): gr.update(value="⏸️ Pause", interactive=False),
        webui_manager.get_component_by_id("browser_use_agent.clear_button"): gr.update(
            interactive=True
        ),
        webui_manager.get_component_by_id(
            "browser_use_agent.create_script_button"
        ): gr.update(
            value="📝 Create Script", interactive=True
        ),
    }


async def handle_create_script(
    webui_manager: WebuiManager,
) -> AsyncGenerator[Dict[gr.components.Component, Any], None]:
    logger.info("Create Script button clicked.")

    create_script_button_comp = webui_manager.get_component_by_id(
        "browser_use_agent.create_script_button"
    )
    script_download_file_comp = webui_manager.get_component_by_id(
        "browser_use_agent.script_download_file"
    )

    yield {
        create_script_button_comp: gr.update(
            value="⏳ Processing...", interactive=False
        )
    }

    await asyncio.sleep(5.0)

    script_path = "socnv/script.py"
    try:
        if os.path.exists(script_path):
            yield {
                create_script_button_comp: gr.update(
                    value="📝 Create Script", interactive=True
                ),
                script_download_file_comp: gr.update(
                    value=script_path, label="Download Script", visible=True
                ),
            }
            logger.info(f"Script file loaded successfully: {script_path}")
        else:
            yield {
                create_script_button_comp: gr.update(
                    value="📝 Create Script", interactive=True
                ),
                script_download_file_comp: gr.update(
                    value=None, label="Script file not found", visible=True
                ),
            }
            logger.error(f"Script file not found: {script_path}")
            gr.Warning(f"Script file not found at {script_path}")
    except Exception as e:
        yield {
            create_script_button_comp: gr.update(
                value="📝 Create Script", interactive=True
            ),
            script_download_file_comp: gr.update(
                value=None, label="Error loading script", visible=True
            ),
        }
        logger.error(f"Error loading script file: {e}")
        gr.Error(f"Error loading script file: {e}")




def create_browser_use_agent_tab(webui_manager: WebuiManager):
    webui_manager.init_browser_use_agent()

    tab_components = {}
    with gr.Column():
        chatbot = gr.Chatbot(
            lambda: webui_manager.bu_chat_history,
            elem_id="browser_use_chatbot",
            label="Agent Interaction",
            type="messages",
            height=600,
            show_copy_button=True,
        )

        user_input = gr.Textbox(
            label="User Input",
            placeholder="Enter your next task...",
            lines=1,
            interactive=True,
            visible=True,
        )

        gr.Markdown("### Test Case Configuration")
        with gr.Group():
            task_name = gr.Textbox(
                label="Task Name",
                placeholder="Navigate to Tech Roles section",
                lines=1,
                interactive=True,
            )
            task_instruction = gr.Textbox(
                label="Instruction",
                placeholder="go to https://www.hackerrank.com/blog/ and perform the following test case",
                lines=2,
                interactive=True,
            )
            task_description = gr.Textbox(
                label="Description",
                placeholder="User navigates to the 'Tech Roles' section from the main blog page.",
                lines=2,
                interactive=True,
            )

        with gr.Group():
            gr.Markdown("#### Input Parameters")
            with gr.Row():
                input_search_input = gr.Textbox(
                    label="Search Input",
                    placeholder="N/A",
                    lines=1,
                    interactive=True,
                )
                input_action = gr.Textbox(
                    label="Action",
                    placeholder="Click on the `Tech Roles` link in the navigation bar",
                    lines=2,
                    interactive=True,
                )

        with gr.Group():
            gr.Markdown("#### Expected Results")
            with gr.Row():
                expected_outcome = gr.Textbox(
                    label="Expected Outcome",
                    placeholder="The user is taken to the 'Tech Roles' section of the blog.",
                    lines=2,
                    interactive=True,
                )
                expected_status = gr.Textbox(
                    label="Expected Status",
                    placeholder="Successful",
                    lines=1,
                    interactive=True,
                )

        with gr.Row():
            stop_button = gr.Button(
                "⏹️ Stop", interactive=False, variant="stop", scale=2
            )
            pause_resume_button = gr.Button(
                "⏸️ Pause", interactive=False, variant="secondary", scale=2, visible=True
            )
            clear_button = gr.Button(
                "🗑️ Clear", interactive=True, variant="secondary", scale=2
            )
            create_script_button = gr.Button(
                "📝 Create Script", interactive=True, variant="secondary", scale=2
            )
            run_button = gr.Button("▶️ Submit Task", variant="primary", scale=3)

        browser_view = gr.HTML(
            value="<div style='width:100%; height:50vh; display:flex; justify-content:center; align-items:center; border:1px solid #ccc; background-color:#f0f0f0;'><p>Browser View (Requires Headless=True)</p></div>",
            label="Browser Live View",
            elem_id="browser_view",
            visible=False,
        )

        with gr.Column():
            gr.Markdown("### Task Outputs")
            agent_history_file = gr.File(label="Agent History JSON", interactive=False)
            recording_gif = gr.Image(
                label="Task Recording GIF",
                format="gif",
                interactive=False,
                type="filepath",
            )
            script_download_file = gr.File(
                label="Download Script", interactive=False, visible=False
            )

    tab_components.update(
        dict(
            chatbot=chatbot,
            user_input=user_input,
            task_name=task_name,
            task_instruction=task_instruction,
            task_description=task_description,
            input_search_input=input_search_input,
            input_action=input_action,
            expected_outcome=expected_outcome,
            expected_status=expected_status,
            clear_button=clear_button,
            run_button=run_button,
            stop_button=stop_button,
            pause_resume_button=pause_resume_button,
            create_script_button=create_script_button,
            agent_history_file=agent_history_file,
            recording_gif=recording_gif,
            browser_view=browser_view,
            script_download_file=script_download_file,
        )
    )
    webui_manager.add_components("browser_use_agent", tab_components)

    all_managed_components = set(webui_manager.get_components())
    run_tab_outputs = list(tab_components.values())

    async def submit_wrapper(
        components_dict: Dict[Component, Any],
    ) -> AsyncGenerator[Dict[Component, Any], None]:
        async for update in handle_submit(webui_manager, components_dict):
            yield update

    async def stop_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        update_dict = await handle_stop(webui_manager)
        yield update_dict

    async def pause_resume_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        update_dict = await handle_pause_resume(webui_manager)
        yield update_dict

    async def clear_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        update_dict = await handle_clear(webui_manager)
        yield update_dict

    async def create_script_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        async for update in handle_create_script(webui_manager):
            yield update

    run_button.click(
        fn=submit_wrapper, inputs=all_managed_components, outputs=run_tab_outputs
    )
    stop_button.click(fn=stop_wrapper, inputs=None, outputs=run_tab_outputs)
    pause_resume_button.click(
        fn=pause_resume_wrapper, inputs=None, outputs=run_tab_outputs
    )
    clear_button.click(fn=clear_wrapper, inputs=None, outputs=run_tab_outputs)
    create_script_button.click(
        fn=create_script_wrapper, inputs=None, outputs=run_tab_outputs
    )
