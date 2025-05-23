import nest_asyncio  # type: ignore
import uvicorn

from .deep_search_persist.api_endpoints import app  # type: ignore

nest_asyncio.apply()

# Terminal formatting control codes
b = "\033[1m"  # Bold
n0 = "\033[0m"  # Reset


def main():
    """Runs the FastAPI application with uvicorn."""
    FastAPI_HOST = "0.0.0.0"
    FastAPI_PORT = 8000

    print(
        "Set the address shown below to a chat client as an OpenAI "
        "completion endpoint, or launch the Gradio interface "
        "in simple_webui folder."
    )
    print(f"Service will be running on:   " f"\033[1mhttp://{FastAPI_HOST}\033[0m:\033[1m{FastAPI_PORT}/v1\033[0m")

    uvicorn.run(app, host=FastAPI_HOST, port=FastAPI_PORT)


if __name__ == "__main__":
    main()


__all__ = [
    "main",
]
