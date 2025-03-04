import os
import json
from typing import Optional, Dict, List, Union
import requests
from datetime import datetime
import truffle

class WebSearchTool:
    """Tool for performing web searches using Serper.dev API."""
    
    def __init__(self):
        self.client = truffle.TruffleClient()
        self.api_key = os.getenv("SERPER_API_KEY")
        self.base_url = "https://google.serper.dev"
        self.result_limit = int(os.getenv("SEARCH_RESULT_LIMIT", "10"))
        self.timeout = int(os.getenv("SEARCH_TIMEOUT", "30"))

    def _make_request(self, endpoint: str, payload: dict) -> dict:
        """Make a request to the Serper API."""
        if not self.api_key:
            return {"error": "SERPER_API_KEY environment variable not set"}

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

    @truffle.tool(
        description="Perform a web search using Google Search API",
        icon="search"
    )
    @truffle.args(
        query="Search query string",
        result_type="Type of results to return (web, news, images, or places)",
        country="Two-letter country code for localized results",
        language="Two-letter language code for results",
        auto_correct="Whether to auto-correct spelling mistakes"
    )
    def Search(
        self,
        query: str,
        result_type: str = "web",
        country: Optional[str] = None,
        language: Optional[str] = None,
        auto_correct: bool = True
    ) -> Dict[str, Union[bool, List[Dict[str, str]]]]:
        """
        Perform a web search and return structured results.
        Supports different types of searches: web, news, images, places.
        """
        result_type = result_type.lower()
        if result_type not in ["web", "news", "images", "places"]:
            return {"error": "Invalid result_type. Must be one of: web, news, images, places"}

        payload = {
            "q": query,
            "num": self.result_limit,
            "auto_correct": auto_correct
        }
        
        if country:
            payload["gl"] = country.upper()
        if language:
            payload["hl"] = language.lower()

        response = self._make_request(result_type, payload)
        
        if "error" in response:
            return response

        try:
            results = []
            
            if result_type == "web":
                for item in response.get("organic", []):
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "position": item.get("position", 0),
                        "domain": item.get("domain", "")
                    })
            
            elif result_type == "news":
                for item in response.get("news", []):
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "date": item.get("date", ""),
                        "source": item.get("source", "")
                    })
            
            elif result_type == "images":
                for item in response.get("images", []):
                    results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "image_url": item.get("imageUrl", ""),
                        "source_url": item.get("sourceUrl", ""),
                        "size": item.get("size", "")
                    })
            
            elif result_type == "places":
                for item in response.get("places", []):
                    results.append({
                        "title": item.get("title", ""),
                        "address": item.get("address", ""),
                        "rating": item.get("rating", 0),
                        "reviews": item.get("reviews", 0),
                        "type": item.get("type", ""),
                        "phone": item.get("phone", ""),
                        "website": item.get("website", "")
                    })

            return {
                "success": True,
                "query": query,
                "result_type": result_type,
                "results": results,
                "total_results": len(results)
            }
        except Exception as e:
            return {"error": f"Failed to parse results: {str(e)}"}

    @truffle.tool(
        description="Search for recent news articles",
        icon="newspaper"
    )
    @truffle.args(
        query="Search query string",
        hours_ago="Only return articles from the last N hours",
        country="Two-letter country code for localized results",
        language="Two-letter language code for results"
    )
    def SearchNews(
        self,
        query: str,
        hours_ago: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Union[bool, List[Dict[str, str]]]]:
        """
        Search specifically for news articles with time filtering.
        """
        results = self.Search(
            query=query,
            result_type="news",
            country=country,
            language=language
        )
        
        if not results.get("success", False):
            return results

        if hours_ago is not None:
            # Filter results by time
            current_time = datetime.now()
            filtered_results = []
            
            for item in results["results"]:
                try:
                    article_date = datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S")
                    hours_difference = (current_time - article_date).total_seconds() / 3600
                    
                    if hours_difference <= hours_ago:
                        filtered_results.append(item)
                except (ValueError, KeyError):
                    continue

            results["results"] = filtered_results
            results["total_results"] = len(filtered_results)

        return results

    @truffle.tool(
        description="Search for code-related information",
        icon="code-search"
    )
    @truffle.args(
        query="Search query string",
        sites="List of technical sites to search (e.g., stackoverflow, github)",
        language="Programming language to focus on"
    )
    def SearchCode(
        self,
        query: str,
        sites: Optional[List[str]] = None,
        language: Optional[str] = None
    ) -> Dict[str, Union[bool, List[Dict[str, str]]]]:
        """
        Specialized search for programming and technical information.
        Focuses on developer-specific sites and documentation.
        """
        # Default technical sites if none specified
        default_sites = ["stackoverflow.com", "github.com", "dev.to", "medium.com"]
        sites = sites or default_sites

        # Build the query with site-specific searches
        site_query = " OR ".join(f"site:{site}" for site in sites)
        full_query = f"{query} ({site_query})"
        
        if language:
            full_query = f"{language} {full_query}"

        return self.Search(
            query=full_query,
            result_type="web",
            auto_correct=True
        ) 