import asyncio
import time
from typing import Any, AsyncGenerator, Callable, List, Literal, Optional, Union, overload

import aiohttp
import anyio
from loguru import logger

from .configuration import app_config
from .api_models import ChatCompletionChunk
from .helper_classes import Message, Messages
from .helper_functions import (
    generate_final_report_async,
    generate_search_queries_async,
    generate_writing_plan_async,
    get_new_search_queries_async,
    judge_search_result_and_refine_plan_async,
    make_initial_searching_plan_async,
    perform_search_async,
    process_link,
    extract_relevant_context_async,  # Added
    is_page_useful_async,  # Added
)


# Helper function to create chunks for streaming
def create_chunk(content: str) -> str:
    chunk = ChatCompletionChunk(
        id=f"chatcmpl-{int(time.time()*1000)}",
        created=int(time.time()),
        model="deep_researcher",
        choices=[{"index": 0, "delta": {"content": content}, "finish_reason": None}],
    )
    return f"data: {chunk.model_dump_json()}\n\n"


# Helper function to convert an async generator to a regular awaitable that returns a list
async def process_link_wrapper(
    session: aiohttp.ClientSession,
    link: str,
    messages: Messages,
    search_query: str,
    create_chunk: Optional[Callable[[str], Any]],
) -> List[str]:
    """Wrapper for process_link that collects all chunks from the async generator into a list."""
    result = []
    try:
        async for chunk in process_link(session, link, messages, search_query, create_chunk):
            result.append(chunk)
    except Exception as e:
        logger.exception("Error in process_link_wrapper", link=link, error=str(e))
        result.clear()  # TODO: Consider returning the partial result if available
    finally:
        return result


