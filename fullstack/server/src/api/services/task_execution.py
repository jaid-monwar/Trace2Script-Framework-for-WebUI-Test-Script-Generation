import asyncio
import logging
import os
import uuid
from typing import Dict, Any, Optional

from sqlmodel import Session, select

from src.api.db.session import get_session, engine
from src.api.models.task import Task
from src.api.services.result_processing import process_task_result_safe
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContext, CustomBrowserContextConfig
from src.controller.custom_controller import CustomController
from src.utils import llm_provider
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextWindowSize
from browser_use.agent.views import AgentHistoryList

from src.webui.webui_manager import WebuiManager
from src.webui.components.browser_use_agent_tab import run_agent_task
import gradio as gr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

running_tasks = {}


class MockComponent:
    def __init__(self, value=None):
        self.value = value
        self.elem_id = None
        self.elem_classes = []
        self.visible = True
        self.interactive = True
        self.label = None
    
    def update(self, **kwargs):
        return kwargs
    
    def __str__(self):
        return f"MockComponent(value={self.value})"


def create_mock_webui_manager_and_components(task_data: Dict[str, Any]) -> tuple[WebuiManager, Dict[gr.components.Component, Any]]:
    webui_manager = WebuiManager()
    webui_manager.init_browser_use_agent()
    
    mock_components = {}
    
    task_name_comp = MockComponent()
    task_instruction_comp = MockComponent()
    task_description_comp = MockComponent()
    input_search_input_comp = MockComponent()
    input_action_comp = MockComponent()
    expected_outcome_comp = MockComponent()
    expected_status_comp = MockComponent()
    
    user_input_comp = MockComponent()
    run_button_comp = MockComponent()
    stop_button_comp = MockComponent()
    pause_resume_button_comp = MockComponent()
    clear_button_comp = MockComponent()
    chatbot_comp = MockComponent()
    history_file_comp = MockComponent()
    gif_comp = MockComponent()
    browser_view_comp = MockComponent()
    
    llm_provider_comp = MockComponent()
    llm_model_comp = MockComponent()
    llm_temperature_comp = MockComponent()
    llm_base_url_comp = MockComponent()
    llm_api_key_comp = MockComponent()
    use_vision_comp = MockComponent()
    ollama_num_ctx_comp = MockComponent()
    
    headless_comp = MockComponent()
    disable_security_comp = MockComponent()
    window_w_comp = MockComponent()
    window_h_comp = MockComponent()
    keep_browser_open_comp = MockComponent()
    
    webui_manager.id_to_component.update({
        "browser_use_agent.task_name": task_name_comp,
        "browser_use_agent.task_instruction": task_instruction_comp,
        "browser_use_agent.task_description": task_description_comp,
        "browser_use_agent.input_search_input": input_search_input_comp,
        "browser_use_agent.input_action": input_action_comp,
        "browser_use_agent.expected_outcome": expected_outcome_comp,
        "browser_use_agent.expected_status": expected_status_comp,
        
        "browser_use_agent.user_input": user_input_comp,
        "browser_use_agent.run_button": run_button_comp,
        "browser_use_agent.stop_button": stop_button_comp,
        "browser_use_agent.pause_resume_button": pause_resume_button_comp,
        "browser_use_agent.clear_button": clear_button_comp,
        "browser_use_agent.chatbot": chatbot_comp,
        "browser_use_agent.agent_history_file": history_file_comp,
        "browser_use_agent.recording_gif": gif_comp,
        "browser_use_agent.browser_view": browser_view_comp,
        
        "agent_settings.llm_provider": llm_provider_comp,
        "agent_settings.llm_model_name": llm_model_comp,
        "agent_settings.llm_temperature": llm_temperature_comp,
        "agent_settings.llm_base_url": llm_base_url_comp,
        "agent_settings.llm_api_key": llm_api_key_comp,
        "agent_settings.use_vision": use_vision_comp,
        "agent_settings.ollama_num_ctx": ollama_num_ctx_comp,
        
        "browser_settings.headless": headless_comp,
        "browser_settings.disable_security": disable_security_comp,
        "browser_settings.window_w": window_w_comp,
        "browser_settings.window_h": window_h_comp,
        "browser_settings.keep_browser_open": keep_browser_open_comp,
    })
    
    for comp_id, component in webui_manager.id_to_component.items():
        webui_manager.component_to_id[component] = comp_id
    
    components_dict = {
        task_name_comp: task_data.get("task_name", ""),
        task_instruction_comp: task_data.get("instruction", ""),
        task_description_comp: task_data.get("description", ""),
        input_search_input_comp: task_data.get("search_input_input", ""),
        input_action_comp: task_data.get("search_input_action", ""),
        expected_outcome_comp: task_data.get("expected_outcome", ""),
        expected_status_comp: task_data.get("expected_status", ""),
        
        user_input_comp: "",
        run_button_comp: None,
        stop_button_comp: None,
        pause_resume_button_comp: None,
        clear_button_comp: None,
        chatbot_comp: [],
        history_file_comp: None,
        gif_comp: None,
        browser_view_comp: "",
        
        llm_provider_comp: task_data.get("llm_provider", "openai"),
        llm_model_comp: task_data.get("llm_model", "gpt-4o"),
        llm_temperature_comp: task_data.get("temperature", 0.6),
        llm_base_url_comp: task_data.get("base_url"),
        llm_api_key_comp: task_data.get("api_key"),
        use_vision_comp: False,
        ollama_num_ctx_comp: task_data.get("context_length", 16000),
        
        headless_comp: task_data.get("browser_headless_mode", True),
        disable_security_comp: task_data.get("disable_security", True),
        window_w_comp: task_data.get("window_width", 1280),
        window_h_comp: task_data.get("window_height", 720),
        keep_browser_open_comp: False,
    }
    
    return webui_manager, components_dict


