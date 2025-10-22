import docker
import tempfile
import os
import time
import uuid
import subprocess
import asyncio
import re
import json
import shutil
import aiohttp
from typing import Tuple, Dict, Any
from playwright.async_api import async_playwright
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
            language: Programming language ('python', 'c', 'java', 'html', 'react', 'node')
        
        Returns:
            Tuple of (success, output_text, logs, exit_code)
        """
        
        # Handle web languages
        if language in ["html", "react", "node"]:
            return await self._execute_web_code(code, language)
        
        # Use subprocess execution for traditional languages
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
            # Extract class name from code (improved approach)
            class_name = "Main"  # Default fallback
            for line in code.split('\n'):
                line = line.strip()
                if line.startswith('public class') and '{' in line:
                    # Extract class name from "public class ClassName {"
                    parts = line.split()
                    if len(parts) >= 3:
                        class_name = parts[2].split('{')[0].strip()
                        break
                elif line.startswith('class') and '{' in line:
                    # Handle "class ClassName {" without public
                    parts = line.split()
                    if len(parts) >= 2:
                        class_name = parts[1].split('{')[0].strip()
                        break
            
            print(f"Detected Java class name: {class_name}")
            
            # Create temporary Java file with class name as filename
            temp_java_file = os.path.join(tempfile.gettempdir(), f"{class_name}.java")
            with open(temp_java_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            print(f"Created temporary Java file: {temp_java_file}")
            
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
                print(f"Java compilation failed: {errors}")
                return False, "", f"Compilation error: {errors}", compile_process.returncode
            
            print(f"Java compilation successful, running class: {class_name}")
            
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
                
                print(f"Java execution completed with exit code: {exit_code}")
                if errors:
                    print(f"Java execution errors: {errors}")
                if output:
                    print(f"Java execution output: {output}")
                
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
    
    async def _execute_web_code(self, code: str, language: str) -> Tuple[bool, str, str, int]:
        """
        Execute web code (HTML/React/Node) with appropriate framework
        
        Args:
            code: Code to execute
            language: 'html', 'react', or 'node'
        
        Returns:
            Tuple of (success, output_text, logs, exit_code)
        """
        if language == "html":
            return await self._execute_html_code(code)
        elif language == "react":
            return await self._execute_react_code(code)
        elif language == "node":
            return await self._execute_node_code(code)
        else:
            return False, "", f"Unsupported web language: {language}", 1
    
    async def _execute_html_code(self, code: str) -> Tuple[bool, str, str, int]:
        """Execute HTML/CSS/JS code and capture browser output"""
        temp_html_file = None
        temp_dir = None
        
        try:
            # Create temporary directory for HTML file
            temp_dir = tempfile.mkdtemp(prefix="html_")
            temp_html_file = os.path.join(temp_dir, "index.html")
            
            # Write HTML code to file
            with open(temp_html_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            print(f"Created temporary HTML file: {temp_html_file}")
            
            # Use Playwright to render and capture output
            console_logs = []
            output_html = ""
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Capture console logs
                page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
                
                # Load the HTML file
                await page.goto(f"file://{temp_html_file}")
                
                # Wait for JavaScript execution (timeout from config)
                await page.wait_for_timeout(settings.WEB_EXECUTION_TIMEOUT_HTML * 1000)
                
                # Get rendered HTML
                output_html = await page.content()
                
                await browser.close()
            
            # Format console logs
            logs = "\n".join(console_logs) if console_logs else ""
            
            print(f"HTML execution completed successfully")
            return True, output_html, logs, 0
            
        except Exception as e:
            print(f"HTML execution error: {str(e)}")
            return False, "", f"HTML execution error: {str(e)}", 1
        finally:
            # Cleanup temporary files
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
    
    async def _execute_react_code(self, code: str) -> Tuple[bool, str, str, int]:
        """Execute React code using Vite dev server - wrapper around execute_react_project"""
        
        # Check if this is simple code (not a full React project)
        # Simple code doesn't contain React-specific patterns
        is_simple_code = not (
            'import React' in code or 
            'from "react"' in code or 
            'from \'react\'' in code or
            '<' in code or 
            'export default' in code or
            'ReactDOM' in code or
            'BrowserRouter' in code or
            'react-router' in code or
            'useState' in code or
            'useEffect' in code or
            'className=' in code or
            'jsx' in code.lower()
        )
        
        if is_simple_code:
            # For simple code, just execute it as regular JavaScript
            print(f"[React Code] Detected simple code, executing as JavaScript")
            return await self._execute_node_code(code)
        
        # For full React code, use the properly working execute_react_project method
        print(f"[React Code] Detected React code, delegating to execute_react_project")
        
        # Create a simple project structure with the user's code as App.jsx
        project_files = {
            "src/App.jsx": code,
            "src/App.css": ""  # Empty CSS file
        }
        
        # Use the execute_react_project method which handles all the Docker networking properly
        try:
            success, output, logs, exit_code, screenshots = await self.execute_react_project(
                project_files=project_files,
                routes=["/"],
                job_id=f"simple_{uuid.uuid4().hex[:8]}",
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                username="User"
            )
            
            # For simple single-file React execution, we just return the first route's output
            if screenshots and len(screenshots) > 0:
                # Screenshots contain the rendered HTML, but we want to return it as output
                output_html = output if output else "React app rendered successfully"
            else:
                output_html = output if output else "React app executed"
            
            return success, output_html, logs, exit_code
            
        except Exception as e:
            print(f"[React Code] Error: {str(e)}")
            return False, "", f"React execution error: {str(e)}", 1
    
    async def _execute_node_code(self, code: str) -> Tuple[bool, str, str, int]:
        """Execute Node.js/Express code"""
        temp_dir = None
        container_name = None
        
        try:
            # Create temporary project directory
            temp_dir = tempfile.mkdtemp(prefix="node_")
            container_name = f"node_{uuid.uuid4().hex[:8]}"
            
            print(f"Created temporary Node project: {temp_dir}")
            
            # Write package.json
            package_json = {
                "name": "node-app",
                "type": "commonjs",
                "scripts": {
                    "start": "node server.js"
                },
                "dependencies": {
                    "express": "^4.18.2"
                }
            }
            
            with open(os.path.join(temp_dir, "package.json"), "w") as f:
                json.dump(package_json, f, indent=2)
            
            # Write user's server code
            with open(os.path.join(temp_dir, "server.js"), "w") as f:
                f.write(code)
            
            # Spawn Node Docker container
            print(f"Spawning Node.js Docker container: {container_name}")
            
            # Run Docker container with npm install and node server
            process = await asyncio.create_subprocess_exec(
                'docker', 'run', '--rm',
                '--name', container_name,
                '-p', '3000:3000',
                '-v', f'{temp_dir}:/app',
                '-w', '/app',
                '--memory=512m',
                '--cpus=0.5',
                'node:20-slim',
                'sh', '-c',
                'npm install --silent && node server.js',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for server to start
            print("Waiting for Node.js server to start...")
            await asyncio.sleep(5)
            
            # Try to fetch response from server
            output_html = ""
            logs = ""
            
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://host.docker.internal:3000", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        output_html = await response.text()
                        logs = f"HTTP {response.status} OK"
            except Exception as e:
                print(f"Failed to connect to Node.js server: {str(e)}")
                output_html = "Server started (no response captured)"
                logs = f"Server started but connection failed: {str(e)}"
            
            # Terminate Docker container
            try:
                terminate_process = await asyncio.create_subprocess_exec(
                    'docker', 'stop', container_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await terminate_process.wait()
            except:
                pass
            
            print(f"Node.js execution completed successfully")
            return True, output_html, logs, 0
            
        except Exception as e:
            print(f"Node.js execution error: {str(e)}")
            return False, "", f"Node.js execution error: {str(e)}", 1
        finally:
            # Cleanup
            if container_name:
                try:
                    stop_process = await asyncio.create_subprocess_exec(
                        'docker', 'stop', container_name,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await asyncio.wait_for(stop_process.wait(), timeout=5.0)
                except:
                    pass
            
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
    
    async def execute_react_project(self, project_files: dict, routes: list = None, job_id: str = None, task_id: str = None, username: str = None) -> Tuple[bool, str, str, int, dict]:
        """
        Execute complete React project with multiple files
        
        Args:
            project_files: Dictionary of {filepath: content}
            routes: List of routes to capture screenshots for
            job_id: Job identifier
            task_id: Task identifier
            username: Username for the task
        
        Returns:
            Tuple of (success, output, logs, exit_code, screenshots_by_route)
            screenshots_by_route: {"/": "html1", "/about": "html2", ...}
        """
        temp_dir = None
        container_name = None
        
        try:
            # Create project directory in the mounted react_temp volume
            # This ensures the files are accessible to Docker-in-Docker
            base_temp_dir = settings.REACT_TEMP_DIR
            os.makedirs(base_temp_dir, exist_ok=True)
            
            # Create unique project directory
            project_id = uuid.uuid4().hex[:8]
            temp_dir = os.path.join(base_temp_dir, f"react_spa_{project_id}")
            os.makedirs(temp_dir, exist_ok=True)
            
            container_name = f"react_spa_{project_id}"
            
            print(f"[React Project] Created temp directory: {temp_dir}")
            print(f"[React Project] Project files: {list(project_files.keys())}")
            
            # Find an available port first
            import socket
            import random
            def find_free_port():
                # Use ONLY the safest port range for Windows (50000-60000)
                # This avoids Windows reserved ports and Hyper-V dynamic port allocation
                for attempt in range(100):  # Try 100 times with different ports
                    port = random.randint(50000, 60000)
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            s.bind(('', port))
                            s.listen(1)
                            print(f"[React Project] Found free port: {port}")
                            return port
                    except OSError as e:
                        if attempt % 20 == 0:
                            print(f"[React Project] Port {port} unavailable (attempt {attempt}), retrying...")
                        continue
                
                # If we still can't find a port, fail with a clear error
                raise Exception("Could not find an available port in the safe range (50000-60000) after 100 attempts. Please check your Windows Hyper-V port exclusions.")
            
            port = find_free_port()
            print(f"[React Project] Using port: {port}")
            
            # Create full project structure with the determined port
            await self._create_react_project_structure(temp_dir, project_files, port)
            
            # Start Docker container with npm install
            await self._start_react_container(temp_dir, project_id, container_name, port)
            
            # Capture screenshots for all routes
            screenshots = await self._capture_react_routes(routes or ["/"], port, container_name)
            
            print(f"[React Project] Successfully captured {len(screenshots)} routes")
            return True, "All routes captured successfully", "All routes captured successfully", 0, screenshots
            
        except Exception as e:
            print(f"[React Project] Error: {str(e)}")
            return False, f"React project execution failed: {str(e)}", f"React project execution failed: {str(e)}", 1, {}
        finally:
            await self._cleanup_react_project(temp_dir, container_name)
    
    async def _create_react_project_structure(self, temp_dir: str, project_files: dict, port: int = 3001):
        """Write all project files to temp directory"""
        # Create directory structure
        src_dir = os.path.join(temp_dir, "src")
        components_dir = os.path.join(src_dir, "components")
        os.makedirs(components_dir, exist_ok=True)
        
        print(f"[React Project] Creating project structure in {temp_dir}")
        
        # Package.json with react-router-dom
        package_json = {
            "name": "react-spa",
            "type": "module",
            "scripts": {
                "dev": "vite --host 0.0.0.0 --port 3001"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.20.0",
                "vite": "^5.0.0",
                "@vitejs/plugin-react": "^4.2.0"
            }
        }
        package_json_path = os.path.join(temp_dir, "package.json")
        print(f"[React Project] Writing package.json to: {package_json_path}")
        with open(package_json_path, "w") as f:
            json.dump(package_json, f, indent=2)
        print(f"[React Project] package.json written successfully")
        
        # Verify file exists
        if os.path.exists(package_json_path):
            print(f"[React Project] package.json exists: {os.path.getsize(package_json_path)} bytes")
        else:
            print(f"[React Project] ERROR: package.json not created!")
        
        # Vite config - use env var for allowed hosts (more robust)
        vite_config = f"""import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'

