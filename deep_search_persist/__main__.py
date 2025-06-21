import nest_asyncio  # type: ignore
import uvicorn
from loguru import logger

from .deep_search_persist.api_endpoints import app  # type: ignore

nest_asyncio.apply()


def main():
    """Runs the FastAPI application with uvicorn."""
    FastAPI_HOST = "0.0.0.0"
    FastAPI_PORT = 8000

    logger.info(
        ("Service is running. Set the address below as an OpenAI completion endpoint, "
         "or launch the Gradio interface in simple_webui folder.")
    )
    logger.info(f"Service URL: http://{FastAPI_HOST}:{FastAPI_PORT}/v1")

    uvicorn.run(app, host=FastAPI_HOST, port=FastAPI_PORT)


if __name__ == "__main__":
    main()


__all__ = [
    "main",
]
