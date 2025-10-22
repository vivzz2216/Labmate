import os
import uuid
from typing import Tuple
from playwright.async_api import async_playwright
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.lexers import JavaLexer, CLexer, JavascriptLexer, HtmlLexer
from pygments.formatters import HtmlFormatter
from jinja2 import Template
from ..config import settings


class ScreenshotService:
    """Service for generating code screenshots using Playwright"""
    
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
    
    async def generate_screenshot(
        self, 
        code: str, 
        output: str, 
        theme: str = "idle",
        job_id: int = None,
        username: str = "User",
        filename: str = "new.py",
        project_files: dict = None
    ) -> Tuple[bool, str, int, int]:
        """
        Generate screenshot of code and output
        
        Args:
            code: Python code to display
            output: Execution output
            theme: 'idle', 'notepad', or 'codeblocks'
            job_id: Job ID for organizing screenshots
            
        Returns:
            Tuple of (success, file_path, width, height)
        """
        
        try:
            # Ensure screenshot directory exists
            screenshot_dir = os.path.join(settings.SCREENSHOT_DIR, str(job_id) if job_id else "temp")
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # For Java/C themes, extract the class name from code to use as filename
            if theme == 'notepad':  # Java
                class_name = self._extract_java_class_name(code)
                if class_name:
                    filename = f"{class_name}.java"
            elif theme == 'codeblocks':  # C
                # Keep existing filename logic for C
                pass
            
            # Generate syntax-highlighted HTML
            highlighted_code = self._highlight_code(code, theme)
            
            # Load and render template
            html_content = await self._render_template(
                highlighted_code, output, theme, username, filename, project_files
            )
            
            # Take screenshot
            screenshot_path = os.path.join(
                screenshot_dir, 
                f"screenshot_{uuid.uuid4().hex[:8]}.png"
            )
            
            success, width, height = await self._take_screenshot(
                html_content, screenshot_path
            )
            
            if success:
                return True, screenshot_path, width, height
            else:
                return False, "", 0, 0
                
        except Exception as e:
            print(f"Screenshot generation error: {str(e)}")
            return False, str(e), 0, 0
    
    
    def _highlight_code(self, code: str, theme: str = "idle") -> str:
        """Apply syntax highlighting based on theme/language"""
        try:
            # Map theme to appropriate lexer
            lexer_map = {
                'idle': PythonLexer(),
                'notepad': JavaLexer(),
                'codeblocks': CLexer(),
                'html': HtmlLexer(),
                'react': JavascriptLexer(),
                'node': JavascriptLexer()
            }
            
            lexer = lexer_map.get(theme, PythonLexer())
            
            formatter = HtmlFormatter(
                nowrap=True,
                cssclass="code-highlight",
                style="default"
            )
            highlighted = highlight(code, lexer, formatter)
            
            # Replace Pygments classes with theme-specific classes
            if theme == 'idle':
                # Python IDLE colors
                replacements = {
                    'class="k"': 'class="keyword"',  # keywords (def, for, in) - ORANGE
                    'class="s"': 'class="string"',   # strings - GREEN
                    'class="c"': 'class="comment"',  # comments - RED
                    'class="m"': 'class="number"',   # numbers - PURPLE
                    'class="nb"': 'class="builtin"', # built-in functions (print, range) - BLACK
                    'class="nf"': 'class="function"', # function names (fibonacci) - BLUE
                    'class="n"': 'class="variable"', # variables - BLACK
                    'class="o"': 'class="operator"', # operators - BLACK
                }
            elif theme == 'notepad':
                # Java Notepad colors
                replacements = {
                    'class="k"': 'class="keyword"',  # keywords - BLUE
                    'class="s"': 'class="string"',   # strings - GREEN
                    'class="c"': 'class="comment"',  # comments - GRAY
                    'class="m"': 'class="number"',   # numbers - RED
                    'class="nf"': 'class="function"', # functions - BLUE
                    'class="n"': 'class="variable"', # variables - BLACK
                    'class="o"': 'class="operator"', # operators - BLACK
                }
            elif theme == 'codeblocks':
                # C CodeBlocks colors
                replacements = {
                    'class="k"': 'class="keyword"',  # keywords - Bold Navy Blue
                    'class="s"': 'class="string"',   # strings - Light Navy Blue
                    'class="c"': 'class="comment"',  # comments - Green
                    'class="m"': 'class="number"',   # numbers - Dark Red
                    'class="nf"': 'class="function"', # functions - Black
                    'class="n"': 'class="variable"', # variables - Black
                    'class="o"': 'class="operator"', # operators - Black
                    'class="cp"': 'class="preprocessor"', # preprocessor - Light Green
                    'class="nb"': 'class="macro"', # macros - Light Green
                    'class="c1"': 'class="preprocessor"', # Alternative preprocessor class
                    'class="cpf"': 'class="preprocessor"', # Preprocessor function
                    'class="kt"': 'class="keyword"', # Type keywords
                    'class="kr"': 'class="keyword"', # Reserved keywords
                }
            else:
                # Default replacements
                replacements = {
                    'class="k"': 'class="keyword"',
                    'class="s"': 'class="string"',
                    'class="c"': 'class="comment"',
                    'class="m"': 'class="number"',
                    'class="nf"': 'class="function"',
                    'class="n"': 'class="variable"',
                    'class="o"': 'class="operator"',
                }
            
            for old_class, new_class in replacements.items():
                highlighted = highlighted.replace(old_class, new_class)
            
            return highlighted
        except Exception as e:
            # Fallback to plain text if highlighting fails
            print(f"Syntax highlighting failed: {e}")
            return code
    
    async def _render_template(
        self, 
        highlighted_code: str, 
        output: str, 
        theme: str,
        username: str = "User",
        filename: str = "new.py",
        project_files: dict = None
    ) -> str:
        """Render HTML template with code and output"""
        
        # Select template file
        template_file = f"{theme}_theme.html"
        template_path = os.path.join(self.template_dir, template_file)
        
        if not os.path.exists(template_path):
            # Fallback to idle theme
            template_path = os.path.join(self.template_dir, "idle_theme.html")
        
        # Read template
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Render template
        template = Template(template_content)
        
        # Clean output for display
        clean_output = self._clean_output(output)
        
        html_content = template.render(
            code_content=highlighted_code,
            output_content=clean_output,
            username=username,
            filename=filename,
            project_files=project_files or {}
        )
        
        return html_content
    
    def _extract_java_class_name(self, code: str) -> str:
        """Extract the public class name from Java code"""
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('public class') and '{' in line:
                # Extract class name from "public class ClassName {"
                parts = line.split()
                if len(parts) >= 3:
                    return parts[2].split('{')[0].strip()
            elif line.startswith('class') and '{' in line:
                # Handle "class ClassName {" without public
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1].split('{')[0].strip()
        return None
    
    def _clean_output(self, output: str) -> str:
        """Clean and format output text to match IDLE shell format"""
        if not output:
            return ""
        
        # Remove excessive whitespace
        lines = output.strip().split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            cleaned_line = line.rstrip()
            if cleaned_line:  # Only add non-empty lines
                cleaned_lines.append(cleaned_line)
        
        # Join lines with spaces (like IDLE does for print output)
        if cleaned_lines:
            cleaned_output = ' '.join(cleaned_lines)
        else:
            cleaned_output = ""
        
        # Limit to reasonable length for screenshot
        if len(cleaned_output) > 2000:
            cleaned_output = cleaned_output[:2000] + " ..."
        
        return cleaned_output
    
    async def _take_screenshot(
        self, 
        html_content: str, 
        output_path: str
    ) -> Tuple[bool, int, int]:
        """Take screenshot using Playwright"""
        
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set viewport size for consistent screenshots
                await page.set_viewport_size({"width": 900, "height": 600})
                
                # Replace relative URLs with absolute URLs so images can load
                html_content = html_content.replace('src="/public/', 'src="http://localhost:8000/public/')
                
                # Set content
                await page.set_content(html_content)
                
                # Wait for content to render
                await page.wait_for_timeout(1000)
                
                # Take screenshot
                await page.screenshot(
                    path=output_path,
                    full_page=True,
                    type='png'
                )
                
                # Get dimensions
                dimensions = await page.evaluate("""
                    () => {
                        const body = document.body;
                        return {
                            width: Math.max(body.scrollWidth, body.offsetWidth),
                            height: Math.max(body.scrollHeight, body.offsetHeight)
                        };
                    }
                """)
                
                await browser.close()
                
                return True, dimensions['width'], dimensions['height']
                
        except Exception as e:
            print(f"Playwright screenshot error: {str(e)}")
            return False, 0, 0
    
    async def test_screenshot(self) -> bool:
        """Test screenshot generation with sample code"""
        test_code = '''
def greet(name):
    return f"Hello, {name}!"

result = greet("LabMate AI")
print(result)
print("Screenshot test successful!")
'''
        
        test_output = "Hello, LabMate AI!\nScreenshot test successful!"
        
        success, path, width, height = await self.generate_screenshot(
            test_code, test_output, "idle"
        )
        
        if success:
            # Clean up test file
            try:
                os.unlink(path)
            except:
                pass
        
        return success and width > 0 and height > 0
    
    async def generate_project_screenshots(
        self,
        project_files: dict,
        screenshots_by_route: dict,
        job_id: int,
        task_id: int,
        username: str = "User"
    ) -> list:
        """
        Generate screenshot for each route in a React project
        
        Args:
            project_files: Dictionary of {filepath: content}
            screenshots_by_route: Dictionary of {route: html_content}
            job_id: Job ID for directory structure
            task_id: Task ID for naming
            username: Username for display
        
        Returns:
            List of {"route": "/path", "url": "/screenshots/..."}
        """
        screenshot_urls = []
        
        print(f"[Screenshot Service] Generating combined screenshots for React project")
        
        # Map route components to their routes
        route_component_mapping = {
            "src/components/Home.js": "/",
            "src/components/Home.jsx": "/",
            "src/components/About.js": "/about", 
            "src/components/About.jsx": "/about",
            "src/components/Contact.js": "/contact",
            "src/components/Contact.jsx": "/contact"
        }
        
        # Files that should only show VS Code (no browser output)
        code_only_files = {
            "src/App.css"
        }
        
        # Files that should show browser output (entry points and main components)
        browser_output_files = {
            "src/App.js",
            "src/App.jsx",
            "src/index.js",
            "src/index.jsx",
            "src/main.js",
            "src/main.jsx"
        }
        
        # Generate screenshots for each file
        for file_path, file_content in project_files.items():
            try:
                # Create filename based on the file path
                filename = file_path.replace("src/", "").replace("/", "_").replace("\\", "_")
                
                print(f"[Screenshot Service] Processing file: {file_path}")
                print(f"[Screenshot Service] In code_only_files: {file_path in code_only_files}")
                print(f"[Screenshot Service] In browser_output_files: {file_path in browser_output_files}")
                print(f"[Screenshot Service] In route_component_mapping: {file_path in route_component_mapping}")
                
                # Check if this file should only show VS Code (no browser output)
                if file_path in code_only_files:
                    # Generate code-only screenshot for CSS files, etc.
                    success, screenshot_path, width, height = await self.generate_screenshot(
                        code=file_content,
                        output="",  # No output for code-only files
                        theme="react",
                        job_id=job_id,
                        username=username,
                        filename=filename,
                        project_files=project_files
                    )
                    print(f"[Screenshot Service] Generated code-only screenshot for {file_path}: {screenshot_path}")
                # Check if this is a main component/entry point that should show browser output
                elif file_path in browser_output_files:
                    # For main components, use the first route's output (usually "/")
                    main_route = "/" if "/" in screenshots_by_route else list(screenshots_by_route.keys())[0] if screenshots_by_route else ""
                    if main_route and main_route in screenshots_by_route:
                        html_content = screenshots_by_route[main_route]
                        success, screenshot_path, width, height = await self.generate_screenshot(
                            code=file_content,
                            output=html_content,  # Include browser output
                            theme="react",
                            job_id=job_id,
                            username=username,
                            filename=filename,
                            project_files=project_files
                        )
                        print(f"[Screenshot Service] Generated combined screenshot for {file_path} + {main_route}: {screenshot_path}")
                    else:
                        # Fallback to code-only if no route output available
                        success, screenshot_path, width, height = await self.generate_screenshot(
                            code=file_content,
                            output="",  # No output
                            theme="react",
                            job_id=job_id,
                            username=username,
                            filename=filename,
                            project_files=project_files
                        )
                        print(f"[Screenshot Service] Generated code-only screenshot for {file_path}: {screenshot_path}")
                # Check if this is a route component that should have combined input+output
                elif file_path in route_component_mapping:
                    route = route_component_mapping[file_path]
                    if route in screenshots_by_route:
                        # Generate combined input+output screenshot for route components
                        html_content = screenshots_by_route[route]
                        success, screenshot_path, width, height = await self.generate_screenshot(
                            code=file_content,
                            output=html_content,  # Include browser output
                            theme="react",
                            job_id=job_id,
                            username=username,
                            filename=filename,
                            project_files=project_files
                        )
                        print(f"[Screenshot Service] Generated combined screenshot for {file_path} + {route}: {screenshot_path}")
                    else:
                        # Fallback to code-only if route not found
                        success, screenshot_path, width, height = await self.generate_screenshot(
                            code=file_content,
                            output="",  # No output
                            theme="react",
                            job_id=job_id,
                            username=username,
                            filename=filename,
                            project_files=project_files
                        )
                        print(f"[Screenshot Service] Generated code-only screenshot for {file_path}: {screenshot_path}")
                else:
                    # Generate code-only screenshot for any other files
                    success, screenshot_path, width, height = await self.generate_screenshot(
                        code=file_content,
                        output="",  # No output for other files
                        theme="react",
                        job_id=job_id,
                        username=username,
                        filename=filename,
                        project_files=project_files
                    )
                    print(f"[Screenshot Service] Generated code-only screenshot for {file_path}: {screenshot_path}")
                
                if success:
                    # Convert absolute path to URL path
                    url_path = screenshot_path.replace("/app", "")
                    screenshot_urls.append({
                        "file": file_path,
                        "url": url_path
                    })
                else:
                    print(f"[Screenshot Service] Failed to generate screenshot for file {file_path}")
                    
            except Exception as e:
                print(f"[Screenshot Service] Error generating screenshot for file {file_path}: {str(e)}")
        
        return screenshot_urls


# Global instance
screenshot_service = ScreenshotService()
