"""
Entry point for launching the Gradio Web UI.
Can be run as a module: python -m deep_search_persist.launch_webui
"""

from deep_search_persist.simple_webui.gradio_online_mode import launch_webui as launch_webui_command

if __name__ == "__main__":
    launch_webui_command()
