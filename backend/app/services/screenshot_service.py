import os
import uuid
from typing import Tuple
from playwright.async_api import async_playwright
from pygments import highlight
from pygments.lexers import PythonLexer
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
        filename: str = "new.py"
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
            
            # Generate syntax-highlighted HTML
            highlighted_code = self._highlight_code(code, theme)
            
            # Load and render template
            html_content = await self._render_template(
                highlighted_code, output, theme, username, filename
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
                'codeblocks': CLexer()
            }
            
            # Import additional lexers
            from pygments.lexers import JavaLexer, CLexer
            
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
        filename: str = "new.py"
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
            filename=filename
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
