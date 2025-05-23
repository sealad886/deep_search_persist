"""
Tests for the ResearchSession class in the docker/persist service.
"""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from ..deep_search_persist.research_session import ResearchSession


class TestResearchSession:
    """Tests for the ResearchSession class."""

    @pytest.fixture
    def sample_session(self):
        """Create a sample ResearchSession instance for testing."""
        return ResearchSession(
            user_query="What is the capital of France?",
            system_instruction="You are a helpful assistant.",
            settings={"model": "test_model", "max_iterations": 2},
        )

    def test_init(self, sample_session):
        """Test that a ResearchSession is initialized with the correct attributes."""
        assert sample_session.user_query == "What is the capital of France?"
        assert sample_session.system_instruction == "You are a helpful assistant."
        assert sample_session.settings == {"model": "test_model", "max_iterations": 2}
        assert sample_session.status == "running"
        assert sample_session.iterations == []
        assert sample_session.final_report is None
        assert sample_session.error_message is None
        assert isinstance(sample_session.session_id, str)
        assert isinstance(sample_session.start_time, str)
        assert sample_session.end_time is None

        # Check aggregated_data structure
        assert "all_search_queries" in sample_session.aggregated_data
        assert "aggregated_contexts" in sample_session.aggregated_data
        assert "last_plan" in sample_session.aggregated_data
        assert "last_completed_iteration" in sample_session.aggregated_data
        assert sample_session.aggregated_data["last_completed_iteration"] == -1

    def test_to_dict(self, sample_session):
        """Test that to_dict returns the correct dictionary representation."""
        session_dict = sample_session.to_dict()

        assert session_dict["session_id"] == sample_session.session_id
        assert session_dict["start_time"] == sample_session.start_time
        assert session_dict["end_time"] is None
        assert session_dict["status"] == "running"
        assert session_dict["user_query"] == "What is the capital of France?"
        assert session_dict["system_instruction"] == "You are a helpful assistant."
        assert session_dict["settings"] == {"model": "test_model", "max_iterations": 2}
        assert session_dict["iterations"] == []
        assert session_dict["final_report"] is None
        assert session_dict["error_message"] is None
        assert session_dict["aggregated_data"] == sample_session.aggregated_data

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    @patch("pathlib.Path.mkdir")
    def test_save_session(self, mock_mkdir, mock_json_dump, mock_file, sample_session):
        """Test that save_session correctly saves the session to a file."""
        filepath = Path("/test/path/session.json")

        sample_session.save_session(filepath)

        # Check that the directory was created
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Check that the file was opened correctly
        mock_file.assert_called_once_with(filepath, "w")

        # Check that json.dump was called with the correct arguments
        mock_json_dump.assert_called_once()
        args, _ = mock_json_dump.call_args
        assert args[0] == sample_session.to_dict()
        assert args[1] == mock_file()

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"session_id": "test-id", "user_query": "test query", "settings": {}, '
        '"start_time": "2023-01-01T00:00:00", "status": "completed"}',
    )
    @patch("json.load")
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_session_success(self, mock_exists, mock_json_load, mock_file):
        """Test that load_session correctly loads a session from a file."""
        filepath = Path("/test/path/session.json")

        # Mock the JSON data that would be loaded
        mock_data = {
            "session_id": "test-id",
            "user_query": "test query",
            "settings": {"model": "test_model"},
            "start_time": "2023-01-01T00:00:00",
            "end_time": "2023-01-01T01:00:00",
            "status": "completed",
            "system_instruction": "test instruction",
            "iterations": [{"iteration": 1}],
            "aggregated_data": {
                "all_search_queries": ["query1"],
                "aggregated_contexts": ["context1"],
                "last_plan": "plan",
                "last_completed_iteration": 1,
            },
            "final_report": "Final report",
            "error_message": None,
        }
        mock_json_load.return_value = mock_data

        session = ResearchSession.load_session(filepath)

        # Check that the file was opened correctly
        mock_file.assert_called_once_with(filepath, "r")

        # Check that json.load was called
        mock_json_load.assert_called_once()

        # Check that the session was created with the correct attributes
        assert session.session_id == "test-id"
        assert session.user_query == "test query"
        assert session.settings == {"model": "test_model"}
        assert session.start_time == "2023-01-01T00:00:00"
        assert session.end_time == "2023-01-01T01:00:00"
        assert session.status == "completed"
        assert session.system_instruction == "test instruction"
        assert session.iterations == [{"iteration": 1}]
        assert session.aggregated_data == {
            "all_search_queries": ["query1"],
            "aggregated_contexts": ["context1"],
            "last_plan": "plan",
            "last_completed_iteration": 1,
        }
        assert session.final_report == "Final report"
        assert session.error_message is None

    @patch("pathlib.Path.exists", return_value=False)
    def test_load_session_file_not_exists(self, mock_exists):
        """Test that load_session returns None if the file doesn't exist."""
        filepath = Path("/test/path/session.json")

        session = ResearchSession.load_session(filepath)

        assert session is None

    @patch("builtins.open", side_effect=Exception("Test error"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_session_error(self, mock_exists, mock_open):
        """Test that load_session handles errors correctly."""
        filepath = Path("/test/path/session.json")

        session = ResearchSession.load_session(filepath)

        assert session is None

    @patch("pathlib.Path.mkdir", side_effect=Exception("Test mkdir error"))  # Mock mkdir to raise
    @patch("builtins.open", new_callable=mock_open)  # Keep open mocked but not raising
    @patch("builtins.print")
    def test_save_session_error(self, mock_print, mock_file_open, mock_path_mkdir, sample_session):
        """Test that save_session handles errors correctly when directory creation fails."""
        filepath = Path("/test/path/session.json")

        sample_session.save_session(filepath)

        # Check that the error was printed
        mock_print.assert_called_once()
        args, _ = mock_print.call_args
        assert "Error saving session" in args[0]
        # Check that the original exception message from mkdir is part of the logged output
        assert str(mock_path_mkdir.side_effect) in args[0]
