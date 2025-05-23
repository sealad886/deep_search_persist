# Comprehensive Test Plan for deep_search_persist

**Task ID:** test-plan-definition-2025-05-21

This document outlines a comprehensive test plan for the `deep_search_persist` package, structured according to the SPARC iteration cycle (Specification, Pseudocode, Architecture, Refinement, and Completion). The plan addresses testing within a Dockerized environment and focuses on *what* needs to be tested to ensure reliability, performance, security, data integrity, usability, and ease of integration.

## 1. Specification (What to Test)

This phase defines the scope and requirements for testing the `deep_search_persist` package. The focus is on identifying all functionalities, scenarios, and conditions that need verification, explicitly including testing within the defined Dockerized environment.

### Functionalities to be Tested:

*   **API Endpoints (`deep_search_persist/deep_search_persist/api_endpoints.py:12`)**:
    *   Health Check (`GET /`): Verify the endpoint returns a 200 status code and "ok" status.
    *   Chat Completions (`POST /chat/completions`):
        *   Verify successful execution of the research workflow for various valid user queries and system instructions.
        *   Test different `max_iterations` settings.
        *   Verify correct streaming of responses via Server-Sent Events (SSE).
        *   Test handling of empty or invalid `messages` in the request body.
        *   Verify error handling and appropriate responses for issues during the research process (e.g., LLM failures, search errors, parsing issues).
    *   Session Management:
        *   `GET /sessions`: Verify listing of all saved sessions, including correct summary data (ID, status, timestamps, iteration).
        *   `GET /sessions/{session_id}`: Verify retrieval of full session data for a valid session ID. Test with non-existent IDs.
        *   `DELETE /sessions/{session_id}`: Verify successful deletion of a session. Test with non-existent IDs.
        *   `POST /sessions/{session_id}/resume`: Verify successful loading of a session for resumption. Test with non-existent or non-resumable sessions.
        *   `GET /sessions/{session_id}/history`: Verify retrieval of iteration history for a session. Test with sessions having no history or non-existent IDs.
        *   `POST /sessions/{session_id}/rollback/{iteration}`: Verify successful rollback to a specified iteration. Test with invalid session IDs or non-existent iterations.
    *   Model Listing (`GET /models`): Verify the endpoint returns a list of available models in the expected format.

*   **Helper Functions (`deep_search_persist/deep_search_persist/helper_functions.py:17`)**:
    *   LLM Interaction (`call_llm_async`, `call_openrouter_async`, `call_ollama_async`):
        *   Test calls with various message inputs, models, and context sizes.
        *   Verify handling of successful responses and errors from LLM APIs.
        *   Test rate limiting and fallback model logic (`deep_search_persist/deep_search_persist/local_ai.py:46`).
    *   Research Planning (`make_initial_searching_plan_async`, `judge_search_result_and_future_plan_async`, `generate_writing_plan_async`):
        *   Test plan generation with different user queries and contexts.
        *   Verify the structure and content of generated plans.
        *   Test handling of empty or ambiguous inputs.
    *   Search Query Generation (`generate_search_queries_async`, `get_new_search_queries_async`):
        *   Test query generation based on research plans and previous results.
        *   Verify the format of generated queries (list of strings).
        *   Test the `<done>` condition for ending research.
    *   Web Interaction (`perform_search_async`, `fetch_webpage_text_async`, `process_link`, `is_page_useful_async`, `extract_relevant_context_async`):
        *   Test search execution with various queries and verify the format of returned links.
        *   Test fetching and parsing of different webpage types (HTML, PDF) and content sizes.
        *   Verify the logic for determining page usefulness and extracting relevant context.
        *   Test handling of network errors, timeouts, and invalid URLs.
        *   Verify concurrency limits and per-domain cooldowns are respected.
    *   Report Generation (`generate_final_report_async`):
        *   Test report generation based on aggregated contexts and writing plans.
        *   Verify the structure, content, and citation format of the final report.

