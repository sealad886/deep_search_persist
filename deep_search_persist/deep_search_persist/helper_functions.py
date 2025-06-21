# ============================
# Asynchronous Helper Functions
# ============================
import asyncio
import re
from typing import Any, AsyncGenerator, Awaitable, Callable, Coroutine, List, Literal, Optional, Union

import aiohttp
from loguru import logger

from .logging.logging_config import log_operation

from .configuration import app_config
from .helper_classes import Message, Messages
from .local_ai import call_ollama_async, fetch_webpage_text_async, call_llm_async, call_llm_async_parse_list


@log_operation("make_initial_searching_plan", level="DEBUG")
async def make_initial_searching_plan_async(session: aiohttp.ClientSession, helper_messages: Messages) -> Optional[str]:
    """
    Ask the reasoning LLMs to produce a research plan based on the user's query.
    """
    logger.info("Creating initial search plan")
    user_query_str = ""
    for msg in helper_messages.get_messages():
        if msg.role == "user":
            user_query_str = msg.content
            break
    if not user_query_str:  # Should ideally not happen if Messages is well-formed
        # Fallback or raise error
        first_message = helper_messages[0].content if len(helper_messages) > 0 else "No query found"
        logger.warning(
            "No user message found in Messages",
            context="make_initial_searching_plan_async",
            fallback_message=first_message,
        )
        user_query_str = first_message

    from ._prompts import INITIAL_SEARCH_PLAN_PROMPT

    prompt = INITIAL_SEARCH_PLAN_PROMPT

    messages_list_dict = [
        {
            "role": "system",
            "content": (
                "You are an advanced reasoning LLM that guides a following "
                "search agent to search for relevant information."
            ),
        },
        {"role": "user", "content": f"User Query: {user_query_str}\n\n{prompt}"},
    ]

    # Convert list of dicts to Messages
    llm_helper_messages = Messages(messages=[Message(role=m["role"], content=m["content"]) for m in messages_list_dict])

    response = await call_llm_async(session, llm_helper_messages, model=app_config.reason_model, ctx=app_config.reason_model_ctx)
    if response:
        try:
            # Remove <think>...</think> tags and their content if they exist
            cleaned_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
            logger.debug("Generated research plan", plan_length=len(cleaned_response))
            return cleaned_response
        except Exception as e:
            logger.exception("Failed to process research plan", error=str(e))
    return None


@log_operation("judge_search_result_and_future_plan", level="DEBUG")
async def judge_search_result_and_future_plan_async(
    session: aiohttp.ClientSession,
    helper_messages: Messages,
    current_plan: str,
    all_contexts_str: str,
) -> Optional[str]:
    """
    Ask the reasoning LLMs to judge the result of the search attempt and produce a plan for the next iteration.
    """
    user_query_str = ""
    for msg in helper_messages:
        if msg.role == "user":
            user_query_str = msg.content
            break
    if not user_query_str:
        first_message = helper_messages[0].content if len(helper_messages) > 0 else "No query found"
        logger.warning(
            "No user message found in Messages",
            context="judge_search_result_and_future_plan_async",
            fallback_message=first_message,
        )
        user_query_str = first_message

    from ._prompts import JUDGE_SEARCH_RESULTS_PROMPT

    prompt = JUDGE_SEARCH_RESULTS_PROMPT

    messages_list_dict = [
        {
            "role": "system",
            "content": (
                "You are an advanced reasoning LLM that guides a following "
                "search agent to search for relevant information."
            ),
        },
        {
            "role": "user",
            "content": f"User Query: {user_query_str}\nCurrent Research Plan: {current_plan}\nAggregated Contexts from previous searches:\n{all_contexts_str}\n\n{prompt}",
        },
    ]
    llm_helper_messages = Messages(messages=[Message(role=m["role"], content=m["content"]) for m in messages_list_dict])
    response = await call_llm_async(session, llm_helper_messages, model=app_config.reason_model, ctx=app_config.reason_model_ctx)
    if response:
        try:
            # Remove <think>...</think> tags and their content if they exist
            cleaned_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
            logger.debug("Generated next research plan", plan_length=len(cleaned_response))
            return cleaned_response
        except Exception as e:
            logger.exception("Failed to process research plan response", error=str(e))
    return None


