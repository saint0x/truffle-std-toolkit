import os
import json
import asyncio
from typing import Optional, Dict, List, Union, Any
from datetime import datetime
from pathlib import Path
import playwright.async_api as pw
import truffle

class BrowserTool:
    """Tool for automated browser interactions using Playwright."""
    
    def __init__(self):
        self.client = truffle.TruffleClient()
        self.browser_type = os.getenv("BROWSER_TYPE", "chromium")
        self.timeout = int(os.getenv("BROWSER_TIMEOUT", "30000"))
        self.headless = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
        self.screenshots_dir = os.getenv("BROWSER_SCREENSHOTS_DIR", "./screenshots")
        self._browser = None
        self._context = None

    async def _ensure_browser(self) -> None:
        """Ensure browser is initialized."""
        if not self._browser:
            playwright = await pw.async_playwright().start()
            browser_class = getattr(playwright, self.browser_type)
            self._browser = await browser_class.launch(headless=self.headless)
            self._context = await self._browser.new_context()

    async def _cleanup(self) -> None:
        """Clean up browser resources."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        self._context = None
        self._browser = None

    def _ensure_screenshots_dir(self) -> None:
        """Ensure screenshots directory exists."""
        Path(self.screenshots_dir).mkdir(parents=True, exist_ok=True)

    @truffle.tool(
        description="Visit a webpage and extract its content",
        icon="globe"
    )
    @truffle.args(
        url="URL to visit",
        wait_for="CSS selector to wait for before proceeding",
        extract_text="Whether to extract text content",
        extract_html="Whether to extract HTML content",
        screenshot="Whether to take a screenshot",
        javascript="JavaScript to execute on the page"
    )
    async def Visit(
        self,
        url: str,
        wait_for: Optional[str] = None,
        extract_text: bool = True,
        extract_html: bool = False,
        screenshot: bool = False,
        javascript: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Visit a webpage and extract its content.
        Supports waiting for elements, taking screenshots, and executing JavaScript.
        """
        try:
            await self._ensure_browser()
            page = await self._context.new_page()
            
            try:
                await page.goto(url, timeout=self.timeout)
                
                if wait_for:
                    await page.wait_for_selector(wait_for, timeout=self.timeout)

                result = {
                    "success": True,
                    "url": url,
                    "title": await page.title()
                }

                if extract_text:
                    result["text"] = await page.evaluate('() => document.body.innerText')

                if extract_html:
                    result["html"] = await page.content()

                if javascript:
                    result["javascript_result"] = await page.evaluate(javascript)

                if screenshot:
                    self._ensure_screenshots_dir()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"screenshot_{timestamp}.png"
                    path = str(Path(self.screenshots_dir) / filename)
                    await page.screenshot(path=path, full_page=True)
                    result["screenshot_path"] = path

                return result
            finally:
                await page.close()
        except Exception as e:
            return {"error": str(e)}
        finally:
            await self._cleanup()

    @truffle.tool(
        description="Fill and submit a web form",
        icon="edit-3"
    )
    @truffle.args(
        url="URL of the form",
        form_data="Dictionary of form field selectors and values",
        submit_button="CSS selector for the submit button",
        wait_after_submit="CSS selector to wait for after submission",
        screenshot_result="Whether to take a screenshot after submission"
    )
    async def FillForm(
        self,
        url: str,
        form_data: Dict[str, str],
        submit_button: str,
        wait_after_submit: Optional[str] = None,
        screenshot_result: bool = False
    ) -> Dict[str, Any]:
        """
        Fill and submit a web form.
        Handles text inputs, checkboxes, radio buttons, and dropdowns.
        """
        try:
            await self._ensure_browser()
            page = await self._context.new_page()
            
            try:
                await page.goto(url, timeout=self.timeout)
                
                # Fill form fields
                for selector, value in form_data.items():
                    element = await page.wait_for_selector(selector, timeout=self.timeout)
                    
                    # Get element type
                    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                    input_type = await element.evaluate('el => el.type?.toLowerCase()')
                    
                    if tag_name == "select":
                        await element.select_option(value=value)
                    elif input_type in ["checkbox", "radio"]:
                        if value.lower() in ["true", "1", "yes"]:
                            await element.check()
                        else:
                            await element.uncheck()
                    else:
                        await element.fill(value)

                # Submit form
                submit = await page.wait_for_selector(submit_button, timeout=self.timeout)
                await submit.click()

                # Wait after submission if specified
                if wait_after_submit:
                    await page.wait_for_selector(wait_after_submit, timeout=self.timeout)

                result = {
                    "success": True,
                    "url": url,
                    "title": await page.title()
                }

                if screenshot_result:
                    self._ensure_screenshots_dir()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"form_result_{timestamp}.png"
                    path = str(Path(self.screenshots_dir) / filename)
                    await page.screenshot(path=path, full_page=True)
                    result["screenshot_path"] = path

                return result
            finally:
                await page.close()
        except Exception as e:
            return {"error": str(e)}
        finally:
            await self._cleanup()

    @truffle.tool(
        description="Extract structured data from a webpage",
        icon="database"
    )
    @truffle.args(
        url="URL to extract data from",
        selectors="Dictionary of data keys and their CSS selectors",
        wait_for="CSS selector to wait for before extraction",
        extract_attributes="Dictionary of selectors and their target attributes"
    )
    async def ExtractData(
        self,
        url: str,
        selectors: Dict[str, str],
        wait_for: Optional[str] = None,
        extract_attributes: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from a webpage using CSS selectors.
        Can extract text content and specific attributes from elements.
        """
        try:
            await self._ensure_browser()
            page = await self._context.new_page()
            
            try:
                await page.goto(url, timeout=self.timeout)
                
                if wait_for:
                    await page.wait_for_selector(wait_for, timeout=self.timeout)

                result = {
                    "success": True,
                    "url": url,
                    "data": {}
                }

                # Extract text content for each selector
                for key, selector in selectors.items():
                    elements = await page.query_selector_all(selector)
                    texts = []
                    for element in elements:
                        if element:
                            texts.append(await element.inner_text())
                    result["data"][key] = texts[0] if len(texts) == 1 else texts

                # Extract specified attributes
                if extract_attributes:
                    result["attributes"] = {}
                    for selector, attribute in extract_attributes.items():
                        elements = await page.query_selector_all(selector)
                        values = []
                        for element in elements:
                            if element:
                                value = await element.get_attribute(attribute)
                                if value:
                                    values.append(value)
                        result["attributes"][selector] = values[0] if len(values) == 1 else values

                return result
            finally:
                await page.close()
        except Exception as e:
            return {"error": str(e)}
        finally:
            await self._cleanup()

    @truffle.tool(
        description="Monitor a webpage for changes",
        icon="eye"
    )
    @truffle.args(
        url="URL to monitor",
        selector="CSS selector to monitor for changes",
        interval="Monitoring interval in seconds",
        max_time="Maximum monitoring time in seconds",
        screenshot_changes="Whether to screenshot when changes are detected"
    )
    async def MonitorChanges(
        self,
        url: str,
        selector: str,
        interval: int = 60,
        max_time: int = 3600,
        screenshot_changes: bool = False
    ) -> Dict[str, Any]:
        """
        Monitor a webpage for changes in specific elements.
        Useful for tracking price changes, stock availability, etc.
        """
        try:
            await self._ensure_browser()
            page = await self._context.new_page()
            
            try:
                await page.goto(url, timeout=self.timeout)
                await page.wait_for_selector(selector, timeout=self.timeout)

                initial_content = await page.evaluate(f'() => document.querySelector("{selector}").innerText')
                changes = []
                start_time = datetime.now()

                while (datetime.now() - start_time).total_seconds() < max_time:
                    await asyncio.sleep(interval)
                    
                    try:
                        current_content = await page.evaluate(f'() => document.querySelector("{selector}").innerText')
                        
                        if current_content != initial_content:
                            change = {
                                "timestamp": datetime.now().isoformat(),
                                "old_content": initial_content,
                                "new_content": current_content
                            }

                            if screenshot_changes:
                                self._ensure_screenshots_dir()
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"change_{timestamp}.png"
                                path = str(Path(self.screenshots_dir) / filename)
                                await page.screenshot(path=path, full_page=True)
                                change["screenshot_path"] = path

                            changes.append(change)
                            initial_content = current_content

                    except Exception as e:
                        changes.append({
                            "timestamp": datetime.now().isoformat(),
                            "error": str(e)
                        })

                return {
                    "success": True,
                    "url": url,
                    "selector": selector,
                    "monitoring_duration": int((datetime.now() - start_time).total_seconds()),
                    "changes": changes
                }
            finally:
                await page.close()
        except Exception as e:
            return {"error": str(e)}
        finally:
            await self._cleanup() 