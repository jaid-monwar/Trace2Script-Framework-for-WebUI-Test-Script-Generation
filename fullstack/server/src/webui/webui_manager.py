import asyncio
import json
import os
import uuid
from collections.abc import Generator
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

import gradio as gr
from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from gradio.components import Component

from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContext
from src.controller.custom_controller import CustomController


class WebuiManager:
    def __init__(self, settings_save_dir: str = "./tmp/webui_settings"):
        self.id_to_component: dict[str, Component] = {}
        self.component_to_id: dict[Component, str] = {}

        self.settings_save_dir = settings_save_dir
        os.makedirs(self.settings_save_dir, exist_ok=True)

    def init_browser_use_agent(self) -> None:
        self.bu_agent: Optional[Agent] = None
        self.bu_browser: Optional[CustomBrowser] = None
        self.bu_browser_context: Optional[CustomBrowserContext] = None
        self.bu_controller: Optional[CustomController] = None
        self.bu_chat_history: List[Dict[str, Optional[str]]] = []
        self.bu_response_event: Optional[asyncio.Event] = None
        self.bu_user_help_response: Optional[str] = None
        self.bu_current_task: Optional[asyncio.Task] = None
        self.bu_agent_task_id: Optional[str] = None


    def add_components(self, tab_name: str, components_dict: dict[str, "Component"]) -> None:
        for comp_name, component in components_dict.items():
            comp_id = f"{tab_name}.{comp_name}"
            self.id_to_component[comp_id] = component
            self.component_to_id[component] = comp_id

    def get_components(self) -> list["Component"]:
        return list(self.id_to_component.values())

    def get_component_by_id(self, comp_id: str) -> "Component":
        return self.id_to_component[comp_id]

    def get_id_by_component(self, comp: "Component") -> str:
        return self.component_to_id[comp]

    def save_config(self, components: Dict["Component", str]) -> None:
        cur_settings = {}
        for comp in components:
            if not isinstance(comp, gr.Button) and not isinstance(comp, gr.File) and str(
                    getattr(comp, "interactive", True)).lower() != "false":
                comp_id = self.get_id_by_component(comp)
                cur_settings[comp_id] = components[comp]

        config_name = datetime.now().strftime("%Y%m%d-%H%M%S")
        with open(os.path.join(self.settings_save_dir, f"{config_name}.json"), "w") as fw:
            json.dump(cur_settings, fw, indent=4)

        return os.path.join(self.settings_save_dir, f"{config_name}.json")

    def load_config(self, config_path: str):
        with open(config_path, "r") as fr:
            ui_settings = json.load(fr)

        update_components = {}
        for comp_id, comp_val in ui_settings.items():
            if comp_id in self.id_to_component:
                comp = self.id_to_component[comp_id]
                update_components[comp] = comp.__class__(value=comp_val)

        config_status = self.id_to_component["load_save_config.config_status"]
        update_components.update(
            {
                config_status: config_status.__class__(value=f"Successfully loaded config: {config_path}")
            }
        )
        yield update_components