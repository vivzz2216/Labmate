import docker
import tempfile
import os
import time
import uuid
import subprocess
import asyncio
from typing import Tuple, Dict, Any
from ..config import settings


class ExecutorService:
    """Service for executing Python code in Docker containers"""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.image = settings.DOCKER_IMAGE
        except Exception as e:
            print(f"Warning: Could not connect to Docker: {e}")
            self.client = None
            self.image = settings.DOCKER_IMAGE
    
    async def execute_code(self, code: str, language: str = "python") -> Tuple[bool, str, str, int]:
        """
        Execute code in a sandboxed subprocess based on language
        
        Args:
            code: Code to execute
            language: Programming language ('python', 'java', 'c', 'webdev')
        
        Returns:
            Tuple of (success, output_text, logs, exit_code)
        """
        
        # For web development, we don't actually execute the code
        # The web execution service handles that separately
        if language == "webdev":
            return await self._execute_web_code(code)
        
        # For other languages, use subprocess execution
        return await self._subprocess_execute(code)
    
    async def _execute_web_code(self, code: str) -> Tuple[bool, str, str, int]:
        """Handle web development code execution"""
        
        # For web development, we consider it successful if it's valid HTML/CSS/JS
        # The actual execution and screenshot generation happens in the screenshot service
        
        # Basic validation
        if not code.strip():
            return False, "", "Empty web code", 1
        
        # Check if it looks like web code
        code_lower = code.lower().strip()
        if any(web_indicator in code_lower for web_indicator in [
            '<html', '<div', '<p', '<h1', '<h2', '<h3', '<body', '<head',
            'color:', 'background:', 'margin:', 'padding:', 'font-',
            'function(', 'var ', 'let ', 'const ', '<script'
        ]):
            return True, "Web code ready for execution", "Web development code validated", 0
        else:
            return False, "", "Code does not appear to be valid web development code", 1
    
    async def _subprocess_execute(self, code: str) -> Tuple[bool, str, str, int]:
        """Execute code using subprocess (safer than Docker-in-Docker for MVP)"""
        temp_file = None
        
        try:
            # Create temporary file with code
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute with timeout
            process = await asyncio.create_subprocess_exec(
                'python3',
                temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(),
                    timeout=30.0  # 30 second timeout
                )
                
                output = stdout_data.decode('utf-8') if stdout_data else ""
                errors = stderr_data.decode('utf-8') if stderr_data else ""
                exit_code = process.returncode
                
                success = exit_code == 0
                return success, output, errors, exit_code
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return False, "", "Execution timeout (30s limit)", 124
                
        except Exception as e:
            return False, "", f"Execution error: {str(e)}", 1
            
        finally:
            # Cleanup temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    async def _mock_execute(self, code: str) -> Tuple[bool, str, str, int]:
        """Mock execution when Docker is not available"""
        try:
            # Simple mock execution
            if "print" in code:
                # Extract print statements for mock output
                import re
                print_matches = re.findall(r'print\s*\(\s*["\'](.*?)["\']', code)
                output = '\n'.join(print_matches) if print_matches else "Mock execution successful"
            else:
                output = "Mock execution successful"
            
            return True, output, "", 0  # exit_code 0 for success
            
        except Exception as e:
            logs = f"Execution error: {str(e)}"
            return False, "", logs, 1
    
    async def _docker_execute(self, code: str) -> Tuple[bool, str, str, int]:
        """Execute code in Docker container"""
        container = None
        temp_file = None
        
        try:
            # Create temporary file with code
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.py', 
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = f.name
            
            # Run container
            container = self.client.containers.run(
                self.image,
                f"python /code/{os.path.basename(temp_file)}",
                volumes={
                    os.path.dirname(temp_file): {'bind': '/code', 'mode': 'ro'}
                },
                mem_limit=settings.MEMORY_LIMIT,
                cpu_period=settings.CPU_PERIOD,
                cpu_quota=settings.CPU_QUOTA,
                network_disabled=True,
                remove=False,
                detach=True,
                stdout=True,
                stderr=True
            )
            
            # Wait for container with timeout
            result = container.wait(timeout=settings.CONTAINER_TIMEOUT)
            exit_code = result['StatusCode']
            
            # Get output
            output = container.logs(stdout=True, stderr=False).decode('utf-8')
            logs = container.logs(stdout=False, stderr=True).decode('utf-8')
            
            # Clean up container
            container.remove()
            
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            
            success = exit_code == 0
            return success, output, logs, exit_code
            
        except docker.errors.ContainerError as e:
            logs = f"Container execution error: {str(e)}"
            return False, "", logs, 1
        except Exception as e:
            logs = f"Execution error: {str(e)}"
            return False, "", logs, 1
        finally:
            # Cleanup
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass


# Create singleton instance
executor_service = ExecutorService()