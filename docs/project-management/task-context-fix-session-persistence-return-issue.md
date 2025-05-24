# Task Context: Fix Session Persistence Return Value Issue

## Task ID
fix-session-persistence-return-issue-2025-05-24

## Problem Description
MyPy is reporting a "Return value expected" error in the `session_persistence.py` file at line 88. The issue is in the `__func_datetime` method of the `SessionSummaryList` class.

## Current Issue Analysis
- **File**: `deep_search_persist/deep_search_persist/persistence/session_persistence.py`
- **Method**: `SessionSummaryList.__func_datetime` (lines 80-96)
- **Problem**: MyPy type checking error indicating return value expected
- **Line 88**: Contains `return self.get(internal_param_name)` but MyPy is flagging this

## Method Signature
```python
def __func_datetime(
    self, internal_param_name: Literal["_start_time", "_end_time"], func: Callable
) -> Optional[datetime]:
```

## Current Code Logic Issues
1. The method calls `self.get(internal_param_name)` but `SessionSummaryList` inherits from `BaseModel` and may not have a `get` method
2. The method has complex conditional logic that may not guarantee a return value in all paths
3. Type annotations suggest `Optional[datetime]` return but the logic may not be type-safe

## Requirements
- Fix the MyPy type checking error
- Ensure the method properly returns `Optional[datetime]` in all code paths
- Maintain the existing functionality for datetime calculation
- Follow Python best practices and type safety
- Ensure compatibility with Pydantic BaseModel

## Acceptance Criteria
1. MyPy type checking passes without errors
2. Method returns proper `Optional[datetime]` values
3. Existing functionality is preserved
4. Code follows Python type safety best practices
5. No breaking changes to the public API

## Context Files
- Primary file: `deep_search_persist/deep_search_persist/persistence/session_persistence.py`
- Related: `deep_search_persist/deep_search_persist/persistence/utils.py` (for DatetimeException)

## Priority
High - This is blocking type checking and could indicate runtime issues
