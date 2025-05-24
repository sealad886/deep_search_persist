# DeepSearch with Persisting History

Automated research using Searxng, featuring session persistence and a Gradio Web UI.

This project provides an automated research agent that leverages Searxng for web searches. Key updates include a refactored core as the `deep-search-persist` Python module, robust session persistence for interrupting and resuming research tasks, and an interactive Gradio-based Web UI for ease of use and session management.

## Key Features

* Automated research capabilities.
* Modular structure based on the `deep-search-persist` Python module.
* Configurable research parameters via [`research.toml`](research.toml:1).
* **MongoDB-backed session persistence** for saving, resuming, and rolling back research sessions (interrupt/resume/rollback). Sessions are stored incrementally in MongoDB, allowing you to:
  * List all sessions
  * Retrieve or resume any session (even after interruption)
  * Roll back a session to a previous iteration
  * Access full session history via API endpoints
* Interactive Web UI (Gradio-based) for ease of use and session management.
* OpenAI-compatible API for programmatic access.
* Support for different operational modes (Online, Hybrid, Local).

## Modes of Operation

The application supports different operational modes, primarily configured via the [`research.toml`](research.toml:1) file at the project root.

* **Online Mode:** Relies heavily on external services like online LLM providers (e.g., via OpenRouter) and Jina for content parsing.
* **Hybrid Mode:** Combines external services with local resources, such as using local LLMs via Ollama while still using online search and parsing.
* **Local Mode:** Aims to use primarily local resources, potentially including local LLMs and local tools for content parsing (e.g., Playwright).

Configure your preferred mode by adjusting settings like `use_jina`, `use_ollama`, and model names in [`research.toml`](research.toml:1).

## Setup and Installation

### Prerequisites

* Python (>=3.10,<3.13)
* Docker and Docker Compose (optional, for Docker-based deployment).
* MongoDB (no manual setup required if using Docker Compose)
* **Ollama (required for Hybrid/Local modes using local LLMs)** - **Must run locally, not in Docker**

### MongoDB Session Persistence

Session data is now persisted in MongoDB. If you use Docker Compose, MongoDB will be started automatically and no manual setup is needed.

* The MongoDB connection URI is set via the `MONGO_URI` environment variable (see `.env` and `docker/docker-compose.persist.yml`).
* All session data (including incremental saves, full history, and rollback points) is stored in MongoDB.
* You can list, resume, and rollback sessions via the API or Web UI.

### Configuration (`research.toml`)

Primary configuration is done via [`research.toml`](research.toml:1) at the project root. This file allows you to customize various aspects of the research process, API endpoints, and model settings.

Key settings include:

* `[Settings]`: `use_jina`, `use_ollama`, `with_planning`, `default_model`, `reason_model`.
* `[API]`: `openai_url`, `openai_compat_api_key`, `jina_api_key`, `searxng_url`.
* `[LocalAI]`: `ollama_base_url`, model context settings.

Refer to the comments within the [`research.toml`](research.toml:1) file for detailed explanations of each option.

### Dependency Installation

For installing dependencies, you can use the following methods:

* **Minimal Installation (Core Application):**

    ```bash
    pip install .
    ```

* **With Optional Dependencies:**
    You can install specific optional dependencies using extras. For example:

    ```bash
    pip install .[web]
    ```

    Available extras include:
  * `dev`: Testing and development tools (pytest, black, mypy, etc.)
  * `web`: Web UI dependencies (Gradio, requests)
  * `all`: All optional dependencies (includes both `dev` and `web`)

    To install with all optional dependencies:

    ```bash
    pip install .[all]
    ```

    The project uses a modular requirements system with files in the `requirements/` directory:
    * Each dependency group has its own file (e.g., `requirements-dev.txt`, `requirements-web.txt`)
    * The build engine automatically discovers these files and creates corresponding install options
    * The `all` option is dynamically generated from all other requirement files
    * This makes it easy to add new dependency groups without modifying setup code

* **Web UI:**
    If you need the Web UI, navigate to the `simple-webui` directory and install its requirements:

    ```bash
    cd simple-webui
    pip install -r requirements.txt
    cd ..
    ```

## Running the Application

### 1. Direct Python Execution (Recommended for development/custom use)