*   **Helper Classes (`deep_search_persist/deep_search_persist/helper_classes.py:28`)**:
    *   `Message`: Test instantiation, attribute access, and serialization/deserialization (`to_dict`, `from_dict`, `to_json`, `from_json`). Test validation for required fields and data types.
    *   `Messages`: Test instantiation, adding messages (`add_message`), retrieving messages (`get_messages`), serialization (`to_list_of_dicts`, `to_openai_format`), deserialization (`from_list_of_dicts`), and utility methods (`pretty_print`, `filter_by_sender`, `sort_by_timestamp`). Test validation for allowed roles and message types.

*   **Persistence (`deep_search_persist/deep_search_persist/persistence/session_persistence.py:137`)**:
    *   `SessionPersistenceManager`:
        *   Test database connection and initialization.
        *   Test saving new sessions and updating existing ones (`save_session`).
        *   Test loading sessions (`load_session`).
        *   Test listing sessions (`list_sessions`) with and without user ID filtering.
        *   Test deleting sessions (`delete_session`).
        *   Test resuming sessions (`resume_session`).
        *   Test retrieving iteration history (`get_iteration_history`).
        *   Test rolling back sessions (`rollback_to_iteration`).
        *   Verify data integrity and consistency across all persistence operations.
        *   Test error handling for database operations (e.g., connection errors, invalid data).
        *   Verify validation hash functionality for data integrity checks.
    *   `SessionStatuses`, `SessionSummary`, `SessionSummaryList`: Unit tests for data models and their methods, including status validation and time calculations in `SessionSummaryList`.
    *   Utility functions (`deep_search_persist/deep_search_persist/persistence/utils.py`): Unit tests for date/time conversion and dictionary cleaning functions.

*   **Configuration (`deep_search_persist/deep_search_persist/configuration.py:18`)**:
    *   Test loading configuration from `research.toml` and environment variables.
    *   Test retrieving configuration values with default values and type conversions (`get_config_value`).
    *   Test error handling for missing or invalid configuration values.

*   **Research Session (`deep_search_persist/deep_search_persist/research_session.py:12`)**:
    *   `ResearchSession` model: Test instantiation, attribute access, and serialization (`dict`, `to_dict`). (Focus on the model structure as persistence is handled by `SessionPersistenceManager`).

### Testing within a Dockerized Environment:

All the above functionalities and scenarios MUST be tested within the Docker environment defined by [`docker/docker-compose.persist.yml`](docker/docker-compose.persist.yml) and [`docker/Dockerfile`](docker/Dockerfile). This includes:

*   Verifying that all services (app, mongo, searxng, redis, ollama, nginx, backup) start correctly and are healthy within Docker.
*   Testing the application's ability to communicate with other services using their Docker network names (e.g., `http://mongo:27017`, `http://searxng-persist:8080`).
*   Testing data persistence by stopping and restarting containers and verifying that data in mounted volumes (`mongo_data`, `temp_pdf_data`, `app_persist_data`, `redis_data`, `backup_data_volume`) is retained.
*   Verifying that the application correctly loads configuration from the `research.toml` file and environment variables within the Docker container.
*   Testing the backup service's functionality to ensure data is correctly copied to the backup volume.

### Quality Attributes to Address:

