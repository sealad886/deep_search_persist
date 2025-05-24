import json
import os
import socket
import subprocess
import platform
from datetime import datetime  # Added for formatting timestamps if needed

import gradio as gr
import requests
import tomllib  # For Python 3.11+
from loguru import logger

from ..deep_search_persist.persistence import SessionSummary, SessionSummaryList  # Adjusted for clarity

RESEARCH_TOML_PATH = os.environ.get("DEEP_SEARCH_RESEARCH_TOML_PATH", "/app/deep_search_persist/research.toml")
DEFAULT_GRADIO_CONTAINER_PORT = 7860
DEFAULT_GRADIO_HOST_PORT = 7861


# --- Helper Function to Extract Session ID ---
def _extract_session_id(dropdown_value):
    """Extracts the session_id from the dropdown's formatted string."""
    if not dropdown_value or " - " not in dropdown_value:
        return None
    return dropdown_value.split(" - ")[0]


def fetch_sessions(base_url):
    """Fetches the list of sessions from the API."""
    sessions_endpoint = f"{base_url}/sessions"
    logger.info(f"Requesting sessions from: {sessions_endpoint}")
    session_list_formatted = []
    status_message = ""
    try:
        response = requests.get(sessions_endpoint, timeout=10)
        response.raise_for_status()
        sessions_data = response.json()

        for session in sessions_data:
            session_id = session.get("session_id", "N/A")
            user_query = session.get("user_query", "N/A")
            status = session.get("status", "N/A")
            start_time_str = session.get("start_time", "N/A")

            # Time formatting
            try:
                start_time_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                formatted_time = start_time_dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_time = start_time_str

            # Truncate long queries for display
            display_query = (user_query[:50] + "...") if len(user_query or "") > 50 else user_query

            session_list_formatted.append(f"{session_id} - {display_query} ({status}) [{formatted_time}]")

        if sessions_data and not session_list_formatted:  # Should not happen if sessions_data is not empty
            status_message = "Formatted 0 sessions, but received data. " "Check formatting logic."
        elif session_list_formatted:
            status_message = f"Fetched {len(session_list_formatted)} sessions."
        else:
            status_message = "No sessions found or an issue occurred before formatting."

    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException fetching sessions: {e}")
        status_message = f"Error fetching sessions: {e}"
    except json.JSONDecodeError:
        logger.error("JSONDecodeError fetching sessions.")
        status_message = "Error decoding session data from API."
    except Exception as e:
        logger.error(f"Unexpected error fetching sessions: {e}")
        status_message = f"An unexpected error occurred: {e}"

    # Return update for dropdown and status message
    return {"choices": session_list_formatted}, status_message


def fetch_session_details(dropdown_value, base_url):
    """Fetches the full details of a selected session."""
    session_id = _extract_session_id(dropdown_value)
    if not session_id:
        return None, "Please select a session from the list first."

    details_endpoint = f"{base_url}/sessions/{session_id}"
    session_details = None
    status_message = ""
    try:
        response = requests.get(details_endpoint, timeout=10)
        response.raise_for_status()
        session_details = response.json()
        status_message = f"Details loaded for session: {session_id}"
    except requests.exceptions.RequestException as e:
        status_message = f"Error fetching details for session {session_id}: {e}"
    except json.JSONDecodeError:
        status_message = f"Error decoding session details for {session_id}."
    except Exception as e:
        status_message = f"An unexpected error occurred: {e}"

    return session_details, status_message