Ensure dependencies are installed and [`research.toml`](research.toml:1) is configured.

Run the API server:

```bash
python -m deep-search-persist
```

The API will typically be available at `http://localhost:8000/v1`.

### 2. Using Docker (Recommended for stable deployment)

Docker provides a containerized environment with all dependencies pre-configured.

#### Prerequisites for Docker

* Docker: Ensure Docker is installed and running on your system.
* Docker Compose: Install Docker Compose, which is used to define and run multi-container Docker applications.
* NVIDIA or AMD drivers: If you plan to use GPU acceleration for local models, ensure you have the appropriate drivers installed on your host machine.

#### Key Features of Docker Setup

* **Containerized API Endpoint:** Runs the `python -m deep-search-persist` core module as a Docker service, exposing the research API.
* **Containerized SearXNG Instance:** Includes an optional SearXNG service for local search capabilities.
* **Containerized Gradio Web UI:** Provides a user-friendly web interface for interacting with the researcher.
* **Local Ollama Integration:** Connects to Ollama running on the host machine (not in Docker).
* **MongoDB-backed Persistent Research Sessions:** All session data is persisted in MongoDB, allowing research tasks to be interrupted, resumed, or rolled back.
* **External Configuration:** The primary configuration is managed via a mounted `research.toml` file from the project root.

#### Configuration for Docker

The `research.toml` file located at the project root is the primary configuration source for the `deep-search-persist` application running within Docker. This file is mounted into the `deep-search-persist` container, and all application settings are read from this file.

Key sections in `research.toml` relevant to Docker users include:

* API keys (e.g., `openai_compat_api_key`, `jina_api_key`)
* Model configurations (`default_model`, `reason_model`, etc.)
* Service URLs:
  * `searxng_url`: If using the included SearXNG service, set this to `"http://searxng:8080"`.
  * `ollama_base_url`: If using Ollama running on your host machine, set this to `"http://host.docker.internal:11434"` (for Docker Desktop) or the appropriate IP address if using a different Docker setup.
* Operation mode settings (`use_jina`, `use_ollama`, `use_embed_browser`).

#### Setup Steps for Docker

1. Clone the Repository (if not already done):

   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Configure `research.toml`:
   Locate and edit the `research.toml` file in the project root. Configure it according to your desired operation mode and service setup.

3. **Ollama Setup (Required for Local AI):**
   **Important**: Ollama must run locally on your host machine, not in Docker.
   
   ```bash
   # Install Ollama (if not already installed)
   # Visit https://ollama.ai/download or use package manager
   
   # Start Ollama server
   ollama serve
   
   # Or use custom port (update OLLAMA_PORT in docker/.env accordingly)
   OLLAMA_HOST=0.0.0.0:11434 ollama serve
   
   # Pull required models
   ollama pull qwen3:14b
   ollama pull phi4-reasoning
   ```
   
   The system expects Ollama on `http://localhost:11434` by default (configurable via `OLLAMA_BASE_URL` in `docker/.env`).

4. Build and Start Services:

   Navigate to the `docker/` directory:

   ```bash
   cd docker
   ```

   Then, build and start the services using Docker Compose. Choose the appropriate command based on your hardware:

   * **CPU-only:**

     ```bash
     docker compose -f docker-compose.persist.yml up --build
     ```

   * **NVIDIA GPU:**

     ```bash
     docker compose -f docker-compose.persist.yml -f docker-compose.cuda.yml up --build
     ```

   * **AMD GPU:**

     ```bash
     docker compose -f docker-compose.persist.yml -f docker-compose.rocm.yml up --build
     ```

   Add the `-d` flag to run in detached mode.

#### Accessing Services

Once the services are running, you can access them at the following default addresses:

* **API Endpoint:** `http://localhost:8000/v1`
* **Web UI:** `http://localhost:7860`
* **SearXNG:** `http://localhost:4000` (if using the included SearXNG service).

## Using the Web UI (Gradio)

The Web UI provides an easy way to interact with the research agent, especially for starting new tasks and resuming sessions.

### Starting the UI

Ensure the main API server (`python -m deep-search-persist` or Docker equivalent) is running.

Navigate to the `simple-webui` directory and run:

```bash
cd simple-webui
python gradio_online_mode.py
cd ..
```

Access the UI in your browser, typically at `http://localhost:7860`.

### Web UI Features

The Gradio interface includes three main tabs:

1. **Research Tab**: Core research functionality with streaming responses
2. **Session Management Tab**: View, manage, and delete saved research sessions
3. **System Status Tab**: Monitor Docker containers and Ollama server status
   - Real-time status monitoring with visual indicators (✅/❌/⚠️)
   - Docker container health checking
   - Ollama server connectivity and model availability
   - Terminal launch button (when Ollama is not running)
   - Configurable terminal commands via `research.toml`

### Interacting with the UI

* **New Research:** Input your query, select models, and adjust parameters.
* **Resuming Sessions:** If the API server has persistence enabled, you can input a `session_id` to resume a previous research task. Session files are typically stored in `simple-webui/logs/sessions/`.
* **System Monitoring:** Use the System Status tab to check if all services are running properly, especially Ollama.
* **Terminal Launch:** If Ollama is not running, click the terminal launch button to open a configured terminal session.

## Using the API

The application exposes an OpenAI-compatible API endpoint for programmatic access.

**Endpoint:** `http://localhost:8000/v1/chat/completions`

**Key Parameters in Request Body:**

* `model`: Should be set to `"deep_researcher"`.
* `messages`: Standard OpenAI messages array.
* `stream`: `true` or `false`.
* `max_iterations`: Research depth.
* `max_search_items`: Results per search query.
* `default_model`, `reason_model`: Can override `research.toml` settings.
* `session_id` (optional): Provide a `session_id` to resume a specific research task. If omitted for a new task, a new ID will be generated if persistence is active.

### Example `curl` Request

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \ # Use key from research.toml
  -d '{
    "model": "deep_researcher",
    "messages": [{"role": "user", "content": "Latest advancements in AI-driven drug discovery"}],
    "stream": true,
    "max_iterations": 5,
    "max_search_items": 3
    # To resume, add: "session_id": "your_existing_session_id"
  }'