async def generate_research_response_streaming(
    system_instruction: str,
    user_query: str,
    max_iterations: int = 10,
    max_search_items: int = 4,
) -> AsyncGenerator[str, None]:
    """
    Streaming version of the research response function that yields chunks.
    """
    # Implementation for streaming mode
    iteration_limit = max_iterations
    aggregated_contexts = []
    all_search_queries = []
    iteration = 0

    logger.info("Starting streaming research response generation", query=user_query)

    messages = Messages([Message(role="user", content=user_query)])
    # Add system instruction to messages if it exists
    if system_instruction:
        messages.add_message(sender="system", content=system_instruction)

    async with aiohttp.ClientSession() as session:
        # Initial research plan
        if app_config.with_planning:
            logger.debug("Generating initial research plan")
            # Use messages object here
            research_plan = await make_initial_searching_plan_async(session, messages)
            # Handle potential list return from make_initial_searching_plan_async
            if isinstance(research_plan, list):
                research_plan = ""

            initial_query_content = f"User Query:{user_query}"
            if research_plan and not research_plan.startswith("Error:"):
                initial_query_content += f"\n\nResearch Plan:{research_plan}"

            # If streaming, yield initial plan
            if research_plan:
                yield create_chunk(f"Initial Research Plan:\n{research_plan}\n\n")

        else:
            research_plan = None
            initial_query_content = f"User Query:{user_query}"

        # Generate initial search queries
        logger.debug("Generating initial search queries")
        new_search_queries = await generate_search_queries_async(session, initial_query_content)
        if not new_search_queries:
            logger.warning("No search queries could be generated")
            yield create_chunk("No search queries could be generated. Exiting.\n\n")
            yield "data: [DONE]\n\n"
            return

        all_search_queries.extend(new_search_queries)
        logger.debug("Initial search queries generated", queries=new_search_queries)

        while iteration < iteration_limit:
            logger.info(f"Starting research iteration {iteration + 1}/{iteration_limit}")
            yield create_chunk(f"\n=== Iteration {iteration + 1} ===\n\n")

            # Perform searches
            iteration_contexts = []
            search_tasks = [perform_search_async(session, query) for query in new_search_queries]
            full_search_results = await asyncio.gather(*search_tasks)

            # ... (rest of search result processing - same for both modes)
            if not app_config.use_jina:
                search_results = [result[:max_search_items] for result in full_search_results]
                logger.debug("Limiting search results", max_items=max_search_items)
            else:
                search_results = full_search_results

            # Process unique links
            unique_links = {}
            for idx, links in enumerate(search_results):
                current_query_for_link = new_search_queries[idx]
                for link in links:
                    if link not in unique_links:
                        unique_links[link] = current_query_for_link

            logger.debug("Processing unique links", count=len(unique_links))
            yield create_chunk(f"Processing {len(unique_links)} unique links...\n\n")

            # Streaming mode: process links as they complete and yield chunks
            # Create tasks from the async generators to make them awaitable
            tasks = [
                asyncio.create_task(process_link_wrapper(session, link, messages, unique_links[link], create_chunk))
                for link in unique_links
            ]

            for completed_task in asyncio.as_completed(tasks):
                try:
                    result = await completed_task  # This is now a list of chunks from the wrapper
                    for chunk in result:
                        if chunk.startswith("url:"):
                            iteration_contexts.append(chunk)
                        else:
                            yield chunk  # Yield status updates/chunks
                except Exception as e:
                    logger.exception("Error in link processing", error=str(e))

            if iteration_contexts:
                aggregated_contexts.extend(iteration_contexts)
                logger.debug(
                    "Added contexts to aggregation",
                    new_count=len(iteration_contexts),
                    total_count=len(aggregated_contexts),
                )
            else:
                logger.warning("No useful contexts found in this iteration")
                yield create_chunk("No useful contexts found in this iteration.\n\n")

            # Check if we should continue
            if iteration + 1 < iteration_limit:
                if app_config.with_planning:
                    # Use messages object here
                    new_research_plan = await judge_search_result_and_refine_plan_async(
                        session,
                        messages,
                        str(research_plan),
                        "\n".join(aggregated_contexts),
                    )
                    if new_research_plan:
                        logger.info("Research plan updated")
                        yield create_chunk(f"Updated Research Plan:\n{new_research_plan}\n\n")
                else:
                    new_research_plan = None

                # Use messages object here
                next_round_queries = await get_new_search_queries_async(
                    session,
                    messages,
                    new_research_plan,
                    all_search_queries,
                    aggregated_contexts,
                )
                if next_round_queries == "<done>":
                    logger.info("Research complete, moving to final report generation")
                    yield create_chunk("Research complete. Generating final report...\n\n")
                    break
                elif next_round_queries:
                    logger.debug("Generated new search queries", queries=next_round_queries)
                    yield create_chunk(f"New search queries generated: {next_round_queries}\n")
                    all_search_queries.extend(next_round_queries)
                    new_search_queries = next_round_queries
                else:
                    logger.info("No new search queries generated, completing research")
                    yield create_chunk("No new search queries. Completing research...\n\n")
                    break
            else:
                break

            iteration += 1
            # Add delay if needed (same for both modes)
            if app_config.operation_wait_time > 0:
                logger.debug("Adding operation wait time", seconds=app_config.operation_wait_time)
                await anyio.sleep(app_config.operation_wait_time)

        # Generate final report
        yield create_chunk("\n</think>\n\n")  # Close think tag before final report

        logger.info("Generating final report")
        if app_config.with_planning:
            logger.debug("Creating writing plan for final report")
            # Use messages object here
            final_report_planning = await generate_writing_plan_async(session, messages, "\n".join(aggregated_contexts))
            if final_report_planning:
                yield create_chunk(f"Writing Plan:\n{final_report_planning}\n\n")
        else:
            final_report_planning = None

        # Use messages object here
        logger.debug(
            "Generating final report with context",
            context_count=len(aggregated_contexts),
        )
        final_report_str = await generate_final_report_async(
            session,
            messages,  # Pass messages object
            final_report_planning,
            aggregated_contexts,
        )

        if not final_report_str or len(final_report_str) < 200:
            error_message_parts = [
                (final_report_str or ""),
                "\n\nThese are the writing prompt, please copy it and try again with anothor model",
                "\n\n---\n\n---\n\n",
                f"User Query: {user_query}\n\nGathered Relevant Contexts:\n",
                "\n\n".join(aggregated_contexts),
                (f"\n\nWriting plan from a planning agent:\n{final_report_planning}" if final_report_planning else ""),
                (
                    "\n\nYou are an expert researcher and report writer. Based on the gathered "
                    "contexts above and the original query, write a comprehensive, "
                    "well-structured, and detailed report that addresses the query "
                    "thoroughly.\n\n---\n\n---"
                ),
            ]
            final_report_str = "".join(error_message_parts)

        yield create_chunk(final_report_str)
        yield "data: [DONE]\n\n"


