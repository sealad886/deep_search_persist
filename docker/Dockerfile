FROM python:3.12-slim-bookworm AS pybuilder

WORKDIR /src

# Ensure pip, wheel, and setuptools are up-to-date
# These are typically pre-installed in the python:slim-bookworm images
RUN pip install --no-cache-dir -U pip wheel setuptools

# For cache busting pip install layer if source code changes
ARG CACHEBUST=1

# Copy application source and configuration files needed for building the package
COPY pyproject.toml setup.py setup.cfg README.md LICENSE ./
COPY deep_search_persist ./deep_search_persist/
COPY requirements.txt ./
COPY requirements/ ./requirements/

# Install the application and its dependencies into a specified prefix
# --no-build-isolation is used from the original Dockerfile's pip install command
RUN pip install --no-cache-dir --prefix=/python_deps .[webui] --no-build-isolation

FROM python:3.12-slim-bookworm AS runtime

WORKDIR /etc

# Install curl for healthchecks.
# python:3.12-slim-bookworm includes pip.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create local store for temp_pdf_data and other necessary config mount points if needed by the app image itself
RUN mkdir -p /data/temp_pdf_data 

WORKDIR /app

# Upgrade pip and install Playwright
RUN pip install --no-cache-dir -U pip playwright

# Install Playwright browser OS dependencies.
# playwright install-deps chromium itself calls 'apt-get update' and 'apt-get install'.
# We run apt-get clean and remove lists after it.
RUN playwright install-deps chromium && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install the Playwright Chromium browser (downloads browser binaries)
RUN playwright install chromium

# Create necessary directories
RUN mkdir -p /app/temp_pdf_data /app/simple-webui/logs/sessions /app/simple-webui/imgs
COPY ../app_logo.jpg simple-webui/imgs/app_logo.jpg

# Copy Python application and its dependencies from pybuilder stage
COPY --from=pybuilder /python_deps /usr/local/

# PYTHONPATH can be useful if the application expects /app in its path for other resources,
# or if scripts are run from /app. For an installed module, it's not strictly for module discovery.
ENV PYTHONPATH=/app
ENV DOCKER_CONTAINER=1

# Expose the FastAPI port
EXPOSE 8000

# Run the persist module
CMD ["python", "-m", "deep_search_persist"]