def delete_session_api(dropdown_value, base_url):
    """Deletes the selected session via the API."""
    session_id = _extract_session_id(dropdown_value)
    if not session_id:
        return (
            "Please select a session to delete.",
            None,
        )  # Return status and None for details

    delete_endpoint = f"{base_url}/sessions/{session_id}"
    status_message = ""
    try:
        response = requests.delete(delete_endpoint, timeout=10)
        response.raise_for_status()
        if response.status_code == 200 or response.status_code == 204:  # Handle 204 No Content
            status_message = f"Session {session_id} deleted successfully."
        else:
            # Attempt to get error message from response if available
            try:
                error_detail = response.json().get("detail", "Unknown reason")
                status_message = (
                    f"Failed to delete session " f"{session_id}: {error_detail} " f"(Status: {response.status_code})"
                )
            except json.JSONDecodeError:
                status_message = f"Failed to delete session {session_id}. " f"Status: {response.status_code}"

    except requests.exceptions.RequestException as e:
        status_message = f"Error deleting session {session_id}: {e}"
    except Exception as e:
        status_message = f"An unexpected error occurred during deletion: {e}"

    # Return status message and clear the details view
    return status_message, None


# --- Original Research Function (Unchanged) ---
def research(system_message, query, max_iterations, base_url):
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": query})

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-xxx",  # Placeholder, consider making this configurable
    }

    data = {
        "model": "deep_researcher",
        "messages": messages,
        "max_iterations": max_iterations,
        "stream": True,
    }

    agent_thinking = []
    final_report = ""
    in_thinking = False
    current_think = ""

    try:
        # Use the persistent endpoint
        research_endpoint = f"{base_url}/chat/completions"
        response = requests.post(
            research_endpoint,
            headers=headers,
            json=data,
            stream=True,
            timeout=300,  # Increased timeout for potentially long research
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue

            if line.startswith(b"data: "):
                try:
                    line_str = line[6:].decode("utf-8")
                    chunk = json.loads(line_str)
                    if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                        content = chunk["choices"][0]["delta"]["content"]
                        if "<think>" in content:
                            in_thinking = True
                            # Handle case where <think> might be split or have content before it
                            parts = content.split("<think>", 1)
                            if parts[0]:  # Content before <think>
                                final_report += parts[0]
                            current_think += parts[1]  # Start accumulating thinking content
                        elif "</think>" in content:
                            in_thinking = False
                            # Handle case where </think> might be split or have content after it
                            parts = content.split("</think>", 1)
                            current_think += parts[0]  # Accumulate content before </think>
                            agent_thinking.append(current_think.strip())
                            current_think = ""
                            if parts[1]:  # Content after </think>
                                final_report += parts[1]
                            yield "\n".join(agent_thinking), final_report
                        elif in_thinking:
                            current_think += content
                            yield "\n".join(agent_thinking + [current_think]), final_report
                        else:
                            final_report += content
                            yield "\n".join(agent_thinking), final_report
                except json.JSONDecodeError:
                    # Ignore lines that are not valid JSON after "data: "
                    continue
                except Exception as e_inner:  # Catch other potential errors during chunk processing
                    print(f"Error processing chunk: {e_inner}, Line: {line}")  # Debugging
                    continue  # Skip problematic chunk

    except requests.exceptions.Timeout:
        yield "\n".join(agent_thinking), "Error: Request timed out after 300 seconds."
    except requests.exceptions.RequestException as e:
        yield "\n".join(agent_thinking), f"Error connecting to API: {str(e)}"
    except Exception as e:
        # Catch any other unexpected errors during the request or initial processing
        yield "\n".join(agent_thinking), f"An unexpected error occurred: {str(e)}"


def _get_webui_ports_from_config():
    """Reads Gradio port configurations from research.toml."""
    container_port = DEFAULT_GRADIO_CONTAINER_PORT
    host_port_suggestion = DEFAULT_GRADIO_HOST_PORT

    try:
        with open(RESEARCH_TOML_PATH, "rb") as f:
            config = tomllib.load(f)
        webui_config = config.get("WebUI", {})
        container_port = webui_config.get("gradio_container_port", DEFAULT_GRADIO_CONTAINER_PORT)
        host_port_suggestion = webui_config.get("gradio_host_port", DEFAULT_GRADIO_HOST_PORT)
        logger.info(
            f"Loaded WebUI config from {RESEARCH_TOML_PATH}: "
            f"container_port={container_port}, "
            f"host_port_suggestion={host_port_suggestion}"
        )
    except FileNotFoundError:
        logger.warning(
            f"{RESEARCH_TOML_PATH} not found. Using default WebUI ports: "
            f"container={container_port}, "
            f"suggested_host={host_port_suggestion}"
        )
    except (tomllib.TOMLDecodeError, Exception) as e:
        logger.error(f"Error reading or parsing {RESEARCH_TOML_PATH}: {e}. " f"Using default WebUI ports.")

    return container_port, host_port_suggestion


def get_docker_container_status():
    """Check the status of Docker containers via their health endpoints."""
    # Define containers with their health check endpoints
    containers = {
        "mongo": {"host": "mongo", "port": 27017, "path": "/", "method": "tcp"},
        "app-persist": {"host": "app-persist", "port": 8000, "path": "/health", "method": "http"},
        "searxng-persist": {"host": "searxng-persist", "port": 8080, "path": "/", "method": "http"},
        "redis-persist": {"host": "redis-persist", "port": 6379, "path": "/", "method": "tcp"},
        "nginx": {"host": "nginx", "port": 80, "path": "/health", "method": "http"}
    }
    
    status_info = {}
    
    for container_name, config in containers.items():
        try:
            if config["method"] == "http":
                # HTTP health check
                url = f"http://{config['host']}:{config['port']}{config['path']}"
                response = requests.get(url, timeout=3)
                if response.status_code < 400:
                    status_info[container_name] = {
                        "status": "running", 
                        "details": f"HTTP {response.status_code} - Responding on {config['host']}:{config['port']}"
                    }
                else:
                    status_info[container_name] = {
                        "status": "error", 
                        "details": f"HTTP {response.status_code} - Service error"
                    }
            elif config["method"] == "tcp":
                # TCP connection check for non-HTTP services
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((config['host'], config['port']))
                sock.close()
                
                if result == 0:
                    status_info[container_name] = {
                        "status": "running", 
                        "details": f"TCP connection successful to {config['host']}:{config['port']}"
                    }
                else:
                    status_info[container_name] = {
                        "status": "stopped", 
                        "details": f"TCP connection failed to {config['host']}:{config['port']}"
                    }
                    
        except requests.exceptions.ConnectionError:
            status_info[container_name] = {
                "status": "stopped", 
                "details": f"Connection refused to {config['host']}:{config['port']}"
            }
        except Exception as e:
            status_info[container_name] = {
                "status": "error", 
                "details": f"Error checking {config['host']}:{config['port']}: {str(e)}"
            }
    
    return status_info


def check_ollama_status():
    """Check if Ollama server is accessible."""
    # Get Ollama configuration - use host.docker.internal for Docker environment
    ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal")
    ollama_port = os.getenv("OLLAMA_PORT", "11434")
    
    # Construct clean URL
    if ollama_host.startswith("http://"):
        ollama_url = f"{ollama_host}:{ollama_port}"
    else:
        ollama_url = f"http://{ollama_host}:{ollama_port}"
    
    # Clean up any double port issues
    import re
    ollama_url = re.sub(r':(\d+):\1', r':\1', ollama_url)
    
    try:
        # Try to connect to Ollama health endpoint
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "status": "running",
                "url": ollama_url,
                "models_count": len(models),
                "details": f"Connected successfully. {len(models)} models available."
            }
        else:
            return {
                "status": "error",
                "url": ollama_url,
                "details": f"HTTP {response.status_code}: {response.text[:100]}"
            }
    except requests.exceptions.ConnectionError:
        return {
            "status": "stopped",
            "url": ollama_url if 'ollama_url' in locals() else "Unknown",
            "details": "Connection refused. Ollama server may not be running."
        }
    except Exception as e:
        return {
            "status": "error",
            "url": ollama_url if 'ollama_url' in locals() else "Unknown",
            "details": f"Error: {str(e)}"
        }


