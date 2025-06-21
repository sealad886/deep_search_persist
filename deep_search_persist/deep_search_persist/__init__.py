from .api_models import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
    Messages,
    ModelList,
    ModelObject,
)
from .configuration import app_config
from .research_session import ResearchSession
from .main_routine import (
    async_main,
    generate_research_response,
    extract_relevant_context_async,
    generate_search_queries_async,
    generate_writing_plan_async,
    is_page_useful_async,
    judge_search_result_and_refine_plan_async,
    make_initial_searching_plan_async,
    perform_search_async,
)
from .local_ai import (
    call_ollama_async,
    call_openrouter_async,
    # openrouter_last_request_times, # This needs to be confirmed where it lives or if still used
    fetch_webpage_text_async,
    get_cleaned_html,
    get_global_semaphore, # Replaced direct global_semaphore access
)
# from .helper_functions import (
#     # get_domain, # Removed as it's not found in helper_functions.py
#     # If openrouter_last_request_times is here, add it
# )

# Explicitly import modules if they are part of the public API
from . import api_endpoints
# from . import chat_completions  # File not found
from . import helper_classes # if it contains public classes
# from . import pdf_processing # Assuming process_pdf, download_pdf are in a module named pdf_processing

# Note: domain_locks, domain_next_allowed_time, pdf_processing_lock were globals,
# their management might have changed with app_config or moved into specific modules.
# For now, not re-exporting them unless their source is clear.
# Also, symbols like process_pdf, download_pdf need to be sourced from their actual module.
# Assuming they might be in a 'pdf_processing.py' or similar.
# For now, I'll remove them from __all__ unless their module is clear.

__all__ = [
    "app_config",
    # API Models & Core Classes
    "ChatCompletionChoice",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "Message",
    "Messages",
    "ModelList",
    "ModelObject",
    "ResearchSession", # Defined in .research_session
    # Core functions from main_routine
    "async_main",
    "generate_research_response",
    "extract_relevant_context_async",
    "generate_search_queries_async",
    "generate_writing_plan_async",
    "is_page_useful_async",
    "judge_search_result_and_refine_plan_async",
    "make_initial_searching_plan_async",
    "perform_search_async",
    # Functions from local_ai
    "call_ollama_async",
    "call_openrouter_async",
    "fetch_webpage_text_async",
    "get_cleaned_html",
    "get_global_semaphore",
    # Functions from helper_functions
    # "get_domain", # Removed as it's not found in helper_functions.py
    # Modules
    "api_endpoints",
    # "chat_completions",  # File not found
    "helper_classes",
    # "pdf_processing", # Module name needs confirmation
    # Potentially other key classes/functions if they are part of the public API
]

# Note: simple_webui is now located at deep_search_persist/simple_webui/ (one level up)
# and no longer imported here to avoid circular imports