@log_operation("generate_writing_plan", level="DEBUG")
async def generate_writing_plan_async(
    session: aiohttp.ClientSession,
    helper_messages: Messages,
    aggregated_contexts_str: str,
) -> Optional[str]:
    """
    Ask the reasoning LLMs to generate a writing plan based on
    the user’s query and aggregated contexts.
    """
    user_query_str = ""
    for msg in helper_messages:
        if msg.role == "user":
            user_query_str = msg.content
            break
    if not user_query_str:
        first_message = helper_messages[0].content if len(helper_messages) > 0 else "No query found"
        logger.warning(
            "No user message found in Messages", context="generate_writing_plan_async", fallback_message=first_message
        )
        user_query_str = first_message

    from ._prompts import GENERATE_WRITING_PLAN_PROMPT  # Corrected prompt import

    prompt = GENERATE_WRITING_PLAN_PROMPT

    messages_list_dict = [
        {
            "role": "system",
            "content": (
                "You are an advanced reasoning LLM that guides a following " "writer to write a research report."
            ),
        },
        {
            "role": "user",
            "content": (
                f"User Query: {user_query_str}\n" f"Aggregated Contexts: {aggregated_contexts_str}\n\n{prompt}"
            ),
        },
    ]
    llm_helper_messages = Messages(messages=[Message(role=m["role"], content=m["content"]) for m in messages_list_dict])
    response = await call_llm_async(session, llm_helper_messages, model=app_config.reason_model, ctx=app_config.reason_model_ctx)
    if response:
        try:
            # Remove <think>...</think> tags and their content if they exist
            cleaned_response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
            logger.debug("Generated writing plan", plan_length=len(cleaned_response))
            return cleaned_response
        except Exception as e:
            logger.exception("Failed to process writing plan response", error=str(e))
    return None


@log_operation("generate_search_queries", level="DEBUG")
async def generate_search_queries_async(session: aiohttp.ClientSession, query_plan: str) -> List[str]:
    """
    Generate a list of search queries based on the given query plan.
    """
    logger.info("Generating search queries from plan")

    from ._prompts import GENERATE_SEARCH_QUERIES_PROMPT

    prompt = GENERATE_SEARCH_QUERIES_PROMPT

    messages_list_dict = [
        {"role": "system", "content": "You are a systematic research planner."},
        {"role": "user", "content": f"Research Plan: {query_plan}\n\n{prompt}"},
    ]
    llm_helper_messages = Messages(messages=[Message(role=m["role"], content=m["content"]) for m in messages_list_dict])
    # Use the new centralized parsing method
    queries = await call_llm_async_parse_list(session, llm_helper_messages, model=app_config.default_model, ctx=app_config.default_model_ctx)
    if isinstance(queries, list):
        return queries
    else:
        logger.error("Unexpected result from LLM list parsing", result=queries, result_type=type(queries).__name__)
        return []


@log_operation("web_search", level="DEBUG")
async def perform_search_async(session: aiohttp.ClientSession, query: str) -> List[str]:
    """Perform a search using the provided query."""
    params = {"q": query, "format": "json"}
    try:
        logger.debug("Initiating search request", query=query, base_url=app_config.base_searxng_url)

        async with session.get(app_config.base_searxng_url, params=params) as resp:
            if resp.status == 200:
                results = await resp.json()
                if "results" in results:
                    links = [item.get("url") for item in results["results"] if "url" in item]
                    logger.debug("Search completed successfully", query=query, result_count=len(links))
                    return links
                else:
                    logger.warning("No results in search response", query=query)
                    return []
            else:
                text = await resp.text()
                logger.error("Search request failed", status=resp.status, response=text, query=query)
                return []
    except Exception as e:
        logger.exception("Error during search operation", query=query, error=str(e))
        return []

async def is_page_useful_async(
    session: aiohttp.ClientSession,
    helper_messages: Messages,
    page_text: str
) -> Optional[Literal["Yes", "No"]]:
    """
    Determine if a webpage is useful for answering the user's query.
    Returns "Yes" or "No".
    """
    user_query_str = ""
    for msg in helper_messages.get_messages():
        if msg.role == "user":
            user_query_str = msg.content
            break
    if not user_query_str:
        first_message = helper_messages[0].content if len(helper_messages) > 0 else "No query found"
        logger.warning(
            "No user message found in Messages", context="is_page_useful_async", fallback_message=first_message
        )
        user_query_str = first_message

    from ._prompts import IS_PAGE_USEFUL_PROMPT

    messages_list_dict = [
        {
            "role": "system",
            "content": "You are a strict and concise evaluator of research relevance.",
        },
        {
            "role": "user",
            "content": IS_PAGE_USEFUL_PROMPT.format(user_query_str, page_text),
        },
    ]
    llm_helper_messages = Messages(messages=[Message(role=m["role"], content=m["content"]) for m in messages_list_dict])
    response = await call_llm_async(session, llm_helper_messages, model=app_config.reason_model, ctx=app_config.reason_model_ctx)
    if response:
        answer = response.strip()
        if answer.lower() == "yes":
            return "Yes"
        elif answer.lower() == "no":
            return "No"
        else:
            return "No"  # Default to No if the response is not clear
    return "No"