async def generate_research_response_non_streaming(
    system_instruction: str,
    user_query: str,
    max_iterations: int = 10,
    max_search_items: int = 4,
) -> str:
    """
    Non-streaming version of the research response function that returns a string.
    """
    # Implementation for non-streaming mode
    iteration_limit = max_iterations
    aggregated_contexts = []
    all_search_queries = []
    iteration = 0

    messages = Messages([Message(role="user", content=user_query)])
    # Add system instruction to messages if it exists
    if system_instruction:
        messages.add_message(sender="system", content=system_instruction)

    async with aiohttp.ClientSession() as session:
        # Initial research plan
        if app_config.with_planning:
            # Use messages object here
            research_plan = await make_initial_searching_plan_async(session, messages)
            # Handle potential list return from make_initial_searching_plan_async
            if isinstance(research_plan, list):
                research_plan = ""

            initial_query_content = f"User Query:{user_query}"
            if research_plan and not research_plan.startswith("Error:"):
                initial_query_content += f"\n\nResearch Plan:{research_plan}"
        else:
            research_plan = None
            initial_query_content = f"User Query:{user_query}"

        # Generate initial search queries
        new_search_queries = await generate_search_queries_async(session, initial_query_content)
        if not new_search_queries:
            return "No search queries could be generated."

        all_search_queries.extend(new_search_queries)

        # Main research loop
        while iteration < iteration_limit:
            # Perform searches
            iteration_contexts = []
            search_tasks = [perform_search_async(session, query) for query in new_search_queries]
            full_search_results = await asyncio.gather(*search_tasks)

            # ... (rest of search result processing - same for both modes)
            if not app_config.use_jina:
                search_results = [result[:max_search_items] for result in full_search_results]
            else:
                search_results = full_search_results

            # Process unique links
            unique_links = {}
            for idx, links in enumerate(search_results):
                current_query_for_link = new_search_queries[idx]
                for link in links:
                    if link not in unique_links:
                        unique_links[link] = current_query_for_link

            logger.info("Processing unique links", count=len(unique_links))

            # Non-streaming mode: collect all results
            # Create tasks from the async generators to make them awaitable
            tasks = [
                asyncio.create_task(process_link_wrapper(session, link, messages, unique_links[link], None))
                for link in unique_links
            ]  # Pass None for create_chunk
            all_results = await asyncio.gather(*tasks, return_exceptions=True)

            for results_list in all_results:
                if isinstance(results_list, list):
                    iteration_contexts.extend(results_list)

            if iteration_contexts:
                aggregated_contexts.extend(iteration_contexts)
            else:
                logger.warning("No useful contexts found in this iteration")

            # Check if we should continue
            if iteration + 1 < iteration_limit:
                if app_config.with_planning:
                    # Use messages object here
                    new_research_plan = await judge_search_result_and_refine_plan_async(
                        session,
                        messages,
                        str(research_plan),
                        "\n".join(aggregated_contexts),
                    )
                else:
                    new_research_plan = None

                # Use messages object here
                next_round_queries = await get_new_search_queries_async(
                    session,
                    messages,
                    new_research_plan,
                    all_search_queries,
                    aggregated_contexts,
                )
                if next_round_queries == "<done>":
                    break
                elif next_round_queries:
                    all_search_queries.extend(next_round_queries)
                    new_search_queries = next_round_queries
                else:
                    break
            else:
                break

            iteration += 1
            # Add delay if needed (same for both modes)
            if app_config.operation_wait_time > 0:
                await anyio.sleep(app_config.operation_wait_time)

        # Generate final report
        if app_config.with_planning:
            # Use messages object here
            final_report_planning = await generate_writing_plan_async(session, messages, "\n".join(aggregated_contexts))
        else:
            final_report_planning = None

        # Use messages object here
        final_report_str = await generate_final_report_async(
            session,
            messages,  # Pass messages object
            final_report_planning,
            aggregated_contexts,
        )

        if not final_report_str or len(final_report_str) < 200:
            error_message_parts = [
                (final_report_str or ""),
                "\n\nThese are the writing prompt, please copy it and try again with anothor model",
                "\n\n---\n\n---\n\n",
                f"User Query: {user_query}\n\nGathered Relevant Contexts:\n",
                "\n\n".join(aggregated_contexts),
                (f"\n\nWriting plan from a planning agent:\n{final_report_planning}" if final_report_planning else ""),
                (
                    "\n\nYou are an expert researcher and report writer. Based on the gathered "
                    "contexts above and the original query, write a comprehensive, "
                    "well-structured, and detailed report that addresses the query "
                    "thoroughly.\n\n---\n\n---"
                ),
            ]
            final_report_str = "".join(error_message_parts)

        return final_report_str


