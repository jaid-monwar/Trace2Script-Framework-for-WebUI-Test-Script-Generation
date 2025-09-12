import logging

import gradio as gr
from gradio.components import Component

from src.utils import config
from src.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


async def close_browser(webui_manager: WebuiManager):
    if webui_manager.bu_current_task and not webui_manager.bu_current_task.done():
        webui_manager.bu_current_task.cancel()
        webui_manager.bu_current_task = None

    if webui_manager.bu_browser_context:
        logger.info("⚠️ Closing browser context when changing browser config.")
        await webui_manager.bu_browser_context.close()
        webui_manager.bu_browser_context = None

    if webui_manager.bu_browser:
        logger.info("⚠️ Closing browser when changing browser config.")
        await webui_manager.bu_browser.close()
        webui_manager.bu_browser = None


def create_browser_settings_tab(webui_manager: WebuiManager):
    tab_components = {}

    with gr.Group():
        with gr.Row():
            keep_browser_open = gr.Checkbox(
                label="Keep Browser Open",
                value=True,
                info="Keep Browser Open between Tasks",
                interactive=True,
            )
            headless = gr.Checkbox(
                label="Headless Mode",
                value=False,
                info="Run browser without GUI",
                interactive=True,
            )
            disable_security = gr.Checkbox(
                label="Disable Security",
                value=True,
                info="Disable browser security",
                interactive=True,
            )

    with gr.Group():
        with gr.Row():
            window_w = gr.Number(
                label="Window Width",
                value=1280,
                info="Browser window width",
                interactive=True,
            )
            window_h = gr.Number(
                label="Window Height",
                value=720,
                info="Browser window height",
                interactive=True,
            )

    tab_components.update(
        dict(
            keep_browser_open=keep_browser_open,
            headless=headless,
            disable_security=disable_security,
            window_h=window_h,
            window_w=window_w,
        )
    )
    webui_manager.add_components("browser_settings", tab_components)

    async def close_wrapper():
        await close_browser(webui_manager)

    headless.change(close_wrapper)
    keep_browser_open.change(close_wrapper)
    disable_security.change(close_wrapper)
