# Task: Fix Pyright Error in `session_persistence.py`

## Task ID: fix-pyright-error-002

## Description
Address the `windsurfPyright` error "Expected type arguments for generic class "AsyncIOMotorDatabase"" in `deep_search_persist/deep_search_persist/persistence/session_persistence.py` at line 143.

## Detected Problems
- `[windsurfPyright] Expected type arguments for generic class "AsyncIOMotorDatabase"`

## File to be modified
`deep_search_persist/deep_search_persist/persistence/session_persistence.py`

## Line of error
143

## Current Code Snippet
```python
AsyncIOMotorDatabase
```

## Acceptance Criteria
- The `AsyncIOMotorDatabase` type hint is correctly parameterized.
- No new Pyright errors are introduced.
- The corrected code is provided.
- An explanation of the fix is provided.

## Dependencies
None

## Estimated Complexity
Low