@overload
async def generate_research_response(  # Parameter name changed to system_instruction
    system_instruction: str,
    user_query: str,
    max_iterations: int = 10,
    max_search_items: int = 4,
    stream: Literal[True] = True,
) -> AsyncGenerator[str, None]: ...


@overload
async def generate_research_response(  # Parameter name changed to system_instruction
    system_instruction: str,
    user_query: str,
    max_iterations: int = 10,
    max_search_items: int = 4,
    stream: Literal[False] = False,
) -> str: ...


async def generate_research_response(
    system_instruction: str,
    user_query: str,
    max_iterations: int = 10,
    max_search_items: int = 4,
    stream: bool = False,
) -> Union[AsyncGenerator[str, None], str]:  # Refined Union type
    """
    Performs research based on user query and system instructions,
    with an option to stream results.
    """
    # Dispatch to the appropriate implementation based on stream flag
    if stream:
        return generate_research_response_streaming(system_instruction, user_query, max_iterations, max_search_items)
    else:
        return await generate_research_response_non_streaming(
            system_instruction, user_query, max_iterations, max_search_items
        )


async def async_main(
    system_instruction: str,
    user_query: str,
    max_iterations: int = 10,
    max_search_items: int = 4,
    stream: bool = False,
    default_model: Optional[str] = None,
    reason_model: Optional[str] = None,
) -> Union[str, AsyncGenerator[str, None]]:
    """Main entry point that handles both streaming and non-streaming modes"""
    if stream:

        async def streaming_wrapper() -> AsyncGenerator[str, None]:
            # Save original configuration values
            original_default = app_config.default_model
            original_reason = app_config.reason_model

            # Override configuration with provided parameters
            if default_model:
                app_config.default_model = default_model
            if reason_model:
                app_config.reason_model = reason_model

            try:
                # Get the async generator from generate_research_response
                # Since generate_research_response is async, await its call.
                # With stream=True, it resolves to an AsyncGenerator.
                response_generator = await generate_research_response(
                    system_instruction=system_instruction,
                    user_query=user_query,
                    max_iterations=max_iterations,
                    max_search_items=max_search_items,
                    stream=True,
                )
                async for chunk in response_generator:  # Iterate over the resolved generator
                    yield chunk
            finally:
                # Restore original configuration values after generator completes
                app_config.default_model = original_default
                app_config.reason_model = original_reason

        return streaming_wrapper()
    else:
        # Handle non-streaming mode with try/finally
        original_default = app_config.default_model
        original_reason = app_config.reason_model

        # Override configuration if parameters are provided
        if default_model:
            app_config.default_model = default_model
        if reason_model:
            app_config.reason_model = reason_model

        try:
            # Since generate_research_response is async, await its call.
            # With stream=False, it resolves to a str.
            response: str = await generate_research_response(
                system_instruction,
                user_query,
                max_iterations,
                max_search_items,
                stream=False,
            )
            return response
        finally:
            # Restore original configuration values
            app_config.default_model = original_default
            app_config.reason_model = original_reason


__all__ = [
    "async_main",
    "generate_research_response",
    "extract_relevant_context_async",
    "generate_search_queries_async",
    "generate_writing_plan_async",
    "is_page_useful_async",
    "judge_search_result_and_refine_plan_async",
    "make_initial_searching_plan_async",
    "perform_search_async",
]