```

## Persistence and Session Management

[!IMPORTANT]
Session persistence is a core feature of the `deep-search-persist` module, allowing you to save and resume research tasks.

* **How it Works:** When a research task is initiated, if persistence is enabled (default behavior of the new module), a session is created. Progress, intermediate results, and final outputs are saved periodically to a session file.
* **Storage:** Session data is stored as JSON files in the `simple-webui/logs/sessions/` directory by default. Each file is named with a unique `session_id`.
* **Interruption:** You can stop the API server or the Web UI at any time. If a research task was in progress, its state up to the last save point will be persisted.
* **Resumption:**
  * **Via Web UI:** Enter the `session_id` in the designated field.
  * **Via API:** Include the `session_id` in your `/chat/completions` request.
  * The research will continue from where it left off.

[!TIP]
Regularly check the `simple-webui/logs/sessions/` directory to see your saved sessions.

## How It Works (Conceptual Flow)

The `deep-search-persist` module orchestrates the research process based on the configured mode and user input.

```mermaid
graph TB;
    subgraph Input
    A[User Query / Session ID]
    end
    subgraph Configuration
    Conf[research.toml]
    end
    subgraph CoreLogic[deep-search-persist module]
    AA[Load Session (if ID provided)]
    subgraph Planning
    B[Generate Research Plan]
    E[Generate Writing Plan]
    end
    subgraph ResearchCycle
    C[Search Agent (SearXNG)]
    Pars[Content Parsing (Jina/Local)]
    D[Evaluate Results (LLM)]
    Store[Persist State]
    end
    subgraph Output
    F[Stream/Final Report]
    end
    end

    Conf --> CoreLogic
    A --> AA
    AA -* New Session --> B
    AA -* Existing Session --> Store
    B --> C
    C --> Pars
    Pars --> D
    D -* Need More --> C
    D -* Complete --> E
    E --> F
    ResearchCycle -* periodic --> Store
    Store --> F

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style F fill:#ccf,stroke:#333,stroke-width:2px
```

The process begins with a user query or a request to resume a session via a `session_id`. The core logic loads the configuration from `research.toml` and, if a `session_id` is provided, attempts to load the existing session state. For new tasks, a research plan is generated. The research cycle involves using SearXNG to find information, parsing the content of relevant results, evaluating the information using an LLM, and periodically persisting the current state. Once sufficient information is gathered, a writing plan is generated, leading to the final streamed or complete report.

## Core Components

* **`deep-search-persist` Module:** The heart of the application, managing research workflow, LLM interactions, and persistence.
* **`research.toml`:** Central configuration file for the project.
* **SearXNG:** A metasearch engine used for gathering search results from various sources. Can be self-hosted via Docker or public instances.
* **Content Parsers:** Tools like Jina API (online) or local methods (e.g., Playwright, potentially `reader-lm`) for extracting clean text content from web pages.
* **LLM Providers:**
  * OpenRouter API: Provides access to a wide range of online language models.
  * Ollama: Allows using local language models.
* **Gradio Web UI:** An interactive web interface for user interaction, task initiation, and session management.
* **Session Storage:** The directory (`simple-webui/logs/sessions/`) where research session data is saved as JSON files.

## Testing

The project includes a suite of tests to ensure functionality and stability.

Tests for the core persistence logic and other components are located in `deep-search-persist/tests/`.

To run tests (example using pytest):

```bash
pip install pytest pytest-asyncio
pytest deep-search-persist/tests/
```

## Roadmap

* [x] Modular Core (`deep-search-persist`)
* [x] Session Persistence & Resumption
* [x] Gradio Web UI for interaction and session management
* [x] Support Ollama
* [x] Support Playwright for local browsing (if `use_jina=false` and `use_embed_browser=true`)
* [x] Dockerization for API and SearXNG
* [ ] Refine process and reduce token usage (e.g., via DSPy or similar techniques).
* [ ] Add more parsing methods with a decision agent to optimize per-website extraction.
* [ ] Integrate tool calling capabilities for LLMs.
* [ ] Add classifier models to fact-check sources or assess relevance.
* [ ] Enhanced Web UI features (e.g., detailed session browser, direct log viewing).

## Troubleshooting

* **Configuration Issues:** Ensure `research.toml` is correctly formatted and all necessary API keys/endpoints are set. Check for typos or incorrect values.
* **Python Environment:** Verify all dependencies from `requirements-persist.txt` (and `simple-webui/requirements.txt` for UI) are installed. Consider using a virtual environment.
* **API Server Not Running:** The Web UI needs the `deep-search-persist` API server to be running in the background. Start the API server first before launching the UI.
* **Session Resumption Fails:** Check if the session ID is correct and the corresponding session file exists in `simple-webui/logs/sessions/`. Ensure file permissions allow the application to read the file.
* **Ollama Issues:** If using local models via Ollama, ensure the Ollama service is running **on your host machine** (not in Docker) and the specified models in `research.toml` are pulled and available. Use the System Status tab in the Web UI to check Ollama connectivity.
* **Rate Limits:** If using online APIs (like OpenRouter or Jina), you might encounter rate limits. Configure `request_per_minute` and `fallback_model` in `research.toml` if needed, or consider using local alternatives.
* **SearXNG Issues:** If using a self-hosted SearXNG instance, ensure it is running and accessible from where the `deep-search-persist` API is running. Verify the `searxng_url` in `research.toml`.

## Price Prediction

The cost of running research tasks depends heavily on the chosen LLM models, the complexity of the research query, the number of iterations, and the amount of content that needs to be processed. Using larger, more capable models will generally incur higher costs. Local models via Ollama can significantly reduce or eliminate API costs, but require local computing resources. Be mindful of your API usage and consider setting limits or using cost-effective models for less critical tasks.

## License

This project is licensed under the **GNU General Public License v3.0 or later**.
See the [`LICENSE`](LICENSE) file for more details.

## Author / Contact

* **Maintained by:** Andrew Cox
* **Contact:** [dev@andrewcox.doctor](mailto:dev@andrewcox.doctor)
* **Repository/Profile:** [https://github.com/sealad886](github.com/sealad886)

## Acknowledgements

* Gratitude to the original author(s) of OpenDeepResearcher.
* Thanks to the developers of SearXNG, Ollama, Gradio, Jina, Playwright, and other open-source tools and libraries used in this project.
