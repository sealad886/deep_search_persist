"""
Entry point for launching the Gradio Web UI.
Can be run as a module: python -m deep_search_persist.launch_webui
"""

from deep_search_persist.simple_webui.gradio_online_mode import launch_webui as actual_gradio_launch_webui

if __name__ == "__main__":
    actual_gradio_launch_webui()
