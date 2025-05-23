# Test Requirements for deep_search_persist Package

## Functional Test Requirements

### Core Research Functionality
1. **Research Pipeline**
   - [ ] Verify streaming vs non-streaming response modes
   - [ ] Test planning loop execution with WITH_PLANNING=true/false
   - [ ] Validate search query generation → search execution → content processing flow
   - [ ] Verify error handling in process_link_wrapper

2. **Session Persistence**
   - [ ] Test MongoDB session storage (create/resume/rollback)
   - [ ] Verify filesystem fallback when MongoDB unavailable
   - [ ] Validate session history tracking

3. **API Endpoints**
   - [ ] Test /v1/chat/completions:
     - Streaming response format
     - Non-streaming response format
     - Session ID handling
   - [ ] Verify error responses for invalid requests

### Operational Modes
1. **Online Mode**
   - [ ] Test external LLM integration
   - [ ] Validate Jina content parsing

2. **Hybrid Mode**
   - [ ] Test Ollama local LLM integration
   - [ ] Verify fallback to online services

3. **Local Mode**
   - [ ] Test Playwright local parsing
   - [ ] Validate pure local LLM operation

## Docker Integration Tests

### Container Build & Runtime
1. **Image Validation**
   - [ ] Verify multi-stage build completes successfully
   - [ ] Check Python package installation in final image
   - [ ] Validate healthcheck scripts

2. **Dependencies**
   - [ ] Test Playwright browser installation
   - [ ] Verify volume mounts (/data/temp_pdf_data, /app/simple-webui/logs/sessions)

### Docker Compose
1. **Service Orchestration**
   - [ ] Test MongoDB initialization
   - [ ] Verify API ↔ MongoDB connectivity
   - [ ] Validate Web UI ↔ API connectivity

2. **GPU Support**
   - [ ] Test CUDA variant (if applicable)
   - [ ] Verify ROCm variant (if applicable)

## Non-Functional Requirements

### Performance
- [ ] Measure response times under load (50+ concurrent requests)
- [ ] Test memory usage during extended research sessions

### Reliability
- [ ] Verify graceful handling of:
  - External service failures
  - Network interruptions
  - Resource constraints

### Security
- [ ] Validate API key handling
- [ ] Test session isolation

## Test Automation Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_research_response_streaming():
    # Test streaming response format
    pass
```

### Integration Tests
```python
def test_api_session_resumption():
    # Start session → resume with session_id
    pass
```

### E2E Tests
```bash
# Sample test script
docker-compose -f docker-compose.persist.yml up --build -d
curl -X POST http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d '{"model":"deep_researcher","messages":[{"role":"user","content":"test query"}]}'
```

## Test Environment Requirements

1. **CI Pipeline**
   - Docker-in-Docker support
   - GPU-enabled runners (for GPU tests)
   - MongoDB test container

2. **Monitoring**
   - Test coverage reporting (≥90% target)
   - Performance metrics collection
