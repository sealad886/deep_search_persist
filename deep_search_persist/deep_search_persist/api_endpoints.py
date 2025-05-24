import asyncio  # Added for async operations
import copy
import datetime
import json  # Added for SSE
import os
import re  # Added for stripping think tags for logic
import time
from typing import AsyncGenerator, List, Optional  # Modified for event_generator and Optional

import aiohttp  # Added for async HTTP requests in helpers
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse  # Added StreamingResponse
from fastapi.responses import StreamingResponse
from loguru import logger

from .api_models import ModelList  # Message removed as unused
from .api_models import ChatCompletionRequest, ModelObject, SessionSummary, SessionSummaryList
from .helper_classes import Message, Messages  # Added
from .helper_functions import (
    generate_final_report_async,
    generate_search_queries_async,
    judge_search_result_and_future_plan_async,
    make_initial_searching_plan_async,
    perform_search_async,
    process_link,
)
from .logging.logging_config import LogContext
from .persistence.session_persistence import SessionPersistenceManager
from .research_session import ResearchSession

app = FastAPI(
    title="Deep Researcher API with Persistence",
    summary="Use AI to refine an iterative search on a topic of your choice, then generate a detailed report.",
    version="0.1.0",
    docs="/docs",
    redoc_url="/redoc",
    terms_of_service="",
    contact={"email": "dev@andrewcox.doctor"},
    license="GPL-3.0-or-later",
    license_url="https://www.gnu.org/licenses/gpl-3.0.en.html",
)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/deep_search")
persistence = SessionPersistenceManager(MONGO_URI)


@app.get("/")
@app.get("/health", name="health")
@app.get("/healthcheck", name="healthcheck")
async def health_check():
    logger.debug("Healthcheck endpoint called")
    jsonresponse = JSONResponse(content={"status": "ok"}, status_code=200)
    logger.debug("Healtcheck endpoint responded")
    return jsonresponse


