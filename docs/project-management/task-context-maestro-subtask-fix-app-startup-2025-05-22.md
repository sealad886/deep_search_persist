# Task Context: Resolve Application Startup Issues in Dockerized Environment

**Task ID**: `maestro-subtask-fix-app-startup-2025-05-22`

**Assigned Mode**: BackendForge

**Description**:
This task is delegated to BackendForge to resolve critical application startup issues within the Dockerized environment. The primary goal is to ensure that all Docker Compose services, particularly `app-persist` and `gradio-ui`, start successfully and are reported as healthy.

**Identified Issues from Previous Attempts (from TestCrafter mode)**:

1.  **Pydantic `NameError`**:
    *   **Error Message**: `NameError: Fields must not use names with leading underscores; e.g., use 'messages' instead of '_messages'.`
    *   **Origin**: `deep_search_persist/deep_search_persist/helper_classes.py`, specifically within the `Messages` class (around line 170).
    *   **Details**: Pydantic 2.x (or a newer version) disallows public fields in `BaseModel` classes from starting with an underscore. The `_messages` field in the `Messages` class needs to be renamed to `messages`, and all internal references to `self._messages` within the `Messages` class methods must be updated to `self.messages`. The `__init__` method also needs adjustment to correctly initialize the `messages` field.

2.  **Missing `JINA_API_KEY` Configuration**:
    *   **Error Message**: `KeyError: "Mandatory key 'jina_api_key' not found in section 'API'"`
    *   **Origin**: `deep_search_persist/deep_search_persist/configuration.py` during application startup.
    *   **Details**: The application is attempting to load a mandatory `jina_api_key` from its configuration, but it's not found. Logs indicate "Configuration file not found, using defaults," suggesting that `research.toml` (which is copied to `/app/research.toml` in the Dockerfile) is not being correctly loaded or accessed by the application. The `JINA_API_KEY` needs to be provided, either by ensuring `research.toml` is correctly read and contains the key, or by setting it as an environment variable if that's the intended mechanism.

**Acceptance Criteria**:
*   The `deep_search_persist/deep_search_persist/helper_classes.py` file is modified to resolve the Pydantic `NameError` (i.e., `_messages` is renamed to `messages`, and all internal references are updated).
*   The `JINA_API_KEY` is successfully provided to the `app-persist` container, resolving the `KeyError`. This may involve modifying `docker/research.toml` or the Dockerfile/docker-compose setup to pass it as an environment variable.
*   All Docker Compose services (`app-persist`, `gradio-ui`, `mongo`, `redis-persist`, `ollama`, `searxng-persist`, `backup-persist`) start successfully and are reported as healthy when running `docker compose -f docker/docker-compose.persist.yml up -d --wait`.

**Mandatory Context Files for BackendForge**:
BackendForge, you MUST read the following files before starting this task:
*   `/docs/project-management/task-context-test-implementation-execution-2025-05-21.md` (for overall context of the previous testing task)
*   `/docs/project-management/workflow-state.md` (for current workflow status and task dependencies)
*   `/deep_search_persist/deep_search_persist/helper_classes.py` (for Pydantic error fix)
*   `/deep_search_persist/deep_search_persist/configuration.py` (to understand configuration loading)
*   `/docker/research.toml` (to inspect existing configuration)
*   `/docker/docker-compose.persist.yml` (to inspect service definitions and environment variables)
*   `/docker/Dockerfile` (to understand application image build process)
*   `/requirements.txt` (to ensure all necessary Python dependencies are listed)

**Dependencies**: None (this is a new coordination task to unblock further testing).

**Expected Deliverables**:
*   Updated `deep_search_persist/deep_search_persist/helper_classes.py`.
*   Updated `docker/research.toml` or `docker-compose.persist.yml` (or both) to resolve `JINA_API_KEY` issue.
*   Confirmation that `docker compose -f docker/docker-compose.persist.yml up -d --wait` runs successfully with all services healthy.

**Next Steps (after BackendForge completes)**:
Upon successful completion, Maestro will verify the Docker environment health and then delegate back to TestCrafter to continue with test execution and reporting.
