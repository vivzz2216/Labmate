import os
import tempfile
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class WebExecutionService:
    """
    Service for executing web development code (HTML/CSS/JS) and capturing screenshots
    of the rendered webpage output.
    """
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "web_execution"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def execute_web_code(
        self, 
        html_code: str, 
        css_code: Optional[str] = None, 
        js_code: Optional[str] = None,
        width: int = 1200,
        height: int = 800
    ) -> str:
        """
        Execute web code and capture screenshot of the rendered webpage.
        
        Args:
            html_code: HTML code to execute
            css_code: Optional CSS code to include
            js_code: Optional JavaScript code to include
            width: Screenshot width
            height: Screenshot height
            
        Returns:
            Path to the screenshot file
        """
        try:
            # Create temporary HTML file
            html_file = await self._create_html_file(html_code, css_code, js_code)
            
            # Execute the web code and capture screenshot
            screenshot_path = await self._capture_webpage_screenshot(
                html_file, width, height
            )
            
            # Clean up temporary files
            if html_file.exists():
                html_file.unlink()
            
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Error executing web code: {e}")
            raise
    
    async def _create_html_file(
        self, 
        html_code: str, 
        css_code: Optional[str] = None, 
        js_code: Optional[str] = None
    ) -> Path:
        """Create a complete HTML file with embedded CSS and JS."""
        
        # If the HTML code already has a complete structure, use it as is
        if html_code.strip().lower().startswith('<!doctype') or html_code.strip().lower().startswith('<html'):
            complete_html = html_code
        else:
            # Wrap the code in a basic HTML structure
            complete_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Development Output</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #ffffff;
            color: #333333;
            line-height: 1.6;
        }}
        
        /* Custom CSS */
        {css_code or ''}
    </style>
</head>
<body>
    {html_code}
    
    <script>
        /* Custom JavaScript */
        {js_code or ''}
    </script>
</body>
</html>"""
        
        # Create temporary file
        temp_file = self.temp_dir / f"web_output_{asyncio.get_event_loop().time()}.html"
        temp_file.write_text(complete_html, encoding='utf-8')
        
        return temp_file
    
    async def _capture_webpage_screenshot(
        self, 
        html_file: Path, 
        width: int = 1200, 
        height: int = 800
    ) -> str:
        """Capture screenshot of the rendered webpage using Playwright."""
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            try:
                # Create new page
                page = await browser.new_page()
                
                # Set viewport size
                await page.set_viewport_size({"width": width, "height": height})
                
                # Load the HTML file
                file_url = f"file://{html_file.absolute()}"
                await page.goto(file_url, wait_until="networkidle")
                
                # Wait a bit for any animations or dynamic content to load
                await page.wait_for_timeout(1000)
                
                # Take screenshot
                screenshot_path = self.temp_dir / f"webpage_screenshot_{asyncio.get_event_loop().time()}.png"
                await page.screenshot(
                    path=str(screenshot_path),
                    full_page=True,
                    type='png'
                )
                
                return str(screenshot_path)
                
            finally:
                await browser.close()
    
    async def execute_and_capture_complete_web_project(
        self, 
        files: Dict[str, str],
        main_file: str = "index.html",
        width: int = 1200,
        height: int = 800
    ) -> str:
        """
        Execute a complete web project with multiple files and capture screenshot.
        
        Args:
            files: Dictionary of filename -> content
            main_file: The main HTML file to render
            width: Screenshot width
            height: Screenshot height
            
        Returns:
            Path to the screenshot file
        """
        try:
            # Create temporary project directory
            project_dir = self.temp_dir / f"project_{asyncio.get_event_loop().time()}"
            project_dir.mkdir(exist_ok=True)
            
            # Write all files
            for filename, content in files.items():
                file_path = project_dir / filename
                file_path.write_text(content, encoding='utf-8')
            
            # Get the main HTML file
            main_html_path = project_dir / main_file
            if not main_html_path.exists():
                raise ValueError(f"Main file {main_file} not found in project files")
            
            # Capture screenshot
            screenshot_path = await self._capture_webpage_screenshot(
                main_html_path, width, height
            )
            
            # Clean up project directory
            import shutil
            shutil.rmtree(project_dir, ignore_errors=True)
            
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Error executing web project: {e}")
            raise
    
    async def analyze_web_code(self, code: str) -> Dict[str, Any]:
        """
        Analyze web code to determine if it's HTML, CSS, JS, or mixed.
        
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "type": "unknown",
            "has_html": False,
            "has_css": False,
            "has_js": False,
            "is_complete_html": False,
            "suggested_approach": "basic_html"
        }
        
        code_lower = code.lower().strip()
        
        # Check for HTML
        if any(tag in code_lower for tag in ['<html', '<div', '<p', '<h1', '<h2', '<body', '<head']):
            analysis["has_html"] = True
        
        # Check for CSS
        if any(css in code_lower for css in ['<style>', 'color:', 'background:', 'margin:', 'padding:']):
            analysis["has_css"] = True
        
        # Check for JavaScript
        if any(js in code_lower for js in ['<script>', 'function', 'const ', 'let ', 'var ']):
            analysis["has_js"] = True
        
        # Check if it's complete HTML
        if code_lower.startswith('<!doctype') or code_lower.startswith('<html'):
            analysis["is_complete_html"] = True
            analysis["type"] = "complete_html"
        elif analysis["has_html"]:
            analysis["type"] = "html_fragment"
        elif analysis["has_css"] and not analysis["has_html"]:
            analysis["type"] = "css_only"
        elif analysis["has_js"] and not analysis["has_html"]:
            analysis["type"] = "js_only"
        
        # Determine suggested approach
        if analysis["is_complete_html"]:
            analysis["suggested_approach"] = "direct_execution"
        elif analysis["has_html"]:
            analysis["suggested_approach"] = "wrap_in_html"
        elif analysis["has_css"] or analysis["has_js"]:
            analysis["suggested_approach"] = "create_demo_page"
        else:
            analysis["suggested_approach"] = "create_basic_page"
        
        return analysis

# Global instance
web_execution_service = WebExecutionService()