async def execute_task_with_webui_wrapper(task_id: int):
    try:
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            task_data = {
                "task_name": task.task_name,
                "instruction": task.instruction,
                "description": task.description,
                "search_input_input": task.search_input_input,
                "search_input_action": task.search_input_action,
                "expected_outcome": task.expected_outcome,
                "expected_status": task.expected_status,
                "llm_provider": task.llm_provider,
                "llm_model": task.llm_model,
                "temperature": task.temperature,
                "base_url": task.base_url,
                "api_key": task.api_key,
                "context_length": task.context_length,
                "browser_headless_mode": task.browser_headless_mode,
                "disable_security": task.disable_security,
                "window_width": task.window_width,
                "window_height": task.window_height,
            }
            
            task.status = "running"
            session.add(task)
            session.commit()
        
        logger.info(f"Starting task execution using webui wrapper for task {task_id}")
        
        webui_manager, components_dict = create_mock_webui_manager_and_components(task_data)
        
        webui_manager.bu_agent_task_id = f"task_{task_id}"
        
        expected_history_path = os.path.join(
            "./tmp/agent_history",
            f"task_{task_id}",
            f"task_{task_id}.json"
        )
        expected_gif_path = os.path.join(
            "./tmp/agent_history", 
            f"task_{task_id}",
            f"task_{task_id}.gif"
        )
        
        task_completed_successfully = False
        task_failed = False
        
        try:
            last_update = None
            async for update in run_agent_task(webui_manager, components_dict):
                last_update = update
                logger.debug(f"Task {task_id} - Received update from run_agent_task")
            
            task_completed_successfully = os.path.exists(expected_history_path)
            logger.info(f"Task {task_id} execution completed via webui wrapper - Success: {task_completed_successfully}")
            logger.info(f"Expected history path: {expected_history_path}")
            logger.info(f"Expected GIF path: {expected_gif_path}")
            
        except Exception as webui_error:
            logger.error(f"Error in webui run_agent_task for task {task_id}: {webui_error}", exc_info=True)
            task_failed = True
        
        final_status = "completed" if task_completed_successfully else "failed"
        
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if task:
                task.status = final_status
                session.add(task)
                session.commit()
                logger.info(f"Task {task_id} marked as {final_status}")
        
        if task_completed_successfully:
            try:
                logger.info(f"Starting result processing for completed task {task_id}")
                logger.info(f"Using history file: {expected_history_path}")
                logger.info(f"Using GIF file: {expected_gif_path}")
                
                history_exists = os.path.exists(expected_history_path)
                gif_exists = os.path.exists(expected_gif_path)
                
                logger.info(f"History file exists: {history_exists}")
                logger.info(f"GIF file exists: {gif_exists}")
                
                if history_exists:
                    process_task_result_safe(task_id, expected_gif_path if gif_exists else None)
                    logger.info(f"Result processing completed for task {task_id}")
                else:
                    logger.warning(f"Agent history file not found for task {task_id}: {expected_history_path}")
                    
            except Exception as e:
                logger.error(f"Error in result processing for task {task_id}: {str(e)}")
        else:
            logger.info(f"Skipping result processing for task {task_id} - task did not complete successfully")
        
    except Exception as e:
        logger.error(f"Error executing task {task_id} with webui wrapper: {e}", exc_info=True)
        
        try:
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if task:
                    task.status = "failed"
                    session.add(task)
                    session.commit()
                    logger.info(f"Task {task_id} marked as failed due to error")
        except Exception as db_error:
            logger.error(f"Failed to update task {task_id} status to failed: {db_error}")