@log_operation("extract_context", level="DEBUG")
async def extract_relevant_context_async(
    session: aiohttp.ClientSession,
    helper_messages: Messages,
    search_query: str,
    page_text: str
) -> str:
    """
    Extract relevant context from a webpage.
    Returns extracted context as a string, or an empty string if none.
    """
    user_query_str = ""
    for msg in helper_messages.get_messages():
        if msg.role == "user":
            user_query_str = msg.content
            break
    if not user_query_str:
        first_message = helper_messages[0].content if len(helper_messages) > 0 else "No query found"
        logger.warning(
            "No user message found in Messages",
            context="extract_relevant_context_async",
            fallback_message=first_message,
        )
        user_query_str = first_message

    messages_list_dict = [
        {
            "role": "system",
            "content": "You are an expert in extracting and summarizing relevant information.",
        },
        {
            "role": "user",
            "content": (
                f"User Query: {user_query_str}\nSearch Query: {search_query}\n\n"
                f"Webpage Content:\n{page_text}\n\n"
                "You are an expert information extractor. Given the user's query, "
                "the search query that led to this page, and the webpage content, "
                "extract all pieces of information that are relevant to "
                "answering the user's query. Return only the relevant context "
                "as plain text without commentary."
            ),
        },
    ]
    llm_helper_messages = Messages(messages=[Message(role=m["role"], content=m["content"]) for m in messages_list_dict])
    response = await call_llm_async(session, llm_helper_messages, model=app_config.default_model, ctx=app_config.default_model_ctx)
    return response if response else ""


@log_operation("get_new_search_queries", level="DEBUG")
async def get_new_search_queries_async(
    session: aiohttp.ClientSession,
    helper_messages: Messages,
    new_research_plan: Optional[str],
    previous_search_queries: List[str],
    all_contexts: List[str],
) -> Union[List[str], Literal["<done>"]]:
    logger.info(
        "Determining if new search queries are needed",
        previous_query_count=len(previous_search_queries),
        context_count=len(all_contexts),
    )
    """
    Based on the original query, new research plan, previous search queries, and extracted contexts,
    ask the LLM whether additional search queries are needed.
    Returns a Python list of up to four queries, or "<done>" if research is complete.
    """
    user_query_str = ""
    for msg in helper_messages.get_messages():
        if msg.role == "user":
            user_query_str = msg.content
            break
    if not user_query_str:
        first_message = helper_messages[0].content if len(helper_messages) > 0 else "No query found"
        logger.warning(
            "No user message found in Messages", context="get_new_search_queries_async", fallback_message=first_message
        )
        user_query_str = first_message

    context_combined = "\n".join(all_contexts)
    prompt = (
        "You are an analytical research assistant. Based on the original query, the search queries performed so far, "
        "the next step plan by a planning agent and the extracted contexts from webpages, determine if further "
        "research is needed. If further research is needed, ONLY provide up to four new search queries as a Python "
        "list IN ONE LINE (for example, ['new query1', 'new query2']) in PLAIN text, NEVER wrap in code env. "
        "If you believe no further research is needed, respond with exactly <done>."
        "\nREMEMBER: Output ONLY a Python list or the token <done> WITHOUT any additional text or explanations."
    )
    messages_list_dict = [
        {"role": "system", "content": "You are a systematic research planner."},
        {
            "role": "user",
            "content": " ".join(
                [
                    "User Query:",
                    user_query_str,
                    "\nPrevious Search Queries:",
                    *("\n" + f"{i}: " + q for i, q in enumerate(previous_search_queries, 1)),
                    "\n\nExtracted Relevant Contexts:",
                    "\n" + context_combined,
                    ("\n\nNext Research Plan by planning agent:\n" + new_research_plan if new_research_plan else ""),
                    "\n\n" + prompt,
                ]
            ),
        },
    ]
    llm_helper_messages = Messages(messages=[Message(role=m["role"], content=m["content"]) for m in messages_list_dict])
    # Use the new centralized parsing method
    result = await call_llm_async_parse_list(session, llm_helper_messages, model=app_config.default_model, ctx=app_config.default_model_ctx)
    return result  # This will be either a list of strings, "<done>", or empty list


