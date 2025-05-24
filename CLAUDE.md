# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
# Run the main API server
python -m deep_search_persist

# Run the Gradio Web UI (requires API server running)
cd simple_webui && python gradio_online_mode.py
```

### Testing
```bash
# Run all tests
python -m pytest

# Run specific test types
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/  # Integration tests  
python -m pytest tests/e2e/          # End-to-end tests

# Run tests in the core module
python -m pytest deep_search_persist/tests/

# Run specific test file
python -m pytest tests/unit/test_configuration.py

# Run with coverage (if installed)
python -m pytest --cov=deep_search_persist
```

### Installation & Dependencies
```bash
# Core installation
pip install .

# Install with development dependencies
pip install .[dev]

# Install with web UI dependencies
pip install .[web]

# Install everything
pip install .[all]
```

### Docker Operations
```bash
# Build and run with Docker Compose (from docker/ directory)
cd docker
docker compose -f docker-compose.persist.yml up --build

# With CUDA GPU support
docker compose -f docker-compose.persist.yml -f docker-compose.cuda.yml up --build
```

### Ollama Setup (Required for Local AI)
**Important**: Ollama now runs locally, not in Docker. Start Ollama before using the system:

```bash
# Install Ollama (if not already installed)
# Visit https://ollama.ai/download or use package manager

# Start Ollama server
ollama serve

# Or use custom port (update OLLAMA_PORT in docker/.env accordingly)
OLLAMA_HOST=0.0.0.0:11235 ollama serve
```

The system expects Ollama on `http://localhost:11434` by default (configurable via `OLLAMA_BASE_URL` in `docker/.env`).

### Code Quality
```bash
# Format code (based on pyproject.toml settings)
black deep_search_persist/
isort deep_search_persist/

# Lint with line length 120
flake8 deep_search_persist/ --max-line-length=120
```

## Architecture Overview

### Core Module Structure
The application is built around the `deep_search_persist` Python module with these key components:

- **`main_routine.py`**: Orchestrates the research workflow, handles async generators for streaming responses
- **`research_session.py`**: Pydantic models for session management and state tracking
- **`persistence/session_persistence.py`**: MongoDB-backed session persistence with rollback capabilities
- **`api_endpoints.py`**: FastAPI server providing OpenAI-compatible chat completions endpoint
- **`configuration.py`**: TOML-based configuration management with environment variable support
- **`helper_functions.py`**: Core research operations (search, parsing, planning, report generation)
- **`local_ai.py`**: Ollama integration for local LLM inference

### Configuration System
Primary configuration is via `research.toml` at the project root, supporting:
- **Multi-mode operation**: Online, Hybrid, Local modes via `use_ollama`, `use_jina` flags
- **Docker environment**: Automatically switches to `/app/research.toml` when `DOCKER_CONTAINER` env var is set
- **Environment variable overrides**: For API keys and service URLs
- **Ollama configuration**: Local server URL and connection settings
- **WebUI customization**: Terminal launch commands and port configuration

#### Key Configuration Sections
```toml
[LocalAI]
ollama_base_url = "${OLLAMA_BASE_URL}"  # Points to local Ollama server

[WebUI]
terminal_launch_command = "/bin/zsh -i -c zf"  # Custom terminal command
gradio_host_port = 7860
gradio_container_port = 7860
```

### Session Persistence Architecture
- **MongoDB backend**: Incremental saves, full history, rollback points
- **Async operations**: All persistence operations are async using Motor (MongoDB async driver)
- **Session resumption**: Research can be interrupted and resumed via session_id
- **State management**: Uses Pydantic models for type-safe session serialization

### Research Workflow
1. **Planning Phase**: Generate research plan and search queries (if `with_planning=true`)
2. **Search & Parse**: Query SearXNG, parse content via Jina API or local Playwright
3. **Evaluation**: LLM judges search results and refines plans
4. **Iteration**: Repeat until sufficient information gathered
5. **Report Generation**: Create final structured report

### API Design
- **OpenAI-compatible endpoint**: `/v1/chat/completions` for seamless integration
- **Streaming support**: Real-time response streaming via Server-Sent Events
- **Session parameters**: `session_id`, `max_iterations`, `max_search_items` in request body
- **Model override**: Can override TOML settings per request

### Testing Strategy
- **Unit tests**: Individual components (`tests/unit/`)
- **Integration tests**: Component interactions (`tests/integration/`)
- **E2E tests**: Full workflow testing (`tests/e2e/`)
- **Core module tests**: Additional tests in `deep_search_persist/tests/`

### Docker Architecture
- **Multi-container setup**: API, SearXNG, MongoDB, Gradio Web UI (Ollama runs locally)
- **GPU support**: Optional CUDA/ROCm compose files
- **Configuration mounting**: `research.toml` mounted from host
- **Persistent volumes**: MongoDB data and session storage
- **Local Ollama integration**: Containers connect to host Ollama via `host.docker.internal`

### Gradio Web UI Features
The Gradio interface includes three main tabs:

1. **Research Tab**: Core research functionality with streaming responses
2. **Session Management Tab**: View, manage, and delete saved research sessions
3. **System Status Tab**: Monitor Docker containers and Ollama server status
   - Real-time status monitoring with visual indicators (✅/❌/⚠️)
   - Docker container health checking
   - Ollama server connectivity and model availability
   - Terminal launch button (when Ollama is not running)
   - Configurable terminal commands via `research.toml`

## Important Implementation Notes

### Error Handling
- All async operations use proper exception handling with loguru logging
- Session persistence includes rollback capabilities for error recovery
- Configuration loading falls back to defaults for missing values

### Performance Considerations
- Concurrent request limiting via `concurrent_limit` setting
- Rate limiting for external APIs (`request_per_minute`)
- Browser resource management with cooldown periods
- PDF processing limits (`pdf_max_pages`, `pdf_max_filesize`)

### Security
- API key configuration via TOML or environment variables
- No hardcoded credentials in source code
- Docker security with minimal container privileges