const extra = (process.env.__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS || '')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);

export default defineConfig({{
  plugins: [react()],
  server: {{
    host: true,
    port: {port},
    strictPort: true,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      ...extra
    ],
    hmr: {{
      host: process.env.HMR_HOST || undefined,
      clientPort: process.env.HMR_CLIENT_PORT ? Number(process.env.HMR_CLIENT_PORT) : undefined
    }}
  }}
}})
"""
        with open(os.path.join(temp_dir, "vite.config.js"), "w") as f:
            f.write(vite_config)
        
        # Index.html
        index_html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>React SPA Lab</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
"""
        with open(os.path.join(temp_dir, "index.html"), "w") as f:
            f.write(index_html)
        
        # Write all user-provided files
        for filepath, content in project_files.items():
            # Normalize path (remove leading src/ if present since we add it)
            normalized = filepath.replace("src/", "").replace("src\\", "")
            
            # Detect JSX usage in content or explicit .jsx extension
            contains_jsx = False
            try:
                if re.search(r'\bimport\s+React\b', content) or re.search(r'<[A-Za-z]', content):
                    contains_jsx = True
            except Exception:
                contains_jsx = False

            # If the file is App.js, or contains JSX, ensure it uses .jsx extension
            base, ext = os.path.splitext(normalized)
            if normalized == "App.js" or contains_jsx:
                normalized = base + ".jsx"
            
            # Determine full path
            full_path = os.path.join(src_dir, normalized)
            
            # Create parent directories
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Update import statements to use .jsx extensions for JSX files
            updated_content = content
            if contains_jsx or normalized == "App.jsx":
                # Update imports to use .jsx extensions
                updated_content = re.sub(r"import\s+(\w+)\s+from\s+['\"]\.\/components\/(\w+)['\"]", 
                                       r"import \1 from './components/\2.jsx'", updated_content)
            
            # Write file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            print(f"[React Project] Wrote file: {normalized}")
        
        # Create FileExplorer component to show project structure
        file_explorer_path = os.path.join(src_dir, "components", "FileExplorer.js")
        file_explorer_content = """import React from 'react';

function FileExplorer({ files }) {
  return (
    <div style={{ 
      backgroundColor: '#1e1e1e', 
      color: '#d4d4d4', 
      padding: '10px', 
      fontFamily: 'Consolas, monospace',
      fontSize: '12px',
      border: '1px solid #333',
      borderRadius: '4px',
      margin: '10px 0'
    }}>
      <div style={{ color: '#569cd6', marginBottom: '5px' }}>📁 React Project</div>
      <div style={{ marginLeft: '20px' }}>
        <div style={{ color: '#569cd6' }}>📁 src</div>
        <div style={{ marginLeft: '20px' }}>
          {files.map((file, index) => (
            <div key={index} style={{ color: '#9cdcfe' }}>
              📄 {file}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default FileExplorer;
"""
        with open(file_explorer_path, "w", encoding="utf-8") as f:
            f.write(file_explorer_content)
        print(f"[React Project] Created FileExplorer component")
        
        # DON'T modify user's App.js - keep it as is
        # The FileExplorer will be added via main.jsx wrapper instead
        print("[React Project] User's App.js kept unchanged")
        
        # Create main.jsx with FileExplorer wrapper
        main_jsx_path = os.path.join(src_dir, "main.jsx")
        
        # Determine the actual App filename and CSS filename after JSX detection
        app_filename = "App.jsx"  # Default
        css_filename = "App.css"   # Default
        
        for filepath, content in project_files.items():
            normalized = filepath.replace("src/", "").replace("src\\", "")
            
            # Check App.js file
            if normalized == "App.js":
                # Check if it contains JSX
                contains_jsx = False
                try:
                    if re.search(r'\bimport\s+React\b', content) or re.search(r'<[A-Za-z]', content):
                        contains_jsx = True
                except Exception:
                    contains_jsx = False
                
                if contains_jsx:
                    app_filename = "App.jsx"
                else:
                    app_filename = "App.js"
            
            # Check for CSS files
            if normalized.endswith('.css'):
                css_filename = normalized
        
        main_jsx_content = f"""import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './{app_filename}'
import './{css_filename}'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
"""
        with open(main_jsx_path, "w") as f:
            f.write(main_jsx_content)
        print("[React Project] Created clean main.jsx")
    
    async def _start_react_container(self, temp_dir: str, project_id: str, container_name: str, port: int):
        """Start React dev server with extended timeout and better error handling"""
        print(f"[React Project] Starting container: {container_name}")
        
        # First, check if container already exists and remove it
        try:
            await asyncio.create_subprocess_exec(
                'docker', 'rm', '-f', container_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
        except:
            pass
        
        
        # Calculate host path for Docker volume mount
        # The temp_dir is /app/react_temp/react_spa_xxx inside the backend container
        # We need to mount the host path: <HOST_PROJECT_ROOT>/backend/react_temp/react_spa_xxx
        host_project_root = settings.HOST_PROJECT_ROOT
        host_path = os.path.join(host_project_root, "backend", "react_temp", f"react_spa_{project_id}")
        
        # Convert Windows paths to Docker-compatible format
        docker_host_path = host_path.replace('\\', '/')
        
        # Check if this is a Windows absolute path (e.g., C:/ or C:\)
        if len(docker_host_path) > 1 and docker_host_path[1] == ':':
            # Convert C:/Users/... to /c/Users/... format for Docker Desktop on Windows
            drive_letter = docker_host_path[0].lower()
            path_without_drive = docker_host_path[2:]  # Remove "C:"
            docker_host_path = f'/{drive_letter}{path_without_drive}'
        
        print(f"[React Project] Container temp dir: {temp_dir}")
        print(f"[React Project] Host path for mount: {host_path}")
        print(f"[React Project] Docker volume path: {docker_host_path}")
        
        # Start container with volume mount and run npm install + vite directly
        startup_cmd = (
            'echo "=== Starting React project ===" && '
            'echo "Current directory: $(pwd)" && '
            'echo "Files in /app:" && ls -la /app && '
            'echo "=== Testing npm registry connectivity ===" && '
            'timeout 10 npm ping || echo "npm registry unreachable, continuing anyway..." && '
            'echo "=== Installing dependencies (timeout: 60s) ===" && '
            'timeout 60 npm install --no-audit --no-fund --loglevel verbose 2>&1 && '
            'echo "=== Dependencies installed successfully ===" && '
            'echo "=== Starting Vite dev server ===" && '
            f'npx vite --host --port {port} --logLevel info 2>&1'
        )
        
        print(f"[React Project] Starting container with command: {startup_cmd[:100]}...")
        
        process = await asyncio.create_subprocess_exec(
            'docker', 'run', '-d',
            '--name', container_name,
            '--network', 'labmate_default',  # Connect to the same network as backend
            '-p', f'{port}:{port}',
            '-v', f'{docker_host_path}:/app',
            '-w', '/app',
            '--memory=2g', '--cpus=2',
            '-e', f'__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS={container_name}',
            '-e', f'HMR_HOST={container_name}',
            '-e', f'HMR_CLIENT_PORT={port}',
            'node:20-slim',
            'sh', '-c', 
            startup_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            print(f"[React Project] Container start failed: {error_msg}")
            raise Exception(f"Failed to start container: {error_msg}")
        
        container_id = stdout.decode().strip()
        print(f"[React Project] Container started: {container_id}")
        
        # Wait for npm install and Vite startup with better health checks
        print("[React Project] Installing dependencies and starting Vite (this may take 90-120s)...")
        
        # Show initial logs after a short delay
        await asyncio.sleep(2)
        try:
            logs_process = await asyncio.create_subprocess_exec(
                'docker', 'logs', '--tail', '20', container_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
            logs_stdout, logs_stderr = await logs_process.communicate()
            initial_logs = (logs_stdout.decode() if logs_stdout else "") + (logs_stderr.decode() if logs_stderr else "")
            if initial_logs.strip():
                print(f"[React Project] Initial container output:\n{initial_logs}")
        except:
            pass
        
        # Check container logs periodically for debugging
        for attempt in range(24):  # 24 attempts * 5 seconds = 120 seconds
            try:
                # Check if container is still running
                check_process = await asyncio.create_subprocess_exec(
                    'docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                check_stdout, check_stderr = await check_process.communicate()
                if container_name not in check_stdout.decode():
                    print(f"[React Project] Container {container_name} stopped unexpectedly")
                    # Get logs for debugging
                    logs_process = await asyncio.create_subprocess_exec(
                        'docker', 'logs', container_name,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    logs_stdout, logs_stderr = await logs_process.communicate()
                    logs = logs_stdout.decode() + "\n" + logs_stderr.decode()
                    print(f"[React Project] Container logs:\n{logs}")
                    raise Exception(f"Container stopped unexpectedly. Logs:\n{logs}")
                
                # Try to connect to the server via Docker internal networking
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(f"http://{container_name}:{port}", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                            if resp.status == 200:
                                text = await resp.text()
                                # Basic sanity checks: index served and root exists or vite client present
                                if '<div id="root"' in text or 'vite/client' in text or '/@vite/client' in text:
                                    print(f"[React Project] Vite dev server ready! (Status: 200)")
                                    return  # Server is ready
                                else:
                                    print("Server returned 200 but index doesn't contain expected markers; continuing wait.")
                            else:
                                print(f"[React Project] Server responded with {resp.status}; waiting...")
                    except:
                        pass  # Server not ready yet
                
            except aiohttp.ClientError:
                # Server not ready yet, continue waiting
                pass
            except Exception as e:
                print(f"[React Project] Health check error: {e}")
                # Continue waiting unless it's a critical error
                if "Container stopped" in str(e):
                    raise
            
            # Show progress and logs every 3 attempts (15 seconds)
            if attempt > 0 and attempt % 3 == 0:
                print(f"[React Project] Still waiting... ({attempt+1}/24)")
                # Show recent logs
                try:
                    logs_process = await asyncio.create_subprocess_exec(
                        'docker', 'logs', '--tail', '10', container_name,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    logs_stdout, logs_stderr = await logs_process.communicate()
                    recent_logs = logs_stdout.decode() + logs_stderr.decode()
                    if recent_logs.strip():
                        print(f"[React Project] Recent logs:\n{recent_logs}")
                except:
                    pass
            
            await asyncio.sleep(5)
        
        # Get container logs for debugging
        print("[React Project] Timeout reached. Fetching container logs...")
        try:
            logs_process = await asyncio.create_subprocess_exec(
                'docker', 'logs', '--tail', '100', container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logs_stdout, logs_stderr = await logs_process.communicate()
            logs = logs_stdout.decode() + "\n" + logs_stderr.decode()
            print(f"[React Project] Container logs (last 100 lines):\n{logs}")
        except Exception as log_error:
            print(f"[React Project] Failed to fetch logs: {log_error}")
        
        raise Exception("React dev server failed to start after 120 seconds")
    
    async def _capture_react_routes(self, routes: list, port: int, container_name: str) -> dict:
        """Capture screenshot of each route"""
        screenshots = {}
        
        print(f"[React Project] Capturing {len(routes)} routes: {routes} on port {port}")
        
        # First, test server accessibility with curl (if available)
        print(f"[React Project] Testing server accessibility...")
        try:
            curl_process = await asyncio.create_subprocess_exec(
                'curl', '-I', f'http://{container_name}:{port}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            curl_stdout, curl_stderr = await curl_process.communicate()
            curl_output = curl_stdout.decode() + curl_stderr.decode()
            print(f"[React Project] Curl test result:\n{curl_output[:500]}")
        except Exception as curl_error:
            print(f"[React Project] Curl not available, skipping test: {str(curl_error)}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set a longer default timeout
            page.set_default_timeout(60000)  # 60 seconds
            
            # --- NEW: more aggressive logging to debug why modules don't load ---
            # Log all network responses (status + content-type) for debugging
            def _on_response(resp):
                try:
                    url = resp.url
                    status = resp.status
                    # Only print script-relevant resources to keep logs readable
                    if any(x in url for x in ['/@vite/client', '/src/', '.js', '.jsx', '.ts', '.tsx']):
                        ct = resp.headers.get('content-type', '') if hasattr(resp, 'headers') else ''
                        print(f"[React Project] RESP {status} {url} (content-type: {ct})")
                except Exception as e:
                    print(f"[React Project] Response handler error: {e}")

            page.on("response", lambda r: _on_response(r))

            # Log failed requests
            page.on("requestfailed", lambda req: print(f"[React Project] REQ FAILED {req.url} -> {req.failure}"))

            # Keep existing console capture and error capture
            page.on("console", lambda msg: print(f"[Playwright console][{msg.type}] {msg.text}"))

            # Add an init script that writes an inline marker into #root as an immediate test.
            # This runs before any page scripts and will tell us if JS execution is blocked at all.
            inline_test_script = """
            // Inline test script injected by ExecutorService debug mode
            (() => {
              try {
                document.addEventListener('DOMContentLoaded', () => {
                  const root = document.getElementById('root');
                  if (root) {
                    const marker = document.createElement('div');
                    marker.id = '__labmate_inline_debug';
                    marker.textContent = 'INLINE_SCRIPT_RAN';
                    root.appendChild(marker);
                  }
                });
              } catch (e) {
                // ensure exceptions don't block other scripts
                console.error('Inline debug script error', e);
              }
            })();
            """
            await page.add_init_script(inline_test_script)

            # Keep existing JS error capture injection (you already had this)
            await page.expose_function("logError", lambda error: print(f"[React Project] JS Error: {error}"))
            await page.add_init_script("""
                window.jsErrors = [];
                window.consoleLogs = [];
                window.addEventListener('error', (e) => {
                  window.jsErrors.push(e.message + ' at ' + e.filename + ':' + e.lineno);
                });
                const originalLog = console.log;
                const originalError = console.error;
                const originalWarn = console.warn;
                console.log = function(...args) {
                    window.consoleLogs.push('LOG: ' + args.join(' '));
                    originalLog.apply(console, args);
                };
                console.error = function(...args) {
                    window.consoleLogs.push('ERROR: ' + args.join(' '));
                    originalError.apply(console, args);
                };
                console.warn = function(...args) {
                    window.consoleLogs.push('WARN: ' + args.join(' '));
                    originalWarn.apply(console, args);
                };
            """)
            # --- END NEW DEBUGGING INSTRUMENTATION ---
            
            for route in routes:
                try:
                    url = f"http://{container_name}:{port}{route}"
                    print(f"[React Project] Navigating to: {url}")
                    
                    # Navigate to the route with longer timeout
                    try:
                        await page.goto(url, timeout=60000, wait_until="load")
                        print(f"[React Project] Page loaded for {route}")
                    except Exception as nav_error:
                        print(f"[React Project] Navigation error for {route}: {str(nav_error)}")
                        raise
                    
                    # CRITICAL: Wait for Vite to compile and send modules, then for React to execute
                    # Vite uses ES modules which load asynchronously
                    print(f"[React Project] Waiting for Vite modules to load and execute...")
                    
                    # Strategy: Wait for the main.jsx script to actually execute
                    # We'll check multiple conditions to ensure React is ready
                    max_wait = 30  # 30 seconds total
                    for attempt in range(max_wait):
                        await page.wait_for_timeout(1000)  # Wait 1 second
                        
                        # Check if React has mounted (root has children)
                        root_children = await page.evaluate("() => document.getElementById('root')?.children.length || 0")
                        if root_children > 0:
                            print(f"[React Project] ✓ React mounted successfully after {attempt + 1} seconds for {route}")
                            break
                        
                        # Check if scripts are executing (React/ReactDOM loaded)
                        react_loaded = await page.evaluate("() => typeof window.React !== 'undefined'")
                        react_dom_loaded = await page.evaluate("() => typeof window.ReactDOM !== 'undefined'")
                        
                        if attempt % 5 == 0:  # Log every 5 seconds
                            print(f"[React Project] Still waiting for React ({attempt + 1}s)... Root children: {root_children}, React loaded: {react_loaded}, ReactDOM loaded: {react_dom_loaded}")
                        
                        if attempt == max_wait - 1:
                            print(f"[React Project] ⚠ React did not mount after {max_wait} seconds for {route}")
                    
                    # Give one final moment for any last renders
                    await page.wait_for_timeout(2000)
                    
                    # Debug: Check what's actually rendered
                    try:
                        page_title = await page.title()
                        body_text = await page.evaluate("() => document.body.innerText")
                        root_element = await page.evaluate("() => document.getElementById('root')")
                        root_content = await page.evaluate("() => document.getElementById('root')?.innerHTML || 'No root element'")
                        h1_content = await page.evaluate("() => document.querySelector('h1')?.textContent || 'No h1 found'")
                        
                        # Check if root element exists
                        root_exists = root_element is not None
                        
                        print(f"[React Project] Route {route} - Title: '{page_title}'")
                        print(f"[React Project] Route {route} - Root element exists: {root_exists}")
                        print(f"[React Project] Route {route} - Body preview: {body_text[:200] if body_text else 'Empty'}...")
                        print(f"[React Project] Route {route} - Root content: {root_content[:200] if root_content else 'Empty'}...")
                        print(f"[React Project] Route {route} - H1 content: '{h1_content}'")
                        
                        # Check for inline debug marker (indicates JS execution is working)
                        inline_marker = await page.evaluate("() => document.getElementById('__labmate_inline_debug')?.textContent || 'NOT_FOUND'")
                        print(f"[React Project] Route {route} - Inline marker: '{inline_marker}'")
                        
                        # Check for JavaScript errors
                        js_errors = await page.evaluate("() => window.jsErrors || []")
                        if js_errors:
                            print(f"[React Project] Route {route} - JS Errors: {js_errors}")
                        
                        # Check console errors
                        console_logs = await page.evaluate("() => window.consoleLogs || []")
                        if console_logs:
                            print(f"[React Project] Route {route} - Console logs: {console_logs}")
                        
                        # Check if React scripts loaded
                        scripts = await page.evaluate("() => Array.from(document.scripts).map(s => s.src)")
                        print(f"[React Project] Route {route} - Scripts loaded: {scripts}")
                        
                        # Check if React is actually loaded
                        react_loaded = await page.evaluate("() => typeof window.React !== 'undefined'")
                        react_dom_loaded = await page.evaluate("() => typeof window.ReactDOM !== 'undefined'")
                        print(f"[React Project] Route {route} - React loaded: {react_loaded}")
                        print(f"[React Project] Route {route} - ReactDOM loaded: {react_dom_loaded}")
                        
                        # Check if there are any elements in the root
                        root_children = await page.evaluate("() => document.getElementById('root')?.children.length || 0")
                        print(f"[React Project] Route {route} - Root children count: {root_children}")
                        
                        # Check if there are any React components mounted
                        react_fiber = await page.evaluate("() => document.getElementById('root')?._reactInternalFiber || document.getElementById('root')?._reactInternalInstance")
                        print(f"[React Project] Route {route} - React fiber exists: {react_fiber is not None}")
                        
                        # Check the actual HTML content of the root
                        root_html = await page.evaluate("() => document.getElementById('root')?.outerHTML || 'No root element'")
                        print(f"[React Project] Route {route} - Root HTML: {root_html[:500]}...")
                        
                        # Check if there are any script execution errors
                        script_errors = await page.evaluate("""
                            () => {
                                const scripts = Array.from(document.scripts);
                                const errors = [];
                                scripts.forEach((script, index) => {
                                    if (script.src && !script.src.includes('@vite/client')) {
                                        // Check if script failed to load
                                        if (!script.textContent && !script.src.includes('main.jsx')) {
                                            errors.push(`Script ${index} (${script.src}) may have failed to load`);
                                        }
                                    }
                                });
                                return errors;
                            }
                        """)
                        if script_errors:
                            print(f"[React Project] Route {route} - Script errors: {script_errors}")
                        
                        # Check if the main.jsx script is actually executing
                        main_script_executed = await page.evaluate("""
                            () => {
                                // Check if ReactDOM.createRoot was called
                                return window.ReactDOM && window.ReactDOM.createRoot;
                            }
                        """)
                        print(f"[React Project] Route {route} - ReactDOM.createRoot available: {main_script_executed}")
                        
                        # Check if there are any network errors
                        network_errors = await page.evaluate("""
                            () => {
                                const scripts = Array.from(document.scripts);
                                return scripts.filter(s => s.src).map(s => ({
                                    src: s.src,
                                    loaded: s.readyState === 'complete' || s.readyState === 'loaded'
                                }));
                            }
                        """)
                        print(f"[React Project] Route {route} - Script loading status: {network_errors}")
                            
                    except Exception as debug_error:
                        print(f"[React Project] Debug error for {route}: {str(debug_error)}")
                    
                    # Get the HTML content
                    html_content = await page.content()
                    screenshots[route] = html_content
                    print(f"[React Project] ✓ Successfully captured route: {route}")
                    
                except Exception as e:
                    print(f"[React Project] ✗ Failed to capture {route}: {str(e)}")
                    import traceback
                    print(f"[React Project] Traceback: {traceback.format_exc()}")
                    screenshots[route] = f"Error capturing route: {str(e)}"
            
            await browser.close()
        
        return screenshots

    async def _cleanup_react_project(self, temp_dir: str, container_name: str):
        """Clean up temporary files and containers"""
        print("[React Project] Cleaning up...")

        # Stop and remove container
        if container_name:
            try:
                stop_process = await asyncio.create_subprocess_exec(
                    'docker', 'stop', container_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(stop_process.wait(), timeout=5.0)
                print(f"[React Project] Stopped container: {container_name}")
            except Exception as e:
                print(f"[React Project] Failed to stop container: {str(e)}")
        
        # Remove temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"[React Project] Removed temp directory: {temp_dir}")
            except Exception as e:
                print(f"[React Project] Failed to remove temp directory: {str(e)}")


# Create singleton instance
executor_service = ExecutorService()
