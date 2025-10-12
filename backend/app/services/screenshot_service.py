import os
import uuid
from typing import Tuple, Optional
from playwright.async_api import async_playwright
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from jinja2 import Template
from ..config import settings
from .web_execution_service import web_execution_service


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
        language: str = "python"
    ) -> Tuple[bool, str, int, int]:
        """
        Generate screenshot of code and output
        
        Args:
            code: Code to display
            output: Execution output
            theme: 'idle', 'notepad', 'codeblocks', 'vscode'
            job_id: Job ID for organizing screenshots
            language: 'python', 'java', 'c', 'webdev'
            
        Returns:
            Tuple of (success, file_path, width, height)
        """
        
        try:
            # Ensure screenshot directory exists
            screenshot_dir = os.path.join(settings.SCREENSHOT_DIR, str(job_id) if job_id else "temp")
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # Handle web development differently
            if language == "webdev":
                return await self._generate_webdev_screenshots(
                    code, output, theme, screenshot_dir, job_id
                )
            
            # Generate syntax-highlighted HTML
            highlighted_code = self._highlight_code(code, theme)
            
            # Load and render template
            html_content = await self._render_template(
                highlighted_code, output, theme
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
    
    async def _generate_webdev_screenshots(
        self, 
        code: str, 
        output: str, 
        theme: str,
        screenshot_dir: str,
        job_id: int
    ) -> Tuple[bool, str, int, int]:
        """
        Generate screenshots for web development assignments:
        1. VS Code editor with the code
        2. Webpage output from executing the code
        """
        try:
            # Step 1: Generate VS Code editor screenshot
            vscode_success, vscode_path, vscode_width, vscode_height = await self._generate_vscode_screenshot(
                code, screenshot_dir
            )
            
            # Step 2: Execute web code and capture webpage screenshot
            webpage_success, webpage_path, webpage_width, webpage_height = await self._generate_webpage_screenshot(
                code, screenshot_dir
            )
            
            # For now, return the VS Code screenshot as the main result
            # In the future, we might want to combine both or return both
            if vscode_success:
                return True, vscode_path, vscode_width, vscode_height
            elif webpage_success:
                return True, webpage_path, webpage_width, webpage_height
            else:
                return False, "Failed to generate webdev screenshots", 0, 0
                
        except Exception as e:
            print(f"Webdev screenshot generation error: {str(e)}")
            return False, str(e), 0, 0
    
    async def _generate_vscode_screenshot(
        self, 
        code: str, 
        screenshot_dir: str
    ) -> Tuple[bool, str, int, int]:
        """Generate VS Code editor screenshot"""
        try:
            # Load VS Code template
            vscode_template_path = os.path.join(self.template_dir, "vscode_editor.html")
            
            if not os.path.exists(vscode_template_path):
                return False, "VS Code template not found", 0, 0
            
            # Read template and replace code content
            with open(vscode_template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Escape code for HTML
            escaped_code = code.replace('<', '&lt;').replace('>', '&gt;')
            
            # Replace placeholder
            html_content = template_content.replace('{{CODE_CONTENT}}', escaped_code)
            
            # Take screenshot
            screenshot_path = os.path.join(
                screenshot_dir, 
                f"vscode_editor_{uuid.uuid4().hex[:8]}.png"
            )
            
            success, width, height = await self._take_screenshot(
                html_content, screenshot_path, viewport_width=1400, viewport_height=900
            )
            
            return success, screenshot_path, width, height
            
        except Exception as e:
            print(f"VS Code screenshot error: {str(e)}")
            return False, str(e), 0, 0
    
    async def _generate_webpage_screenshot(
        self, 
        code: str, 
        screenshot_dir: str
    ) -> Tuple[bool, str, int, int]:
        """Generate webpage screenshot by executing the web code"""
        try:
            # Analyze the code to determine approach
            analysis = await web_execution_service.analyze_web_code(code)
            
            # Execute the web code and capture screenshot
            if analysis["suggested_approach"] == "direct_execution":
                screenshot_path = await web_execution_service.execute_web_code(code)
            else:
                # For fragments or mixed code, create a complete HTML page
                screenshot_path = await web_execution_service.execute_web_code(
                    code, width=1200, height=800
                )
            
            if os.path.exists(screenshot_path):
                # Move to our screenshot directory
                final_path = os.path.join(
                    screenshot_dir, 
                    f"webpage_output_{uuid.uuid4().hex[:8]}.png"
                )
                
                # Copy file
                import shutil
                shutil.copy2(screenshot_path, final_path)
                
                # Get dimensions (we'll use default for now)
                width, height = 1200, 800
                
                # Clean up temp file
                try:
                    os.unlink(screenshot_path)
                except:
                    pass
                
                return True, final_path, width, height
            else:
                return False, "Webpage execution failed", 0, 0
                
        except Exception as e:
            print(f"Webpage screenshot error: {str(e)}")
            return False, str(e), 0, 0
    
    def _highlight_code(self, code: str, theme: str = "idle") -> str:
        """Apply syntax highlighting based on theme/language"""
        try:
            # Map theme to appropriate lexer
            lexer_map = {
                'idle': PythonLexer(),
                'notepad': JavaLexer(),
                'codeblocks': CLexer(),
                'vscode': HtmlLexer()  # Default to HTML for web development
            }
            
            # Import additional lexers
            from pygments.lexers import JavaLexer, CLexer, HtmlLexer, JavascriptLexer, CssLexer
            
            # Update lexer map with all imports
            lexer_map.update({
                'notepad': JavaLexer(),
                'codeblocks': CLexer(),
                'vscode': HtmlLexer(),
                'javascript': JavascriptLexer(),
                'css': CssLexer()
            })
            
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
                    'class="k"': 'class="keyword"',  # keywords - BLUE
                    'class="s"': 'class="string"',   # strings - ORANGE
                    'class="c"': 'class="comment"',  # comments - GREEN
                    'class="m"': 'class="number"',   # numbers - LIGHT GREEN
                    'class="nf"': 'class="function"', # functions - YELLOW
                    'class="n"': 'class="variable"', # variables - LIGHT BLUE
                    'class="o"': 'class="operator"', # operators - WHITE
                    'class="cp"': 'class="preprocessor"', # preprocessor - PURPLE
                    'class="nb"': 'class="macro"', # macros - CYAN
                }
            elif theme == 'vscode':
                # VS Code colors for web development
                replacements = {
                    'class="nt"': 'class="html-tag"',  # HTML tags - BLUE
                    'class="na"': 'class="html-attribute"', # HTML attributes - LIGHT BLUE
                    'class="s"': 'class="html-value"', # HTML values - ORANGE
                    'class="k"': 'class="js-keyword"', # JavaScript keywords - BLUE
                    'class="nf"': 'class="js-function"', # JavaScript functions - YELLOW
                    'class="c"': 'class="js-comment"', # Comments - GREEN
                    'class="m"': 'class="js-number"', # Numbers - LIGHT GREEN
                    'class="o"': 'class="operator"', # Operators - WHITE
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
        theme: str
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
            output_content=clean_output
        )
        
        return html_content
    
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
        output_path: str,
        viewport_width: int = 900,
        viewport_height: int = 600
    ) -> Tuple[bool, int, int]:
        """Take screenshot using Playwright"""
        
        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set viewport size for consistent screenshots
                await page.set_viewport_size({"width": viewport_width, "height": viewport_height})
                
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


# Global instance
screenshot_service = ScreenshotService()