@log_operation("generate_final_report", level="DEBUG")
async def generate_final_report_async(
    session: aiohttp.ClientSession,
    helper_messages: Messages,
    report_planning: Optional[str],
    all_contexts: List[str],
) -> Optional[str]:
    logger.info(
        "Generating final research report", context_count=len(all_contexts), has_planning=report_planning is not None
    )
    """
    Generate the final comprehensive report using all gathered contexts.
    """
    user_query_str = ""
    system_instruction_str: Optional[str] = None
    # Extract user query and system instruction from Messages
    for msg in helper_messages.get_messages():
        if msg.role == "user" and not user_query_str:  # Take first user message as primary query
            user_query_str = msg.content
        elif msg.role == "system" and not system_instruction_str:  # Take first system message
            system_instruction_str = msg.content

    if not user_query_str:  # Fallback if no user message explicitly found
        # This case should ideally be prevented by checks in api_endpoints.py
        logger.warning("No user query found in Messages for generate_final_report_async")
        # Attempt to find any user message if primary one wasn't set
        user_messages_contents = [m.content for m in helper_messages.get_messages() if m.role == "user"]
        if user_messages_contents:
            user_query_str = user_messages_contents[0]
        else:
            user_query_str = "General research topic"  # Default if absolutely no user query

    context_combined = "\n".join(all_contexts)
    prompt = (
        "You are an expert researcher and report writer. Based on the gathered contexts above and the original query, "
        "write a comprehensive, well-structured, and detailed report that addresses the query thoroughly. "
        "Include all relevant insights and conclusions without extraneous commentary."
        "Math equations should use proper LaTeX syntax in markdown format, with \\(\\LaTeX{}\\) for inline, "
        "$$\\LaTeX{}$$ for block."
        "Properly cite all the VALID and REAL sources inline from 'Gathered Relevant Contexts' with [cite_number]"
        "and also summarize the corresponding bibliography list with their urls in markdown format in the end of your "
        "report. Ensure that all VALID and REAL sources from 'Gathered Relevant Contexts' that you have used to write "
        "this report or back your statements are properly cited inline using the [cite_number] format "
        "(e.g., [1], [2], etc.). Then, append a complete bibliography section at the end of your report in markdown "
        "format, listing each source with its corresponding URL. Please NEVER omit the bibliography."
        "REMEMBER: NEVER make up sources or citations, only use the provided contexts, if no source used or available,"
        "just write 'No available sources'."
    )

    messages_list_dict = [
        {
            "role": "system",
            "content": (
                "You are a skilled report writer."
                + (
                    f" There is also some extra system instructions: {system_instruction_str}"
                    if system_instruction_str
                    else ""
                )
            ),
        },
        {
            "role": "user",
            "content": (
                f"User Query: {user_query_str}\n\nGathered Relevant Contexts:\n{context_combined}"
                + (
                    f"\n\nWriting plan from a planning agent:\n{report_planning}"
                    if report_planning and not report_planning.startswith("Error:")
                    else ""
                )
                + f"\n\nWriting Instructions:{prompt}"
            ),
        },
    ]
    llm_helper_messages = Messages(messages=[Message(role=m["role"], content=m["content"]) for m in messages_list_dict])
    report = await call_llm_async(session, llm_helper_messages, model=app_config.default_model, ctx=app_config.default_model_ctx)
    return report


@log_operation("process_link", level="DEBUG")
async def process_link(
    session: aiohttp.ClientSession,
    link: str,
    helper_messages: Messages,
    search_query: str,
    create_chunk: Optional[Callable[[str], Any]] = None,
) -> AsyncGenerator[str, None]:
    """
    Process a single link: fetch, check usefulness, extract context. Streams status and yields context.
    """
    logger.debug("Starting link processing", link=link, search_query=search_query)

    # Initial status message
    status_msg = f"Fetching content from: {link}\n\n"
    if create_chunk:
        yield create_chunk(status_msg)
    logger.debug("Fetching content", link=link)

    try:
        # Create fetch task immediately
        fetch_task = asyncio.create_task(fetch_webpage_text_async(session, link))

        # Wait for fetch to complete
        page_text = await fetch_task
        if not page_text:
            logger.warning("No content fetched from link", link=link)
            return

        logger.debug("Content fetched successfully", link=link, content_length=len(page_text))

        # Create usefulness task immediately
        # is_page_useful_async now expects Messages
        usefulness_task: asyncio.Task[Optional[Literal["Yes", "No"]]] = asyncio.create_task(is_page_useful_async(session, helper_messages, page_text))

        # Wait for usefulness check and stream its result
        usefulness: Optional[Literal["Yes", "No"]] = await usefulness_task
        status_msg = f"Page usefulness for {link}: {usefulness}\n\n"
        if create_chunk:
            yield create_chunk(status_msg)
        else:
            logger.info(status_msg.strip())

        # If useful, extract context directly
        if usefulness == "Yes":
            logger.debug("Page deemed useful, extracting context", link=link)
            # Extract context directly
            context = await extract_relevant_context_async(session, helper_messages, search_query, page_text)
            if context:
                status_msg = f"Extracted context from {link} (first 200 chars): {context[:200]}\n\n"
                if create_chunk and app_config.verbose_web_parse:
                    yield create_chunk(status_msg)
                logger.debug("Context extracted successfully", link=link, context_length=len(context))
                context = "url:" + link + "\ncontext:" + context
                yield context
            else:
                logger.debug("No context extracted from useful page", link=link)
        else:
            logger.debug("Page deemed not useful, skipping context extraction", link=link)
    except Exception as e:
        logger.exception("Error processing link", link=link, error=str(e))
    return