# --- Transformer to handle both OpenAI-style (list) and server Messages ---
def transform_chat_completion_request(raw_body: dict) -> ChatCompletionRequest:
    body = copy.deepcopy(raw_body)
    messages = body.get("messages")
    # If messages is a list of dicts, convert to Messages
    if isinstance(messages, list):
        body["messages"] = Messages(messages=[Message(**m) for m in messages])
    elif isinstance(messages, dict):
        # Single message dict, wrap in Messages
        body["messages"] = Messages(messages=[Message(**messages)])
    elif isinstance(messages, Messages):
        pass  # Already correct
    else:
        raise ValueError("Invalid 'messages' format in request body.")
    return ChatCompletionRequest(**body)


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    Handles chat completion requests by initiating a research session and streaming results.
    Implements server-sent events (SSE) for real-time updates to the client.
    """
    raw_body = await request.json()
    try:
        parsed_request = transform_chat_completion_request(raw_body)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=422)

    # Use parsed_request directly

    async def event_generator() -> AsyncGenerator[str, None]:
        research_state: Optional[ResearchSession] = None
        # session_filepath: Optional[Path] = None  # No longer needed

        def create_sse_event_data(content_data: dict) -> str:
            """Helper to format data for SSE."""
            return f"data: {json.dumps(content_data)}\n\n"

        def create_sse_content_chunk(content: str) -> str:
            """Creates an SSE data chunk for a content string."""
            return create_sse_event_data({"choices": [{"delta": {"content": content}}]})

        def process_link_feed_chunk_creator(status_msg: str) -> str:
            """
            Callback for process_link to create SSE chunks for its status messages.
            Ensures that <think> tags in status_msg are passed through.
            """
            return create_sse_content_chunk(status_msg)

        try:
            # Create Messages
            helper_messages_list: List[Message] = []
            if parsed_request.system_instruction:
                helper_messages_list.append(Message(role="system", content=parsed_request.system_instruction))

            raw_user_query_content = ""  # For ResearchSession.user_query attribute

            if parsed_request.messages:
                for i, api_msg in enumerate(parsed_request.messages.get_messages()):
                    # Assuming the first message's content is the primary query for ResearchSession
                    if i == 0 and api_msg.content:
                        raw_user_query_content = api_msg.content
                    helper_messages_list.append(Message(role=api_msg.role, content=api_msg.content))

            # If parsed_request.messages was empty or first message had no content
            if not raw_user_query_content:
                user_messages_in_helper = [m for m in helper_messages_list if m.role == "user"]
                if user_messages_in_helper:
                    # Take first user message as query
                    raw_user_query_content = user_messages_in_helper[0].content
                else:
                    yield create_sse_content_chunk("Error: User query is missing or empty.")
                    yield "data: [DONE]\n\n"
                    return

            messages = Messages(messages=helper_messages_list)

            research_state = ResearchSession(
                user_query=raw_user_query_content,  # This will be the main topic for the session
                # Stored for potential reference, though Messages has it
                system_instruction=parsed_request.system_instruction,
                settings=parsed_request.dict(),
            )
            research_state.status = "running"
            research_state.start_time = datetime.datetime.now().isoformat()
            research_state.aggregated_data = {
                "all_search_queries": [],
                "aggregated_contexts": [],
                "last_plan": research_state.settings.get("initial_plan", ""),  # Store initial plan if provided
                "final_report_content": "",
                "current_iteration_data": {},  # For any per-iteration specific logs/data
            }
            # --- Persist the session to MongoDB ---
            await persistence.save_session(research_state, 0)

            yield f"data: SESSION_ID:{research_state.session_id}\n\n"

            async with aiohttp.ClientSession() as http_session:
                current_plan_for_logic = research_state.aggregated_data["last_plan"]

                if not current_plan_for_logic:
                    yield create_sse_content_chunk("<think>Generating initial research plan...</think>")
                    initial_plan_raw = await make_initial_searching_plan_async(http_session, messages)
                    if not initial_plan_raw:
                        error_msg = "Error: Failed to generate initial research plan."
                        yield create_sse_content_chunk(error_msg)
                        raise Exception(error_msg)

                    # Stream raw plan with potential <think> tags
                    yield create_sse_content_chunk(initial_plan_raw)
                    research_state.aggregated_data["last_plan"] = initial_plan_raw
                    await persistence.save_session(research_state, 0)
                    current_plan_for_logic = re.sub(
                        r"<think>.*?</think>", "", initial_plan_raw, flags=re.DOTALL
                    ).strip()

                max_iterations = research_state.settings.get("max_iterations", 3)

                for iteration in range(max_iterations):
                    iteration_label = f"Iteration {iteration + 1}/{max_iterations}"
                    yield create_sse_content_chunk(
                        f"<think>{iteration_label}. Current plan:\n{current_plan_for_logic}</think>"
                    )
                    research_state.aggregated_data["current_iteration_data"] = {
                        "number": iteration + 1,
                        "status": "starting plan",
                    }
                    await persistence.save_session(research_state, iteration)

                    yield create_sse_content_chunk(f"<think>{iteration_label}: Generating search queries...</think>")
                    search_queries = await generate_search_queries_async(http_session, current_plan_for_logic)

                    if not search_queries or search_queries == "<done>":
                        yield create_sse_content_chunk(
                            f"<think>{iteration_label}: No new search queries generated or <done> "
                            f"received. Moving to judge/report phase.</think>"
                        )
                        break

                    queries_display_str = json.dumps(search_queries)
                    yield create_sse_content_chunk(
                        f"<think>{iteration_label}: Generated search queries: {queries_display_str}</think>\n"
                        f"Generated search queries: {queries_display_str}"
                    )
                    research_state.aggregated_data["all_search_queries"].extend(search_queries)
                    research_state.aggregated_data["current_iteration_data"]["search_queries"] = search_queries
                    await persistence.save_session(research_state, iteration)

                    for sq_idx, query in enumerate(search_queries):
                        query_label = f"Query {sq_idx + 1}/{len(search_queries)} ('{query}')"
                        yield create_sse_content_chunk(
                            f"<think>{iteration_label}: Performing search for {query_label}...</think>"
                        )
                        research_state.aggregated_data["current_iteration_data"]["current_query"] = query
                        await persistence.save_session(research_state, iteration)

                        links = await perform_search_async(http_session, query)
                        if not links:
                            yield create_sse_content_chunk(f"No links found for {query_label}.")
                            continue

                        links_display_str = json.dumps(links)
                        yield create_sse_content_chunk(
                            f"<think>{iteration_label}: Found {len(links)} links for {query_label}. "
                            f"Processing them...</think>\nFound {len(links)} links for '{query}': {links_display_str}"
                        )
                        research_state.aggregated_data["current_iteration_data"]["found_links"] = links
                        await persistence.save_session(research_state, iteration)

                        for link_idx, link_url in enumerate(links):
                            link_label = f"Link {link_idx + 1}/{len(links)} ({link_url})"
                            yield create_sse_content_chunk(
                                f"<think>{iteration_label}: Processing {link_label} for {query_label}...</think>"
                            )
                            research_state.aggregated_data["current_iteration_data"]["processing_link"] = link_url
                            await persistence.save_session(research_state, iteration)

                            # Process the link and yield results
                            async for item_from_pl in process_link(
                                http_session,
                                link_url,
                                messages,
                                query,
                                create_chunk=process_link_feed_chunk_creator,
                            ):
                                if item_from_pl.startswith("data:"):  # SSE string from process_link_feed_chunk_creator
                                    yield item_from_pl
                                else:  # Raw context string "url:...\ncontext:..."
                                    actual_context = item_from_pl  # May contain <think> tags
                                    yield create_sse_content_chunk(actual_context)  # Stream raw context
                                    research_state.aggregated_data["aggregated_contexts"].append(actual_context)
                                    await persistence.save_session(research_state, iteration)
                            await asyncio.sleep(0.05)  # Small delay for stream flushing

                    yield create_sse_content_chunk(
                        f"<think>{iteration_label}: Judging search results and planning next steps...</think>"
                    )
                    research_state.aggregated_data["current_iteration_data"]["status"] = "judging results"
                    await persistence.save_session(research_state, iteration)

                    combined_contexts_for_judgement = "\n".join(research_state.aggregated_data["aggregated_contexts"])
                    next_plan_raw = await judge_search_result_and_future_plan_async(  # Corrected typo
                        http_session,
                        messages,
                        current_plan_for_logic,
                        combined_contexts_for_judgement,
                    )

                    if not next_plan_raw:  # Should not happen if LLM is up, but handle defensively
                        yield create_sse_content_chunk(
                            f"<think>{iteration_label}: Failed to get next plan. Ending research.</think>"
                        )
                        break

                    yield create_sse_content_chunk(next_plan_raw)  # Stream raw plan

                    current_plan_for_logic = re.sub(r"<think>.*?</think>", "", next_plan_raw, flags=re.DOTALL).strip()
                    research_state.aggregated_data["last_plan"] = next_plan_raw  # Store raw plan
                    research_state.aggregated_data["current_iteration_data"]["next_plan"] = next_plan_raw
                    await persistence.save_session(research_state, iteration)

                    if current_plan_for_logic == "<done>":
                        yield create_sse_content_chunk(
                            f"<think>{iteration_label}: Next plan is <done>. Concluding research phase.</think>"
                        )
                        break

                yield create_sse_content_chunk("<think>Research phase concluded. Generating final report...</think>")
                research_state.aggregated_data["current_iteration_data"] = {"status": "generating report"}
                await persistence.save_session(research_state, max_iterations)

                # Optional: Generate a specific writing plan first
                # writing_plan_raw = await generate_writing_plan_aync(
                #     http_session, user_query,
                #     "\n".join(research_state.aggregated_data['aggregated_contexts'])
                # )
                # if writing_plan_raw:
                #     yield create_sse_content_chunk(writing_plan_raw)
                #     research_state.aggregated_data['writing_plan'] = writing_plan_raw
                #     await persistence.save_session(research_state, max_iterations)
                # Or current iteration if this step is within loop
                # else:
                #     yield create_sse_content_chunk(
                #         "<think>Could not generate a separate writing plan. "
                #         "Proceeding with direct report generation.</think>"
                #     )

                # Using last_plan as the basis for report generation if no specific writing plan step
                plan_for_report = research_state.aggregated_data.get(
                    "writing_plan", research_state.aggregated_data["last_plan"]
                )
                final_report_raw = await generate_final_report_async(
                    http_session,
                    messages,  # system_instruction is part of this
                    plan_for_report,  # Pass the relevant plan
                    research_state.aggregated_data["aggregated_contexts"],
                )

                if final_report_raw:
                    yield create_sse_content_chunk(final_report_raw)  # Stream raw report
                    research_state.aggregated_data["final_report_content"] = final_report_raw
                else:
                    error_msg = "Error: Failed to generate final report."
                    yield create_sse_content_chunk(error_msg)
                    research_state.aggregated_data["final_report_content"] = error_msg

                research_state.status = "completed"
                research_state.end_time = datetime.datetime.now().isoformat()
                await persistence.save_session(research_state, max_iterations)
                yield create_sse_content_chunk("Research session completed.")

        except Exception as e:
            error_detail = f"An error occurred: {str(e)}"
            current_time_iso = datetime.datetime.now().isoformat()
            # Log to server console
            import traceback

            logger.exception(
                "Error during stream generation",
                time=current_time_iso,
                error=error_detail,
                traceback=traceback.format_exc(),
            )

            if research_state:
                research_state.status = "error"
                if not research_state.end_time:
                    research_state.end_time = current_time_iso
                research_state.error_message = error_detail
                try:
                    await persistence.save_session(research_state, -1)
                except Exception as save_exc:
                    logger.exception(
                        "Failed to save error state for session",
                        session_id=getattr(research_state, "session_id", "UNKNOWN"),
                        error=str(save_exc),
                    )

            yield create_sse_content_chunk(f"<think>Error encountered: {error_detail}</think>\n{error_detail}")
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/models")
@app.get("/v1/models")
async def list_models():
    """List the available models"""
    return ModelList(
        data=[
            ModelObject(
                id="deep_researcher",
                created=int(time.time()),
                owned_by="deep_researcher",
            )
        ]
    )


##
# Session Management Endpoints
##
@app.get("/sessions", response_model=SessionSummaryList)
async def list_sessions() -> SessionSummaryList:
    """Lists all saved sessions and their summaries from MongoDB."""
    persistence_summaries = await persistence.list_sessions()
    api_summaries = []
    earliest_time = None
    for s in persistence_summaries:
        # Map persistence SessionSummary to api_models.SessionSummary
        api_summary = SessionSummary(
            session_id=s.session_id,
            user_query="",  # user_query is not available in persistence summary
            status=s.status.value,  # Convert Enum to string
            start_time=(s.created_at if s.created_at is not None else datetime.datetime.now()),
            end_time=(s.updated_at if s.updated_at is not None else None),  # end_time is Optional in API model
        )
        api_summaries.append(api_summary)

        # Find the earliest time for the SessionSummaryList start_time
        if s.created_at:
            if earliest_time is None or s.created_at < earliest_time:
                earliest_time = s.created_at

    # The SessionSummaryList model expects a string for start_time
    return SessionSummaryList(
        sessions=api_summaries,
        start_time=earliest_time.isoformat() if earliest_time else "",
    )


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Loads and returns the full data for a specific session from MongoDB."""
    with LogContext("api.get_session", session_id=session_id):
        try:
            session_data = await persistence.load_session(session_id)
            return session_data
        except Exception as e:
            logger.exception("Could not load session data", session_id=session_id, error=str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")


@app.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    """Deletes the session from MongoDB."""
    with LogContext("api.delete_session", session_id=session_id):
        try:
            await persistence.delete_session(session_id)
        except Exception as e:
            logger.exception("Error deleting session", session_id=session_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not delete session: {str(e)}",  # Use str(e) for detail
            )
    return None  # For 204, FastAPI expects no body, so returning None is appropriate


@app.post("/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    """Resumes a partially completed session from MongoDB."""
    with LogContext("api.resume_session", session_id=session_id):
        try:
            session_data = await persistence.resume_session(session_id)
            return session_data
        except Exception as e:
            logger.exception("Could not resume session", session_id=session_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or cannot be resumed",
            )


@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Returns the iteration history for a session."""
    with LogContext("api.get_session_history", session_id=session_id):
        try:
            history = await persistence.get_iteration_history(session_id)
            return {"history": history}
        except Exception as e:
            logger.exception("Could not get session history", session_id=session_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or no history available",
            )


@app.post("/sessions/{session_id}/rollback/{iteration}")
async def rollback_session(session_id: str, iteration: int):
    """Rolls back the session to a previous iteration."""
    with LogContext("api.rollback_session", session_id=session_id, iteration=iteration):
        try:
            await persistence.rollback_to_iteration(session_id, iteration)
            return {"status": "rolled back", "iteration": iteration}
        except Exception as e:
            logger.exception(
                "Could not rollback session",
                session_id=session_id,
                iteration=iteration,
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not rollback: {str(e)}",  # Use str(e)
            )


__all__: List[str] = [
    "app",
    "health_check",
    "chat_completions",
    "list_models",
    "list_sessions",
    "get_session",
    "delete_session",
    "resume_session",
    "get_session_history",
    "rollback_session",
]
