# WebUI Consolidation and Persistence Fixes

## Summary of Changes

This document describes the changes made to consolidate the duplicate WebUI directories and fix the persistent storage APIs for historical research session management.

## Issues Resolved

### 1. Duplicate WebUI Directories
**Problem**: There were two WebUI directories:
- `deep_search_persist/simple_webui/` (full implementation)
- `deep_search_persist/deep_search_persist/simple_webui/` (placeholder only)

**Solution**: 
- Consolidated all WebUI code into `deep_search_persist/simple_webui/`
- Removed the duplicate placeholder directory
- Updated imports in `__init__.py` to avoid circular import issues

### 2. Session Persistence Issues
**Problem**: Historical research sessions weren't saving properly and the session list was showing empty user queries.

**Root Cause**: The persistence layer's `SessionSummary` model didn't include the `user_query` field, and the API was setting it to an empty string.

**Solution**:
1. **Updated Persistence Layer**: Added `user_query` field to `SessionSummary` model in `session_persistence.py:52`
2. **Enhanced Database Projection**: Modified the MongoDB projection to include `"data.user_query": 1` in `session_persistence.py:397`
3. **Fixed Summary Creation**: Updated the session summary creation logic to extract `user_query` from the nested data field
4. **Updated API Mapping**: Changed the API endpoint to use the actual `user_query` from persistence instead of an empty string

### 3. Enhanced WebUI Session Management
**New Features Added**:
1. **Session ID Display**: Research function now parses and displays session IDs from the API
2. **Session Resume**: Added session ID input field to resume previous research sessions
3. **Resume Button**: Added "Resume Session" button in Session Management tab to copy session IDs
4. **Session Tracking**: Research progress now shows the session ID for tracking

## Technical Details

### File Changes

#### `persistence/session_persistence.py`
```python
# Added user_query field to SessionSummary
class SessionSummary(BaseModel):
    session_id: str
    user_query: Optional[str] = None  # NEW FIELD
    user_id: Optional[str] = None
    # ... other fields

# Updated database projection
projection = {
    "_id": 1,
    "data.user_query": 1,  # NEW: Include user_query from nested data
    "user_id": 1,
    # ... other fields
}

# Enhanced summary creation
user_query = None
if "data" in doc and isinstance(doc["data"], dict):
    user_query = doc["data"].get("user_query")
```

#### `api_endpoints.py`
```python
# Fixed API mapping to use actual user_query
api_summary = SessionSummary(
    session_id=s.session_id,
    user_query=s.user_query or "",  # Use actual user_query from persistence
    status=s.status.value,
    # ... other fields
)
```

#### `simple_webui/gradio_online_mode.py`
```python
# Enhanced research function with session support
def research(system_message, query, max_iterations, base_url, session_id=None):
    # ... existing code
    
    # Add session_id if provided (for resuming sessions)
    if session_id:
        data["session_id"] = session_id
    
    # Handle SESSION_ID messages from API
    if line_str.startswith("SESSION_ID:"):
        current_session_id = line_str.split("SESSION_ID:")[1].strip()
        agent_thinking.append(f"📎 Session ID: {current_session_id}")
        yield "\n".join(agent_thinking), final_report
        continue

# Added session management UI components
session_id_input = gr.Textbox(
    label="Session ID (Optional)",
    placeholder="Enter session ID to resume previous research...",
    elem_classes="session-input"
)

resume_session_btn = gr.Button(
    "▶️ Resume Session", 
    variant="primary",
    elem_classes="resume-button"
)

# Added resume functionality
def resume_session(dropdown_value):
    """Extracts session ID from dropdown selection for resuming."""
    session_id = _extract_session_id(dropdown_value)
    if not session_id:
        gr.Warning("Please select a session first")
        return ""
    
    gr.Info(f"Session ID {session_id} copied to Research tab")
    return session_id
```

## User Interface Improvements

### Research Tab Enhancements
1. **Session Options Section**: New section with session ID input field
2. **Session ID Display**: Research progress now shows the session ID for reference
3. **Resume Capability**: Users can enter a session ID to continue previous research

### Session Management Tab Enhancements
1. **Resume Button**: New "▶️ Resume Session" button copies session ID to Research tab
2. **Improved Session List**: Sessions now display meaningful user queries instead of empty strings
3. **Better Status Tracking**: Enhanced status messages and error handling

## Testing Verification

The following functionality has been verified:

### ✅ Completed
1. **WebUI Consolidation**: Duplicate directories removed, single source of truth established
2. **Import Resolution**: Circular import issues fixed
3. **API Endpoint Structure**: Session endpoints properly structured with user_query field
4. **UI Components**: New session management controls added and functional
5. **Code Integration**: All components properly integrated

### 🔄 Requires Full Stack Testing
1. **End-to-End Session Persistence**: Requires MongoDB and full API stack
2. **Session Resume Functionality**: Requires active API server with persistence
3. **Real Research Workflow**: Requires external services (SearXNG, LLM providers)

## Usage Instructions

### Starting a New Research Session
1. Navigate to the Research tab
2. Enter your research query
3. Click "🚀 Start Research"
4. Note the session ID displayed in the thinking output
5. Research will be automatically saved with the session ID

### Resuming a Previous Research Session
1. Navigate to the Session Management tab
2. Click "🔄 Refresh Sessions" to load saved sessions
3. Select a session from the dropdown
4. Click "▶️ Resume Session" to copy the session ID
5. Navigate to the Research tab
6. The session ID will be pre-filled
7. Enter a new query or modify the existing research
8. Click "🚀 Start Research" to continue

### Managing Sessions
1. **View Details**: Select a session and click "👁️ View Details"
2. **Delete Session**: Select a session and click "🗑️ Delete Session"
3. **Resume Session**: Select a session and click "▶️ Resume Session"

## Architecture Benefits

1. **Single Source of Truth**: All WebUI code in one location
2. **Proper Persistence**: Sessions now properly save and load user queries
3. **Enhanced UX**: Users can track and resume research sessions
4. **Better Error Handling**: Improved status messages and validation
5. **Maintainable Code**: Cleaner imports and better organization

## Future Enhancements

1. **Session Metadata**: Add more session metadata (tags, categories, etc.)
2. **Search and Filter**: Add search/filter capabilities to session list
3. **Export Functionality**: Add ability to export session reports
4. **Session Sharing**: Add ability to share sessions between users
5. **Auto-Resume**: Remember last session and offer to resume on startup