@log_operation("judge_search_result", level="DEBUG")
async def judge_search_result_and_refine_plan_async(  # Renamed to avoid redefinition
    session: aiohttp.ClientSession,
    helper_messages: Messages,  # Changed
    current_plan_for_logic: str,
    combined_contexts_for_judgement: str,
) -> Optional[str]:
    cleaned_response: Optional[str] = None
    logger.info("Judging search results and refining plan", context_length=len(combined_contexts_for_judgement))
    """
    Ask the reasoning LLMs to judge the result of the search attempt and
    produce a plan for the next iteration.

    Args:
        session (aiohttp.ClientSession): The HTTP session for requests.
        helper_messages (Messages): The messages object containing user query and system instructions.
        current_plan_for_logic (str): The current plan for logic.
        combined_contexts_for_judgement (str): Combined contexts for judgement.

    Returns:
        Optional[str]: The next plan, or None if an error occurs.
    """
    user_query_str = ""
    for msg in helper_messages.get_messages():
        if msg.role == "user":
            user_query_str = msg.content
            break
    if not user_query_str:
        first_message = helper_messages[0].content if len(helper_messages) > 0 else "No query found"
        logger.warning(
            "No user message found in Messages",
            context="judge_search_result_and_refine_plan_async",
            fallback_message=first_message,
        )
        user_query_str = first_message

    # This prompt is different from the other judge_search_result_and_future_plan_async
    # defined earlier in the file. Consolidating or differentiating them clearly
    # would be a good next step if their purposes are meant to be distinct.
    # For now, refactoring this specific instance.
    prompt_instruction = (
        "Use the following information to judge the search result and produce "
        "a plan for the next iteration. Now, based on the above information "
        "and instruction, evaluate the search results and generate a refined "
        "research plan for the next iteration."
    )
    user_content = (
        f"User Query: {user_query_str}\n"
        f"Current Plan: {current_plan_for_logic}\n"
        f"Combined Contexts: {combined_contexts_for_judgement}\n\n"
        f"{prompt_instruction}"
    )

    messages_list_dict = [
        # The original system prompt was the constructed prompt.
        # The user message was just the combined_contexts.
        # This is unusual compared to other calls.
        # Re-aligning to a more standard system/user message structure.
        {
            "role": "system",
            "content": (
                "You are an advanced reasoning LLM that specializes in "
                "evaluating research results and refining search strategies."
            ),
        },
        {"role": "user", "content": user_content},
    ]

    llm_helper_messages = Messages(messages=[Message(role=m["role"], content=m["content"]) for m in messages_list_dict])

    # This function directly calls call_ollama_async, not call_llm_async.
    # This means it won't switch to OpenRouter if USE_OLLAMA is false.
    # This is inconsistent with the helper function call_llm_async.
    # For now, keeping the direct call as per original logic of this specific function.
    # call_ollama_async now expects Messages.
    try:
        response_parts = [
            part
            async for part in call_ollama_async(llm_helper_messages, model=app_config.reason_model, ctx=app_config.reason_model_ctx)
        ]
        response_content = "".join(response_parts) if response_parts else None

        if response_content:
            cleaned_response = re.sub(r"<think>.*?</think>", "", response_content, flags=re.DOTALL).strip()
        return cleaned_response
    except Exception as e:
        logger.exception("Error processing response in judge_search_result_and_refine_plan_async", error=str(e))
        return None


__all__ = [
    "make_initial_searching_plan_async",
    "judge_search_result_and_future_plan_async",  # This is the first one
    "generate_writing_plan_async",
    "generate_search_queries_async",
    "perform_search_async",
    "is_page_useful_async",
    "extract_relevant_context_async",
    "get_new_search_queries_async",
    "generate_final_report_async",
    "process_link",
    "judge_search_result_and_refine_plan_async",  # This is the second one (renamed in original context)
]