async def start_task_execution_with_webui_wrapper(task_id: int):
    asyncio.create_task(execute_task_with_webui_wrapper(task_id))


def _compose_task(task_id: int) -> str:
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            logger.error(f"Task {task_id} not found when composing task")
            return ""
        

        parts = [
            directive_prompt,
            task.instruction or "",
            task.description or "",
        ]
        
        if task.search_input_input:
            input_obj = {
                "search_input": task.search_input_input,
                "action": task.search_input_action or "N/A"
            }
            parts.append(f"Input: {input_obj}")
        
        if task.expected_outcome:
            expected_obj = {
                "outcome": task.expected_outcome,
                "status": task.expected_status or "success"
            }
            parts.append(f"Expected: {expected_obj}")
        
        return "\n".join(filter(bool, parts))


async def _initialize_llm(task_id: int, api_key: str) -> Any:
    try:
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                logger.error(f"Task {task_id} not found when initializing LLM")
                return None
            
            provider = task.llm_provider or "openai"
            model_name = task.llm_model or "gpt-4o"
            temperature = task.temperature if task.temperature is not None else 0.6
            base_url = task.base_url
            context_length = task.context_length or 16000
        
        if not provider or not model_name:
            logger.warning(f"LLM Provider or Model Name not specified for task {task_id}")
            return None
        
        logger.info(f"Initializing LLM for task {task_id}: Provider={provider}, Model={model_name}")
        
        try:
            llm = llm_provider.get_llm_model(
                provider=provider,
                model_name=model_name,
                temperature=temperature,
                base_url=base_url,
                api_key=api_key,
                num_ctx=context_length if provider == "ollama" else None,
            )
            return llm
        except Exception as e:
            logger.error(f"Error creating LLM model: {e}", exc_info=True)
            return None
    except Exception as e:
        logger.error(f"Failed to initialize LLM for task {task_id}: {e}", exc_info=True)
        return None


async def _handle_new_step(state, output, step_num: int, task_id: int):
    logger.info(f"Task {task_id} - Step {step_num} completed.")


def _handle_done(history: AgentHistoryList, task_id: int):
    logger.info(f"Task {task_id} finished. Duration: {history.total_duration_seconds():.2f}s")
    
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task:
            final_result = history.final_result()
            errors = history.errors()
            
            if errors and any(errors):
                task.status = "failed"
                logger.error(f"Task {task_id} failed with errors: {errors}")
            else:
                task.status = "completed"
                logger.info(f"Task {task_id} completed successfully")
            
            session.add(task)
            session.commit()
        else:
            logger.error(f"Task {task_id} not found in database when updating status")


