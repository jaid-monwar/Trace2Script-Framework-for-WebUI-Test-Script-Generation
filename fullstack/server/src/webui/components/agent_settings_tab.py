import gradio as gr
from gradio.components import Component

from src.utils import config
from src.webui.webui_manager import WebuiManager


def update_model_dropdown(llm_provider):
    if llm_provider in config.model_names:
        return gr.Dropdown(
            choices=config.model_names[llm_provider],
            value=config.model_names[llm_provider][0],
            interactive=True,
        )
    else:
        return gr.Dropdown(
            choices=[], value="", interactive=True, allow_custom_value=True
        )


def create_agent_settings_tab(webui_manager: WebuiManager):
    tab_components = {}

    with gr.Group():
        with gr.Row():
            llm_provider = gr.Dropdown(
                choices=[provider for provider, model in config.model_names.items()],
                label="LLM Provider",
                value="openai",
                info="Select LLM provider for LLM",
                interactive=True,
            )
            llm_model_name = gr.Dropdown(
                label="LLM Model Name",
                choices=config.model_names["openai"],
                value="gpt-4o",
                interactive=True,
                allow_custom_value=True,
                info="Select a model in the dropdown options or directly type a custom model name",
            )
        with gr.Row():
            llm_temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=0.6,
                step=0.1,
                label="LLM Temperature",
                info="Controls randomness in model outputs",
                interactive=True,
            )

            use_vision = gr.Checkbox(
                label="Use Vision",
                value=False,
                info="Enable Vision(Input highlighted screenshot into LLM)",
                interactive=True,
            )

            ollama_num_ctx = gr.Slider(
                minimum=2**8,
                maximum=2**16,
                value=16000,
                step=1,
                label="Ollama Context Length",
                info="Controls max context length model needs to handle (less = faster)",
                visible=False,
                interactive=True,
            )

        with gr.Row():
            llm_base_url = gr.Textbox(
                label="Base URL", value="", info="API endpoint URL (if required)"
            )
            llm_api_key = gr.Textbox(
                label="API Key",
                type="password",
                value="",
                info="Your API key (leave blank to use .env)",
            )

    tab_components.update(
        dict(
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            llm_temperature=llm_temperature,
            use_vision=use_vision,
            ollama_num_ctx=ollama_num_ctx,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
        )
    )
    webui_manager.add_components("agent_settings", tab_components)

    llm_provider.change(
        fn=lambda x: gr.update(visible=x == "ollama"),
        inputs=llm_provider,
        outputs=ollama_num_ctx,
    )
    llm_provider.change(
        lambda provider: update_model_dropdown(provider),
        inputs=[llm_provider],
        outputs=[llm_model_name],
    )
