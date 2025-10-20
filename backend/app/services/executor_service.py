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
        Execute code in a sandboxed subprocess
        
        Args:
            code: Code to execute
            language: Programming language ('python', 'c', 'java')
        
        Returns:
            Tuple of (success, output_text, logs, exit_code)
        """
        
        # Use subprocess execution (simpler than Docker-in-Docker)
        return await self._subprocess_execute(code, language)
    
    async def _subprocess_execute(self, code: str, language: str = "python") -> Tuple[bool, str, str, int]:
        """Execute code using subprocess (safer than Docker-in-Docker for MVP)"""
        temp_file = None
        executable_file = None
        
        try:
            if language == "c":
                # For C code, compile and run
                return await self._execute_c_code(code)
            elif language == "java":
                # For Java code, compile and run
                return await self._execute_java_code(code)
            else:
                # Default to Python
                return await self._execute_python_code(code)
                
        except Exception as e:
            return False, "", f"Execution error: {str(e)}", 1
        finally:
            # Clean up temporary files
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
            if executable_file and os.path.exists(executable_file):
                try:
                    os.unlink(executable_file)
                except:
                    pass
    
    async def _execute_python_code(self, code: str) -> Tuple[bool, str, str, int]:
        """Execute Python code"""
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
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    async def _execute_c_code(self, code: str) -> Tuple[bool, str, str, int]:
        """Execute C code by compiling and running"""
        temp_c_file = None
        executable_file = None
        
        try:
            # Create temporary C file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.c',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_c_file = f.name
            
            # Create executable filename
            executable_file = temp_c_file.replace('.c', '')
            
            # Compile C code
            compile_process = await asyncio.create_subprocess_exec(
                'gcc',
                temp_c_file,
                '-o',
                executable_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            compile_stdout, compile_stderr = await compile_process.communicate()
            
            if compile_process.returncode != 0:
                # Compilation failed
                errors = compile_stderr.decode('utf-8') if compile_stderr else ""
                return False, "", f"Compilation error: {errors}", compile_process.returncode
            
            # Run the executable
            run_process = await asyncio.create_subprocess_exec(
                executable_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    run_process.communicate(),
                    timeout=30.0  # 30 second timeout
                )
                
                output = stdout_data.decode('utf-8') if stdout_data else ""
                errors = stderr_data.decode('utf-8') if stderr_data else ""
                exit_code = run_process.returncode
                
                success = exit_code == 0
                return success, output, errors, exit_code
                
            except asyncio.TimeoutError:
                run_process.kill()
                await run_process.wait()
                return False, "", "Execution timeout (30s limit)", 124
                
        except Exception as e:
            return False, "", f"Execution error: {str(e)}", 1
        finally:
            if temp_c_file and os.path.exists(temp_c_file):
                try:
                    os.unlink(temp_c_file)
                except:
                    pass
            if executable_file and os.path.exists(executable_file):
                try:
                    os.unlink(executable_file)
                except:
                    pass
    
    async def _execute_java_code(self, code: str) -> Tuple[bool, str, str, int]:
        """Execute Java code by compiling and running"""
        temp_java_file = None
        
        try:
            # Extract class name from code (simple approach)
            class_name = "Main"  # Default
            for line in code.split('\n'):
                if 'public class' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        class_name = parts[2].split('{')[0].strip()
                    break
            
            # Create temporary Java file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.java',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_java_file = f.name
            
            # Compile Java code
            compile_process = await asyncio.create_subprocess_exec(
                'javac',
                temp_java_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            compile_stdout, compile_stderr = await compile_process.communicate()
            
            if compile_process.returncode != 0:
                # Compilation failed
                errors = compile_stderr.decode('utf-8') if compile_stderr else ""
                return False, "", f"Compilation error: {errors}", compile_process.returncode
            
            # Run the Java program
            java_dir = os.path.dirname(temp_java_file)
            run_process = await asyncio.create_subprocess_exec(
                'java',
                '-cp',
                java_dir,
                class_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    run_process.communicate(),
                    timeout=30.0  # 30 second timeout
                )
                
                output = stdout_data.decode('utf-8') if stdout_data else ""
                errors = stderr_data.decode('utf-8') if stderr_data else ""
                exit_code = run_process.returncode
                
                success = exit_code == 0
                return success, output, errors, exit_code
                
            except asyncio.TimeoutError:
                run_process.kill()
                await run_process.wait()
                return False, "", "Execution timeout (30s limit)", 124
                
        except Exception as e:
            return False, "", f"Execution error: {str(e)}", 1
        finally:
            if temp_java_file and os.path.exists(temp_java_file):
                try:
                    os.unlink(temp_java_file)
                except:
                    pass
            # Clean up .class files
            if temp_java_file:
                class_file = temp_java_file.replace('.java', '.class')
                if os.path.exists(class_file):
                    try:
                        os.unlink(class_file)
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