async def execute_task(task_id: int, api_key: str = None):
    try:
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            browser_headless_mode = task.browser_headless_mode
            disable_security = task.disable_security
            window_width = task.window_width
            window_height = task.window_height
        
        llm = await _initialize_llm(task_id, api_key=api_key)
        if not llm:
            logger.error(f"Failed to initialize LLM for task {task_id}")
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if task:
                    task.status = "failed"
                    session.add(task)
                    session.commit()
            return
        
        task_prompt = _compose_task(task_id)
        if not task_prompt:
            logger.error(f"Failed to compose task prompt for task {task_id}")
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if task:
                    task.status = "failed"
                    session.add(task)
                    session.commit()
            return
        
        controller = CustomController()
        
        try:
            browser_config = BrowserConfig(
                headless=browser_headless_mode,
                disable_security=disable_security,
                browser_binary_path=None,
                extra_browser_args=[f"--window-size={window_width},{window_height}"],
                wss_url=None,
                cdp_url=None,
            )
            
            browser = CustomBrowser(config=browser_config)
            
            save_recording_path = "./tmp/videos"
            os.makedirs(save_recording_path, exist_ok=True)
            
            context_config = CustomBrowserContextConfig(
                trace_path=None,
                save_recording_path=save_recording_path,
                save_downloads_path=None,
                browser_window_size=BrowserContextWindowSize(
                    width=window_width, 
                    height=window_height
                ),
            )
            
            browser_context = await browser.new_context(config=context_config)
        except Exception as e:
            logger.error(f"Failed to initialize browser for task {task_id}: {e}", exc_info=True)
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if task:
                    task.status = "failed"
                    session.add(task)
                    session.commit()
            return
        
        run_id = f"task_{task_id}"
        
        save_agent_history_path = "./tmp/agent_history"
        os.makedirs(save_agent_history_path, exist_ok=True)
        os.makedirs(os.path.join(save_agent_history_path, run_id), exist_ok=True)
        
        history_file = os.path.join(
            save_agent_history_path,
            run_id,
            f"task_{task_id}.json",
        )
        gif_path = os.path.join(
            save_agent_history_path,
            run_id,
            f"task_{task_id}.gif",
        )
        
        async def step_callback_wrapper(state, output, step_num: int):
            await _handle_new_step(state, output, step_num, task_id)
        
        def done_callback_wrapper(history: AgentHistoryList):
            _handle_done(history, task_id)
        
        agent = BrowserUseAgent(
            task=task_prompt,
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            controller=controller,
            register_new_step_callback=step_callback_wrapper,
            register_done_callback=done_callback_wrapper,
            use_vision=False,
            override_system_message=None,
            extend_system_message=None,
            max_input_tokens=128000,
            max_actions_per_step=10,
            tool_calling_method="auto",
        )
        
        agent.state.agent_id = run_id
        agent.settings.generate_gif = gif_path
        
        running_tasks[task_id] = {
            "agent": agent,
            "browser": browser,
            "browser_context": browser_context,
            "controller": controller,
        }
        
        try:
            await agent.run(max_steps=50)
        except Exception as e:
            logger.error(f"Error running agent for task {task_id}: {e}", exc_info=True)
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if task:
                    task.status = "failed"
                    session.add(task)
                    session.commit()
        
        try:
            logger.info(f"Saving agent history to: {history_file}")
            agent.save_history(history_file)
            
            if os.path.exists(history_file):
                logger.info(f"Agent history saved successfully: {history_file}")
            else:
                logger.warning(f"Agent history file not found after saving: {history_file}")
                
            if gif_path and os.path.exists(gif_path):
                logger.info(f"GIF generated successfully: {gif_path}")
            else:
                logger.info(f"GIF not generated or not found: {gif_path}")
                
        except Exception as e:
            logger.error(f"Error saving agent history for task {task_id}: {e}", exc_info=True)
        
        try:
            with Session(engine) as session:
                task = session.get(Task, task_id)
                if task and task.status == "completed":
                    logger.info(f"Starting result processing for completed task {task_id}")
                    process_task_result_safe(task_id, gif_path)
                    logger.info(f"Result processing completed for task {task_id}")
                else:
                    logger.info(f"Skipping result processing for task {task_id} - task status: {task.status if task else 'not found'}")
        except Exception as e:
            logger.error(f"Error in result processing for task {task_id}: {str(e)}")
            logger.error("Task completion status remains unaffected by result processing errors")
        
        try:
            await browser_context.close()
            await browser.close()
            await controller.close_mcp_client()
        except Exception as e:
            logger.error(f"Error cleaning up resources for task {task_id}: {e}", exc_info=True)
        
        if task_id in running_tasks:
            del running_tasks[task_id]
            
    except Exception as e:
        logger.error(f"Unhandled error executing task {task_id}: {e}", exc_info=True)
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if task:
                task.status = "failed"
                session.add(task)
                session.commit()


async def start_task_execution(task_id: int, api_key: str = None):
    asyncio.create_task(execute_task(task_id, api_key=api_key))


async def example_usage_webui_wrapper():
    task_id = 1
    logger.info(f"Example: Starting task {task_id} with webui wrapper")
    
    try:
        await execute_task_with_webui_wrapper(task_id)
        logger.info(f"Example: Task {task_id} completed successfully")
    except Exception as e:
        logger.error(f"Example: Task {task_id} failed: {e}")