*   **Reliability:** Test the application's stability under various loads and error conditions. Verify graceful degradation and error reporting when external services fail.
*   **Performance:** Measure the response times of key API endpoints and the duration of core research workflow steps. Identify performance bottlenecks.
*   **Security:** Test input validation and sanitization. Verify compliance with GDPR regarding data storage and handling (though specific GDPR tests might require further requirements).
*   **Data Integrity:** Ensure data is accurately saved, loaded, and manipulated by the persistence layer. Verify the effectiveness of validation hashes.
*   **Usability:** (Primarily for the API's ease of integration) Verify clear API request/response formats and informative error messages.
*   **Ease of Integration:** Test the API's compatibility with the OpenAI format. Verify correct interaction with configured external services.

This phase focuses solely on *what* needs to be tested, providing a clear foundation for subsequent phases.

## 2. Pseudocode (Algorithmic Approach for Test Case Development)

This section outlines the high-level algorithmic approach for developing test cases for `deep_search_persist` using the SPARC cycle. It describes the *process* of creating tests rather than providing specific code examples.

```
Function DevelopTestCasesForSPARC(package_components, quality_attributes, docker_environment_spec):
    // SPARC Phase: Specification (Completed in Section 1)
    // Output: Detailed list of functionalities, scenarios, edge cases, error handling, integration points, and Docker considerations.

    // SPARC Phase: Pseudocode (This Section)
    // Outline the process for creating tests based on the Specification:

    For each component in package_components:
        Identify testable units (functions, classes, modules, API endpoints) within the component.
        Define specific test objectives for each testable unit based on the Specification.

        For each test objective:
            Determine the required input data sets:
                Include valid inputs for positive scenarios.
                Include invalid inputs for negative scenarios (e.g., wrong data types, missing fields).
                Include edge cases (e.g., empty strings, zero values, boundary conditions).
                Include data that triggers specific error handling paths.

            Define the expected outputs or behavior:
                Expected return values.
                Expected side effects (e.g., database changes, logs).
                Expected error types or messages.
                Expected system state changes.

            Outline the steps for setting up the test environment:
                If testing in Docker:
                    Describe how to use docker-compose to start required services (app, mongo, searxng, etc.).
                    Describe how to ensure services are healthy and ready.
                    Describe how to configure the test runner to interact with services via the Docker network.
                If testing outside Docker (for isolated unit tests):
                    Describe how to set up necessary mocks, stubs, or in-memory databases.

            Describe the test execution steps:
                How to call the function, method, or API endpoint under test with the defined inputs.

            Describe the assertion/validation steps:
                How to compare actual outputs/behavior with expected outputs/behavior.
                How to check for expected side effects.
                How to verify error handling.
                If testing in Docker, how to verify container state, logs, or data volumes.

            Specify cleanup steps:
                How to reset the environment or remove test data to ensure test isolation.
                If using Docker, how to stop and remove containers.

    // SPARC Phase: Architecture (See Section 3)
    // Output: Proposed test suite structure, dependency management, Docker integration details.

    // SPARC Phase: Refinement (See Section 4)
    // Output: Strategies for iterative improvement based on results and coverage.

    // SPARC Phase: Completion (See Section 5)
    // Output: Process for finalization, CI/CD integration, and reporting.

End Function
```

This pseudocode provides a structured approach for translating the "what" from the Specification phase into a process for defining the "how" of test case creation in subsequent phases.

## 3. Architecture (Test Suite Structure and Environment)

This section proposes a suitable test suite architecture for `deep_search_persist`, designed to facilitate the SPARC iterations and integrate seamlessly with the project's Dockerized environment.

### Test Suite Directory Structure:

The proposed directory structure within the `tests/` directory is organized by testing level:

```
tests/
├── unit/             # Unit tests for individual functions, classes, and modules
│   ├── test_api_models.py
│   ├── test_configuration.py
│   ├── test_helper_classes.py
│   ├── test_persistence_utils.py
│   └── ... (other unit test files)
├── integration/      # Integration tests for interactions between components
│   ├── test_api_persistence_integration.py
│   ├── test_helper_llm_integration.py
│   ├── test_helper_search_integration.py
│   └── ... (other integration test files)
├── e2e/              # End-to-end tests for critical user journeys in the full system
│   ├── test_research_workflow.py
│   ├── test_session_management_e2e.py
│   └── ... (other e2e test files)
├── data/             # Test data files (e.g., sample documents, JSON payloads)
│   ├── sample.pdf
│   ├── sample.html
│   └── ...
├── fixtures/         # Reusable test fixtures (e.g., test client, mock objects)
│   └── ...
├── utils/            # Test utility functions
│   └── ...
└── conftest.py       # Shared fixtures and test configuration
```

This structure clearly separates tests by scope, making the test suite easier to navigate, maintain, and execute selectively.

### Dependency Management:

*   Test dependencies (e.g., `pytest`, `pytest-asyncio`, `httpx` for API testing, `mongomock` or a test container for persistence, mocking libraries like `unittest.mock` or `pytest-mock`) should be specified in [`requirements/requirements-dev.txt`](requirements/requirements-dev.txt).
*   The `Dockerfile` should be updated to ensure these development dependencies are installed during the build process, making them available within the application container or a dedicated test runner container.

### Integration with Docker Compose and Dockerfile:

*   **Dockerfile (`docker/Dockerfile:1`)**: The `Dockerfile` should include a step to install the development dependencies from `requirements-dev.txt`. This can be done in the `pybuilder` stage or a dedicated test stage if needed, ensuring the test environment within the container has all necessary libraries.
*   **Docker Compose (`docker/docker-compose.persist.yml:1`)**: The `docker-compose.persist.yml` file serves as the blueprint for the test environment.
    *   The existing services (`app-persist`, `mongo`, `searxng-persist`, `redis`, `ollama`, `nginx`) provide the necessary components for integration and E2E testing.
    *   A dedicated test runner service can be added to `docker-compose.persist.yml`. This service would:
        *   Use the same image as `app-persist` (or a build context that includes test dependencies).
        *   Mount the local `tests/` directory into the container.
        *   Have `depends_on` relationships with the services it needs to interact with (e.g., `app-persist`, `mongo`).
        *   Execute the test command (e.g., `pytest`) as its `command`.
        *   Example snippet for `docker-compose.persist.yml`:

        ```yaml
          test-runner:
            container_name: test-runner
            build:
              context: ..
              dockerfile: docker/Dockerfile # Or a dedicated test Dockerfile
            volumes:
              - ./tests:/app/tests:ro # Mount local tests directory
              - ./deep_search_persist:/app/deep_search_persist:ro # Mount app code if needed for coverage
              - ./requirements:/app/requirements:ro # Mount requirements
            depends_on:
              - app-persist
              - mongo
              - searxng-persist
              - ollama
            environment:
              - MONGO_URI=mongodb://mongo:27017/deep_search_test # Use a separate test database
              - DEEP_SEARCH_API_BASE_URL=http://app-persist:8000/v1 # API endpoint within Docker network
              # Other necessary test environment variables
            command: ["pytest", "tests/"] # Command to run tests
        ```
    *   Test environment variables (e.g., `MONGO_URI` pointing to the test MongoDB container, API base URLs pointing to other services within the Docker network) should be configured for the test runner service.
    *   Volumes can be used to persist test data or output test reports from the container.
*   **Test Execution Flow:** Tests, especially integration and E2E tests, should be designed to be executed by starting the Docker Compose environment and running the test runner service. This ensures tests are run in an environment that closely mirrors the production deployment.

This architecture provides a scalable and maintainable structure for the test suite, tightly integrated with the project's Docker-based infrastructure.

## 4. Refinement (Iterative Improvement)

This section details strategies for iteratively improving test coverage and quality within each SPARC cycle. Refinement is a continuous process that uses feedback from test execution and analysis to enhance the test suite and the overall quality of the `deep_search_persist` package, including validating compatibility with the Docker Compose setup.

### Strategies for Iterative Refinement:

*   **Code Coverage Analysis:**
    *   After each test run (especially unit and integration tests), generate code coverage reports using tools like `pytest-cov`.
    *   Analyze the reports to identify lines, branches, and functions that are not being exercised by tests.
    *   Prioritize writing new test cases or expanding existing ones to cover these gaps, focusing on critical paths and complex logic.
*   **Test Result and Log Analysis:**
    *   Thoroughly analyze test failures to understand the root cause.
    *   Distinguish between actual application bugs, issues in the test code itself, or problems with the test environment (particularly when running in Docker).
    *   Utilize application logs (configured via `deep_search_persist/deep_search_persist/logging/logging_config.py`) and Docker container logs to gain insights into the system's behavior during test execution.
*   **Test Data Refinement:**
    *   Continuously review and refine test data sets.
    *   Expand data to cover a wider range of valid inputs, edge cases, and invalid data types identified during development or exploratory testing.
    *   Ensure test data is realistic and representative of production data where possible, while respecting privacy and security concerns (especially for GDPR compliance).
    *   Implement robust test data setup and teardown procedures to ensure tests are isolated and repeatable.
*   **Improving Test Stability and Resilience:**
    *   Identify and address flaky tests (tests that sometimes pass and sometimes fail without code changes).
    *   Investigate potential causes of flakiness, such as timing issues in asynchronous operations, dependencies on external service availability, or shared mutable state.
    *   Implement appropriate waiting mechanisms in integration and E2E tests that interact with asynchronous processes or external services.
    *   Enhance the use of mocking and stubbing in lower-level tests to reduce reliance on external dependencies and improve test determinism.
*   **Alignment with Documentation:**
    *   Ensure that the test plan, test case descriptions, and any automated test code comments are consistent with the project's functional and technical documentation.
    *   Update test documentation whenever application code or requirements change.
*   **Docker Compose Compatibility Validation:**
    *   Regularly execute the test suite within the Docker environment defined by `docker-compose.persist.yml`.
    *   Verify that the test runner container can successfully build, connect to, and interact with other services (Mongo, SearXNG, LLMs) within the Docker network.
    *   Test different configurations or versions of the Docker setup if applicable to ensure compatibility.
    *   Monitor resource usage and performance of tests running in Docker.
*   **Feedback Loop Integration:**
    *   Establish a feedback loop where insights from test execution, coverage analysis, and bug reports inform the ongoing development process and subsequent SPARC iterations.
    *   Use test results to prioritize bug fixes and guide further development efforts.

Refinement is an ongoing process throughout the development lifecycle, ensuring the test suite remains effective and the application's quality continuously improves.

## 5. Completion (Finalizing the Test Suite)

This section describes the process for finalizing the test suite after multiple SPARC cycles have been completed and the test coverage is deemed sufficient. This phase focuses on ensuring the test suite is robust, automated, integrated into the CI/CD pipeline, and provides comprehensive reporting, all within the Dockerized environment.

### Process for Finalizing the Test Suite:

*   **Feature Coverage Verification:**
    *   Conduct a final review of the test suite against the initial Test Requirements (Specification) and any updated requirements.
    *   Use a traceability matrix to confirm that all defined functionalities, positive and negative scenarios, edge cases, error handling conditions, and integration points are covered by automated tests.
    *   Address any remaining coverage gaps by developing necessary test cases.
*   **Automated Execution in Docker:**
    *   Ensure the entire test suite (unit, integration, and E2E tests) is fully automated and can be executed reliably within the Docker environment defined by [`docker/docker-compose.persist.yml`](docker/docker-compose.persist.yml).
    *   Develop and refine the necessary scripts or commands to:
        *   Build the application and test runner Docker images.
        *   Start all required services using Docker Compose.
        *   Execute the test suite within the test runner container.
        *   Collect test results and coverage reports from within the container.
        *   Stop and clean up the Docker environment after test execution.
    *   Verify that the automated execution process is stable and produces consistent results across different runs.
*   **CI/CD Integration:**
    *   Integrate the automated Docker-based test execution into the project's Continuous Integration/Continuous Deployment (CI/CD) pipeline.
    *   Configure the CI/CD system (e.g., GitHub Actions, GitLab CI, Jenkins) to trigger the test suite automatically on relevant events (e.g., code pushes to main branches, pull request creation/updates).
    *   Ensure that static analysis tools (linters, formatters) are also part of the CI checks.
    *   Configure the pipeline to use the test results as quality gates, preventing code merges or deployments if tests fail or coverage targets are not met.
*   **Comprehensive Test Reporting:**
    *   Configure the test runner and CI/CD pipeline to generate comprehensive and easily understandable test reports.
    *   Reports should include:
        *   Summary of test results (total tests, passed, failed, skipped).
        *   Detailed information on failed tests (test name, error message, traceback).
        *   Code coverage metrics (line, branch, function coverage).
        *   Test execution duration.
    *   Integrate reporting with CI/CD dashboards or external reporting tools for visibility to the development team and stakeholders.
*   **Documentation Finalization:**
    *   Ensure all test documentation, including the test plan, test case descriptions, and instructions for running tests (especially in Docker), is complete, accurate, and up-to-date.
    *   Document the CI/CD pipeline configuration related to testing.
*   **Criteria for Completion:**
    *   The test suite is considered finalized and the Completion phase is achieved when:
        *   All requirements from the Specification phase are covered by automated tests running in the Dockerized environment.
        *   The test suite consistently passes in the CI/CD pipeline.
        *   Target code coverage metrics are achieved and maintained.
        *   Test reports are comprehensive and easily accessible.
        *   Stakeholders have reviewed and approved the test coverage and quality metrics.
        *   The test suite is fully integrated into the development workflow and CI/CD pipeline.

This Completion phase ensures that the test suite is a robust and integral part of the development process, providing continuous quality assurance for the `deep_search_persist` package within its intended Dockerized deployment environment.
