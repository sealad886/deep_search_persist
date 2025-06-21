"""
Docker Integration Tests

Tests the complete Docker setup including:
- Container health checks
- Service connectivity  
- API endpoints
- Database connectivity
- WebUI functionality
"""

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import pytest
import requests
from httpx import AsyncClient


class DockerTestHelper:
    """Helper class for Docker test operations."""
    
    def __init__(self):
        self.docker_dir = Path(__file__).parent.parent.parent / "docker"
        self.compose_file = self.docker_dir / "docker-compose.persist.yml"
        self.env_file = self.docker_dir / ".env"
        
    def ensure_env_file(self):
        """Ensure .env file exists with required settings."""
        if not self.env_file.exists():
            env_content = """# Docker Environment Variables for Testing
MONGO_URI=mongodb://mongo:27017/deep_search_test
GRADIO_HOST_PORT=7861
GRADIO_CONTAINER_PORT=7860
OLLAMA_PORT=11235
OLLAMA_BASE_URL=http://host.docker.internal:11235
"""
            with open(self.env_file, 'w') as f:
                f.write(env_content)
    
    def is_docker_running(self) -> bool:
        """Check if Docker daemon is running."""
        try:
            result = subprocess.run(
                ["docker", "info"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def start_services(self, services: Optional[List[str]] = None):
        """Start Docker services."""
        if not self.is_docker_running():
            pytest.skip("Docker daemon not running")
            
        self.ensure_env_file()
        
        cmd = [
            "docker", "compose", 
            "-f", str(self.compose_file),
            "up", "-d", "--build"
        ]
        
        if services:
            cmd.extend(services)
            
        subprocess.run(cmd, cwd=self.docker_dir, check=True)
    
    def stop_services(self):
        """Stop Docker services."""
        subprocess.run([
            "docker", "compose", 
            "-f", str(self.compose_file),
            "down"
        ], cwd=self.docker_dir)
    
    def wait_for_service_health(self, service_url: str, timeout: int = 120) -> bool:
        """Wait for a service to become healthy."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(service_url, timeout=5)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            time.sleep(2)
        
        return False
    
    def get_container_logs(self, service_name: str) -> str:
        """Get logs from a container."""
        try:
            result = subprocess.run([
                "docker", "compose", 
                "-f", str(self.compose_file),
                "logs", service_name
            ], capture_output=True, text=True, cwd=self.docker_dir)
            return result.stdout
        except subprocess.CalledProcessError:
            return ""


@pytest.fixture(scope="session")
def docker_helper():
    """Provide Docker helper for the test session."""
    return DockerTestHelper()


@pytest.fixture(scope="session") 
def docker_services(docker_helper):
    """Start Docker services for testing."""
    if not docker_helper.is_docker_running():
        pytest.skip("Docker daemon not running")
    
    # Start core services needed for testing
    docker_helper.start_services(["mongo", "app-persist"])
    
    # Wait for services to be healthy
    api_healthy = docker_helper.wait_for_service_health("http://localhost:8000/health")
    
    if not api_healthy:
        logs = docker_helper.get_container_logs("app-persist")
        pytest.fail(f"API service failed to start. Logs:\n{logs}")
    
    yield
    
    # Cleanup
    docker_helper.stop_services()


@pytest.mark.docker
@pytest.mark.integration
class TestDockerIntegration:
    """Test Docker integration scenarios."""
    
    def test_docker_daemon_available(self, docker_helper):
        """Test that Docker daemon is running."""
        assert docker_helper.is_docker_running(), "Docker daemon must be running for Docker tests"
    
    def test_compose_file_exists(self, docker_helper):
        """Test that Docker Compose file exists."""
        assert docker_helper.compose_file.exists(), "docker-compose.persist.yml must exist"
    
    @pytest.mark.slow
    async def test_api_service_health(self, docker_services):
        """Test that the API service is healthy."""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
    
    @pytest.mark.slow
    async def test_api_sessions_endpoint(self, docker_services):
        """Test that sessions endpoint works."""
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/sessions")
            # Should return 200 with empty sessions list or existing sessions
            assert response.status_code == 200
            data = response.json()
            assert "sessions" in data
            assert isinstance(data["sessions"], list)
    
    @pytest.mark.slow 
    async def test_mongodb_connectivity(self, docker_services):
        """Test MongoDB connectivity through the API."""
        # Test by creating a simple research session
        async with httpx.AsyncClient() as client:
            payload = {
                "messages": [{"role": "user", "content": "Test query"}],
                "max_iterations": 1,
                "stream": False
            }
            
            # This should create a session in MongoDB
            response = await client.post(
                "http://localhost:8000/v1/chat/completions",
                json=payload,
                timeout=30
            )
            
            # May return error due to missing external services, but should not be DB connection error
            # Check that we don't get a 500 error specifically about MongoDB
            if response.status_code == 500:
                error_text = response.text
                assert "mongo" not in error_text.lower(), f"MongoDB connection error: {error_text}"


@pytest.mark.docker
@pytest.mark.e2e
class TestDockerWebUI:
    """Test Docker WebUI functionality."""
    
    @pytest.fixture(scope="class")
    def webui_services(self, docker_helper):
        """Start WebUI services for testing."""
        if not docker_helper.is_docker_running():
            pytest.skip("Docker daemon not running")
        
        # Start all services including WebUI
        docker_helper.start_services()
        
        # Wait for WebUI to be healthy
        webui_healthy = docker_helper.wait_for_service_health("http://localhost:7861")
        
        if not webui_healthy:
            logs = docker_helper.get_container_logs("gradio-ui")
            pytest.fail(f"WebUI service failed to start. Logs:\n{logs}")
        
        yield
        
        docker_helper.stop_services()
    
    @pytest.mark.slow
    def test_webui_accessible(self, webui_services):
        """Test that WebUI is accessible."""
        response = requests.get("http://localhost:7861", timeout=10)
        assert response.status_code == 200
        assert "DeepSearch" in response.text or "gradio" in response.text.lower()
    
    @pytest.mark.slow  
    def test_webui_api_connectivity(self, webui_services):
        """Test that WebUI can connect to API."""
        # The WebUI should be able to reach the API service
        # We can test this by checking if the WebUI loads without errors
        response = requests.get("http://localhost:7861", timeout=10)
        assert response.status_code == 200
        
        # Check that there are no obvious connection errors in the page
        page_content = response.text.lower()
        assert "connection refused" not in page_content
        assert "network error" not in page_content


@pytest.mark.docker
@pytest.mark.integration 
class TestDockerDatabasePersistence:
    """Test database persistence in Docker."""
    
    @pytest.mark.slow
    async def test_session_persistence_across_restarts(self, docker_helper):
        """Test that sessions persist across container restarts."""
        if not docker_helper.is_docker_running():
            pytest.skip("Docker daemon not running")
        
        # Start services
        docker_helper.start_services(["mongo", "app-persist"])
        
        # Wait for API to be ready
        api_ready = docker_helper.wait_for_service_health("http://localhost:8000/health")
        assert api_ready, "API service must be ready"
        
        # Create a test session
        session_query = "Test persistence query"
        async with httpx.AsyncClient() as client:
            payload = {
                "messages": [{"role": "user", "content": session_query}],
                "max_iterations": 1,
                "stream": False
            }
            
            # Create session (may fail due to external services, but should create DB entry)
            await client.post("http://localhost:8000/v1/chat/completions", json=payload, timeout=30)
            
            # Get current sessions
            response = await client.get("http://localhost:8000/sessions")
            initial_sessions = response.json()["sessions"]
            initial_count = len(initial_sessions)
        
        # Restart the app container
        subprocess.run([
            "docker", "compose", "-f", str(docker_helper.compose_file),
            "restart", "app-persist"
        ], cwd=docker_helper.docker_dir)
        
        # Wait for service to be ready again
        api_ready = docker_helper.wait_for_service_health("http://localhost:8000/health")
        assert api_ready, "API service must be ready after restart"
        
        # Check that sessions are still there
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/sessions")
            assert response.status_code == 200
            
            after_restart_sessions = response.json()["sessions"]
            assert len(after_restart_sessions) >= initial_count, "Sessions should persist across restarts"
        
        # Cleanup
        docker_helper.stop_services()


@pytest.mark.docker
@pytest.mark.slow
class TestDockerServiceConnectivity:
    """Test connectivity between Docker services."""
    
    def test_all_services_can_start(self, docker_helper):
        """Test that all services can start without conflicts."""
        if not docker_helper.is_docker_running():
            pytest.skip("Docker daemon not running")
        
        try:
            # Start all services
            docker_helper.start_services()
            
            # Give services time to initialize
            time.sleep(10)
            
            # Check that key services are responsive
            services_to_check = [
                ("API", "http://localhost:8000/health"),
                ("WebUI", "http://localhost:7861"),
            ]
            
            failed_services = []
            for service_name, url in services_to_check:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code != 200:
                        failed_services.append(f"{service_name} ({response.status_code})")
                except requests.RequestException as e:
                    failed_services.append(f"{service_name} ({str(e)})")
            
            if failed_services:
                # Get logs for debugging
                logs = {
                    "app-persist": docker_helper.get_container_logs("app-persist"),
                    "gradio-ui": docker_helper.get_container_logs("gradio-ui")
                }
                pytest.fail(f"Services failed: {failed_services}. Logs: {logs}")
                
        finally:
            docker_helper.stop_services()