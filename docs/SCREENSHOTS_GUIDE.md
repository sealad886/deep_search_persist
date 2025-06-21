# Screenshots Guide

This document outlines the screenshots needed for comprehensive documentation of DeepSearch with Persisting History.

## Required Screenshots

### 1. WebUI Interface Screenshots

#### Main Research Interface
- **File**: `docs/images/webui-research-tab.png`
- **Content**: Research tab showing:
  - System message input
  - Query input field
  - Model selection dropdowns
  - Max iterations and search items controls
  - Session ID input for resuming
  - Submit button and progress indicators

#### Session Management Interface  
- **File**: `docs/images/webui-session-management.png`
- **Content**: Session Management tab showing:
  - Session list/dropdown
  - Session details display
  - Resume session functionality
  - Delete session options
  - Session status indicators

#### System Status Monitoring
- **File**: `docs/images/webui-system-status.png`
- **Content**: System Status tab showing:
  - Docker container status indicators (✅/❌/⚠️)
  - Ollama server connectivity status
  - Available models list
  - Terminal launch button
  - Real-time status updates

#### Research in Progress
- **File**: `docs/images/webui-research-progress.png`
- **Content**: Active research session showing:
  - Streaming response in Agent Thinking area
  - Session ID display
  - Progress indicators
  - Real-time updates

### 2. Docker Deployment Screenshots

#### Docker Services Running
- **File**: `docs/images/docker-services-running.png`
- **Content**: Terminal showing:
  - `docker compose ps` output
  - All services healthy
  - Port mappings visible
  - Status indicators

#### Docker Logs
- **File**: `docs/images/docker-logs-sample.png`
- **Content**: Terminal showing:
  - `docker compose logs` output
  - Startup messages
  - Service initialization
  - Health check confirmations

### 3. API Interface Screenshots

#### API Health Check
- **File**: `docs/images/api-health-response.png`
- **Content**: Browser or curl showing:
  - `http://localhost:8000/health` response
  - JSON status output
  - Response headers

#### Sessions API
- **File**: `docs/images/api-sessions-list.png`
- **Content**: Browser showing:
  - `http://localhost:8000/sessions` response
  - Session list JSON
  - Session metadata

### 4. Configuration Screenshots

#### research.toml Configuration
- **File**: `docs/images/config-research-toml.png`
- **Content**: Text editor showing:
  - Key configuration sections
  - Docker-specific settings
  - Ollama configuration
  - API endpoints setup

#### Environment Setup
- **File**: `docs/images/config-env-setup.png`
- **Content**: Terminal showing:
  - Ollama server running
  - Model pull commands
  - Environment validation

### 5. Testing Screenshots

#### Test Suite Execution
- **File**: `docs/images/test-suite-running.png`
- **Content**: Terminal showing:
  - `python run_tests.py` output
  - Test categories execution
  - Pass/fail indicators
  - Summary results

#### Docker Validation
- **File**: `docs/images/test-docker-validation.png`
- **Content**: Terminal showing:
  - `python run_tests.py --docker` output
  - Docker connectivity tests
  - Service validation results

## Screenshot Specifications

### Technical Requirements
- **Format**: PNG (preferred) or JPEG
- **Resolution**: Minimum 1200px width
- **Quality**: High DPI/retina displays preferred
- **Compression**: Optimized for web (< 500KB per image)

### Content Guidelines
- **Clean UI**: Remove personal information, sensitive data
- **Good Lighting**: High contrast, readable text
- **Relevant Content**: Show meaningful data, not empty states
- **Professional**: Consistent browser/terminal themes

### File Organization
```
docs/
├── images/
│   ├── webui-research-tab.png
│   ├── webui-session-management.png
│   ├── webui-system-status.png
│   ├── webui-research-progress.png
│   ├── docker-services-running.png
│   ├── docker-logs-sample.png
│   ├── api-health-response.png
│   ├── api-sessions-list.png
│   ├── config-research-toml.png
│   ├── config-env-setup.png
│   ├── test-suite-running.png
│   └── test-docker-validation.png
└── SCREENSHOTS_GUIDE.md (this file)
```

## Integration into Documentation

### README.md Updates
Add screenshot references in relevant sections:

```markdown
### Web UI Features

![Research Interface](docs/images/webui-research-tab.png)

The Gradio interface includes three main tabs:

1. **Research Tab**: Core research functionality with streaming responses
   ![Session Management](docs/images/webui-session-management.png)

2. **Session Management Tab**: View, manage, and delete saved research sessions
   ![System Status](docs/images/webui-system-status.png)

3. **System Status Tab**: Monitor Docker containers and Ollama server status
```

### Docker Deployment Guide Updates
```markdown
## Quick Start

![Docker Services](docs/images/docker-services-running.png)

Once services are running, access the Web UI:

![WebUI Interface](docs/images/webui-research-tab.png)
```

## Creating Screenshots

### Prerequisites
1. **Running Docker Environment**:
   ```bash
   cd docker
   docker compose -f docker-compose.persist.yml up --build
   ```

2. **Ollama with Models**:
   ```bash
   ollama serve
   ollama pull qwen3:14b
   ollama pull phi4-reasoning
   ```

3. **Sample Research Session**:
   - Create a test research query
   - Let it run to show progress
   - Demonstrate session management

### Capture Process
1. **Start all services**
2. **Navigate to each interface**
3. **Capture screenshots using consistent settings**
4. **Edit/crop for clarity**
5. **Optimize file sizes**
6. **Test in documentation context**

## Maintenance

### When to Update Screenshots
- **Major UI changes**
- **New features added**
- **Docker configuration changes**
- **API endpoint modifications**

### Review Process
- **Verify all links work**
- **Check image loading**
- **Validate content accuracy**
- **Test on different screen sizes**

## Current Status

❌ **Screenshots needed** - No screenshots currently available
✅ **Guide created** - This documentation provides framework
⚠️ **Integration pending** - Screenshots need to be captured and integrated

## Next Steps

1. **Capture all required screenshots**
2. **Create docs/images/ directory**
3. **Optimize images for web**
4. **Update README.md with screenshot references**
5. **Update DOCKER_DEPLOYMENT.md with visual guides**
6. **Test documentation with screenshots integrated**