def get_terminal_launch_command():
    """Get the terminal launch command from config."""
    try:
        with open(RESEARCH_TOML_PATH, "rb") as f:
            config = tomllib.load(f)
        webui_config = config.get("WebUI", {})
        return webui_config.get("terminal_launch_command", "/bin/zsh -i -c zf")
    except Exception as e:
        logger.error(f"Error reading terminal launch command from config: {e}")
        return "/bin/zsh -i -c zf"  # Default fallback


def launch_terminal():
    """Launch the system terminal with the configured command."""
    try:
        terminal_command = get_terminal_launch_command()
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # Use osascript to open Terminal.app and run the command
            applescript = f'''
            tell application "Terminal"
                activate
                do script "{terminal_command}"
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript], check=True)
            return "Terminal launched successfully on macOS"
        elif system == "Linux":
            # Try common Linux terminal emulators
            terminals = ["gnome-terminal", "konsole", "xterm", "x-terminal-emulator"]
            for terminal in terminals:
                try:
                    subprocess.run([terminal, "-e", terminal_command], check=True)
                    return f"Terminal launched successfully using {terminal}"
                except FileNotFoundError:
                    continue
            return "No supported terminal emulator found on Linux"
        elif system == "Windows":
            # Windows Terminal or Command Prompt
            try:
                subprocess.run(["wt", "new-tab", "powershell", "-Command", terminal_command], check=True)
                return "Windows Terminal launched successfully"
            except FileNotFoundError:
                subprocess.run(["cmd", "/c", "start", "cmd", "/k", terminal_command], check=True)
                return "Command Prompt launched successfully"
        else:
            return f"Unsupported operating system: {system}"
            
    except Exception as e:
        logger.error(f"Error launching terminal: {e}")
        return f"Error launching terminal: {str(e)}"


def refresh_status():
    """Refresh both Docker and Ollama status."""
    docker_status = get_docker_container_status()
    ollama_status = check_ollama_status()
    
    # Format Docker status for display
    docker_display = []
    for container, info in docker_status.items():
        status_emoji = "✅" if info["status"] == "running" else "❌" if info["status"] == "stopped" else "⚠️"
        docker_display.append(f"{status_emoji} **{container}**: {info['status']} - {info['details']}")
    
    # Format Ollama status for display
    ollama_emoji = "✅" if ollama_status["status"] == "running" else "❌" if ollama_status["status"] == "stopped" else "⚠️"
    ollama_display = f"{ollama_emoji} **Ollama Server** ({ollama_status['url']}): {ollama_status['status']} - {ollama_status['details']}"
    
    return "\n".join(docker_display), ollama_display, ollama_status["status"] != "running"


# --- Gradio UI Creation ---
def create_ui():
    with gr.Blocks(theme="soft") as demo:  # Use Soft theme as in other version
        gr.Markdown(
            "# OpenDeepResearcher Interface",
            latex_delimiters=[{"left": "$$", "right": "$$", "display": True}],
        )

        # Determine API base URL - prefer environment variable if set (useful for Docker)
        default_api_base_url = os.environ.get("DEEP_SEARCH_API_BASE_URL", "http://app-persist:8000/persist")
        # Check if running in Docker and the URL doesn't seem to be a service name
        if (
            "app-persist" not in default_api_base_url
            and os.environ.get("DOCKER_CONTAINER")
            and not default_api_base_url.startswith("http://localhost")
        ):
            logger.warning(
                f"DEEP_SEARCH_API_BASE_URL ('{default_api_base_url}') "
                "does not seem to point to 'app-persist' service name. "
                "If running in Docker Compose, ensure it's "
                "'http://app-persist:8000/persist' or similar for "
                "inter-container communication."
            )

        base_url = gr.Textbox(
            label="API Base URL",
            value=default_api_base_url,
            placeholder=("Enter API base URL (e.g., http://app-persist:8000/persist " "or http://localhost:8000/persist)"),
        )

        with gr.Tabs():
            # --- Research Tab ---
            with gr.TabItem("Research"):
                with gr.Row():
                    # Left column for settings (1/4 width)
                    with gr.Column(scale=1):
                        system_msg = gr.Textbox(
                            label="System Message (Optional)",
                            placeholder="Enter system message here...",
                            lines=3,
                        )
                        query = gr.Textbox(
                            label="Research Query",
                            placeholder="What would you like to research?",
                            lines=5,  # Increased lines for query
                        )
                        max_iter = gr.Slider(
                            minimum=1,
                            maximum=50,
                            value=30,
                            step=1,
                            label="Max Iterations",
                        )
                        start_research_btn = gr.Button("Start Research", variant="primary")

                    # Right column for outputs (3/4 width)
                    with gr.Column(scale=3):
                        thinking_output = gr.Textbox(
                            label="Agent Thinking",
                            lines=20,  # Adjusted lines
                            max_lines=40,
                            show_copy_button=True,
                            interactive=False,  # Read-only
                        )
                        final_output = gr.Textbox(
                            label="Final Report",
                            lines=20,  # Adjusted lines
                            max_lines=40,
                            show_copy_button=True,
                            interactive=False,  # Read-only
                        )

                start_research_btn.click(
                    fn=research,
                    inputs=[system_msg, query, max_iter, base_url],
                    outputs=[thinking_output, final_output],
                    api_name="research",
                )

            # --- Session Management Tab ---
            with gr.TabItem("Session Management"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Manage Saved Sessions")
                        refresh_sessions_btn = gr.Button("Refresh Session List")
                        session_dropdown = gr.Dropdown(
                            label="Select Session",
                            choices=[],  # Initially empty, populated by refresh
                            interactive=True,
                        )
                        view_details_btn = gr.Button("View Details")
                        delete_session_btn = gr.Button("Delete Selected Session", variant="stop")
                        session_status_text = gr.Textbox(label="Status", interactive=False)

                    with gr.Column(scale=2):
                        gr.Markdown("### Session Details")
                        session_details_json = gr.JSON(label="Full Session Data")

                # --- Session Management Event Handlers ---
                refresh_sessions_btn.click(
                    fn=fetch_sessions,
                    inputs=[base_url],
                    outputs=[session_dropdown, session_status_text],
                )

                view_details_btn.click(
                    fn=fetch_session_details,
                    inputs=[session_dropdown, base_url],
                    outputs=[session_details_json, session_status_text],
                )

                # Delete button workflow: delete -> update status -> refresh list
                delete_session_btn.click(
                    fn=delete_session_api,
                    inputs=[session_dropdown, base_url],
                    outputs=[
                        session_status_text,
                        session_details_json,
                    ],  # Update status, clear details
                ).then(
                    fn=fetch_sessions,  # Refresh the dropdown after deletion attempt
                    inputs=[base_url],
                    outputs=[
                        session_dropdown,
                        session_status_text,
                    ],  # Update dropdown, overwrite status
                )

                # Load sessions when the tab is selected or initially?
                # Let's rely on the refresh button for now to avoid startup load.
                # demo.load( # Example if we wanted initial load
                #     fn=fetch_sessions,
                #     inputs=[base_url],
                #     outputs=[session_dropdown, session_status_text]
                # )

            # --- System Status Tab ---
            with gr.TabItem("System Status"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### System Health Monitor")
                        
                        with gr.Row():
                            refresh_status_btn = gr.Button("Refresh Status", variant="primary")
                            auto_refresh_checkbox = gr.Checkbox(
                                label="Auto-refresh (30s)", 
                                value=False,
                                scale=0
                            )
                        
                        refresh_interval = gr.Number(
                            label="Refresh Interval (seconds)",
                            value=30,
                            minimum=5,
                            maximum=300,
                            step=5,
                            visible=False
                        )
                        
                        # Terminal launch section (only show when Ollama is not running)
                        with gr.Group() as terminal_group:
                            gr.Markdown("### Ollama Server Management")
                            terminal_launch_btn = gr.Button(
                                "🚀 Launch Terminal to Start Ollama", 
                                variant="secondary",
                                visible=False
                            )
                            terminal_status_text = gr.Textbox(
                                label="Terminal Launch Status", 
                                interactive=False,
                                visible=False
                            )
                        
                    with gr.Column(scale=2):
                        gr.Markdown("### Docker Containers Status")
                        docker_status_display = gr.Markdown(
                            "Click 'Refresh Status' to check Docker containers...",
                            label="Docker Status"
                        )
                        
                        gr.Markdown("### Ollama Server Status")
                        ollama_status_display = gr.Markdown(
                            "Click 'Refresh Status' to check Ollama server...",
                            label="Ollama Status"
                        )

                # --- System Status Event Handlers ---
                def handle_refresh_status():
                    docker_display, ollama_display, show_terminal = refresh_status()
                    return (
                        docker_display,
                        ollama_display,
                        gr.update(visible=show_terminal),  # Show terminal button if Ollama not running
                        gr.update(visible=show_terminal),  # Show terminal status if Ollama not running
                        ""  # Clear terminal status
                    )

                def handle_terminal_launch():
                    result = launch_terminal()
                    return result

                def toggle_auto_refresh(enabled):
                    return gr.update(visible=enabled)

                # Manual refresh button
                refresh_status_btn.click(
                    fn=handle_refresh_status,
                    outputs=[
                        docker_status_display,
                        ollama_status_display,
                        terminal_launch_btn,
                        terminal_status_text,
                        terminal_status_text
                    ]
                )

                # Auto-refresh checkbox toggle
                auto_refresh_checkbox.change(
                    fn=toggle_auto_refresh,
                    inputs=[auto_refresh_checkbox],
                    outputs=[refresh_interval]
                )

                # Create a simple auto-refresh system using periodic events
                # This will refresh every 30 seconds if auto-refresh is enabled
                
                def conditional_auto_refresh():
                    """Only refresh if auto-refresh checkbox is enabled"""
                    # Note: In a real implementation, you'd need to track the checkbox state
                    # For now, we'll implement a simpler version that can be toggled
                    try:
                        # TODO: This is a placeholder - in practice you'd check the checkbox state
                        return handle_refresh_status()
                    except:
                        return gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

                # Initial load of status
                demo.load(
                    fn=handle_refresh_status,
                    outputs=[
                        docker_status_display,
                        ollama_status_display,
                        terminal_launch_btn,
                        terminal_status_text,
                        terminal_status_text
                    ]
                )

                terminal_launch_btn.click(
                    fn=handle_terminal_launch,
                    outputs=[terminal_status_text]
                )

    return demo


def launch_webui():
    container_port, host_port_suggestion = _get_webui_ports_from_config()

    demo = create_ui()
    demo.queue(default_concurrency_limit=1)

    logger.info(f"Gradio UI will listen on 0.0.0.0:{container_port} inside the container.")
    logger.success(
        f"To use the included web UI, open http://localhost:{host_port_suggestion}."
    )
    logger.info(
        f"Ensure your Docker Compose service 'gradio-ui' maps this host port "
        f"(or your preferred host port via GRADIO_HOST_PORT env var) "
        f"to container port {container_port}."
    )
    logger.info(f"Example .env entry for Docker Compose: GRADIO_HOST_PORT={host_port_suggestion}")
    logger.info(
        "Example docker-compose.persist.yml port mapping for gradio-ui service: "
        f'ports: - "${{GRADIO_HOST_PORT:-{DEFAULT_GRADIO_HOST_PORT}}}:'
        f'{container_port}"'
    )

    # The `inbrowser=True` will attempt to open a browser inside the container;
    # it usually won't be visible on your host but is harmless.
    demo.launch(server_name="0.0.0.0", server_port=container_port, 
                inbrowser=False, pwa=True, favicon_path="/app/simple-webui/imgs/app_logo.jpg")


__all__ = [
    "launch_webui",
]
