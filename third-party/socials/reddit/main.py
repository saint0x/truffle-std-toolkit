import os
import praw
from typing import Optional, Dict, Any, List
import truffle

class RedditTool:
    def __init__(self):
        self.client = truffle.TruffleClient()
        # Initialize Reddit client using environment variables
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "STDKIT/1.0")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables")
        
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent
        )
    
    @truffle.tool(
        description="Search Reddit for posts",
        icon="search"
    )
    @truffle.args(
        query="Search query",
        subreddit="Optional: Specific subreddit to search in",
        limit="Optional: Maximum number of results (1-100)",
        sort="Optional: Sort method (relevance, hot, top, new, comments)"
    )
    def SearchReddit(
        self,
        query: str,
        subreddit: Optional[str] = None,
        limit: int = 10,
        sort: str = "relevance"
    ) -> Dict[str, Any]:
        """
        Search Reddit for posts matching the query.
        Returns a list of posts with their details.
        """
        try:
            # Validate limit
            limit = max(1, min(100, limit))
            
            # Validate sort method
            valid_sorts = ["relevance", "hot", "top", "new", "comments"]
            if sort not in valid_sorts:
                return {
                    "success": False,
                    "error": f"Invalid sort method. Must be one of: {', '.join(valid_sorts)}"
                }
            
            # Perform search
            if subreddit:
                search_results = self.reddit.subreddit(subreddit).search(query, limit=limit, sort=sort)
            else:
                search_results = self.reddit.subreddit("all").search(query, limit=limit, sort=sort)
            
            # Format results
            posts = []
            for post in search_results:
                posts.append({
                    "title": post.title,
                    "subreddit": post.subreddit.display_name,
                    "score": post.score,
                    "url": post.url,
                    "permalink": f"https://reddit.com{post.permalink}",
                    "created_utc": post.created_utc,
                    "num_comments": post.num_comments,
                    "author": str(post.author),
                    "is_self": post.is_self,
                    "selftext": post.selftext if post.is_self else None
                })
            
            return {
                "success": True,
                "query": query,
                "subreddit": subreddit or "all",
                "sort": sort,
                "total_results": len(posts),
                "posts": posts
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @truffle.tool(
        description="Get trending subreddits",
        icon="trending"
    )
    @truffle.args(
        limit="Optional: Maximum number of subreddits to return (1-100)"
    )
    def GetTrendingSubreddits(
        self,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get a list of trending subreddits.
        Returns subreddit information including subscriber count and description.
        """
        try:
            # Validate limit
            limit = max(1, min(100, limit))
            
            # Get trending subreddits
            trending = self.reddit.subreddits.trending(limit=limit)
            
            # Format results
            subreddits = []
            for subreddit in trending:
                subreddits.append({
                    "name": subreddit.display_name,
                    "title": subreddit.title,
                    "subscribers": subreddit.subscribers,
                    "description": subreddit.public_description,
                    "url": f"https://reddit.com/r/{subreddit.display_name}",
                    "created_utc": subreddit.created_utc,
                    "over18": subreddit.over18
                })
            
            return {
                "success": True,
                "total_subreddits": len(subreddits),
                "subreddits": subreddits
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @truffle.tool(
        description="Get hot posts from a subreddit",
        icon="fire"
    )
    @truffle.args(
        subreddit="Name of the subreddit",
        limit="Optional: Maximum number of posts to return (1-100)"
    )
    def GetHotPosts(
        self,
        subreddit: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get hot posts from a specific subreddit.
        Returns a list of hot posts with their details.
        """
        try:
            # Validate limit
            limit = max(1, min(100, limit))
            
            # Get hot posts
            hot_posts = self.reddit.subreddit(subreddit).hot(limit=limit)
            
            # Format results
            posts = []
            for post in hot_posts:
                posts.append({
                    "title": post.title,
                    "score": post.score,
                    "url": post.url,
                    "permalink": f"https://reddit.com{post.permalink}",
                    "created_utc": post.created_utc,
                    "num_comments": post.num_comments,
                    "author": str(post.author),
                    "is_self": post.is_self,
                    "selftext": post.selftext if post.is_self else None
                })
            
            return {
                "success": True,
                "subreddit": subreddit,
                "total_posts": len(posts),
                "posts": posts
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    app = truffle.TruffleApp(RedditTool())
    app.launch() 