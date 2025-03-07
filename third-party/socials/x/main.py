import os
from typing import Optional, Dict, Any, List
import truffle
import tweepy

class XTool:
    def __init__(self):
        self.client = truffle.TruffleClient()
        
        # Initialize X API credentials from environment variables
        self.api_key = os.getenv("X_API_KEY")
        self.api_secret = os.getenv("X_API_SECRET")
        self.access_token = os.getenv("X_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
        
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise ValueError("Please set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, and X_ACCESS_TOKEN_SECRET environment variables")
        
        # Initialize X client
        auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        self.x_client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
    
    @truffle.tool(
        description="Post a new tweet",
        icon="tweet"
    )
    @truffle.args(
        text="The text content of the tweet",
        reply_to="Optional: Tweet ID to reply to",
        quote="Optional: Tweet URL to quote"
    )
    def PostTweet(
        self,
        text: str,
        reply_to: Optional[str] = None,
        quote: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Posts a new tweet, optionally as a reply or quote tweet.
        Returns information about the posted tweet.
        """
        try:
            # Validate tweet length (X's current limit is 280 characters)
            if len(text) > 280:
                return {
                    "success": False,
                    "error": "Tweet exceeds 280 character limit"
                }
            
            # Prepare tweet parameters
            params = {
                "text": text
            }
            
            # Add reply_to if provided
            if reply_to:
                params["in_reply_to_tweet_id"] = reply_to
            
            # Add quote tweet if provided
            if quote:
                # Extract tweet ID from URL if needed
                if "twitter.com" in quote or "x.com" in quote:
                    quote_id = quote.split("/")[-1]
                    params["quote_tweet_id"] = quote_id
                else:
                    params["quote_tweet_id"] = quote
            
            # Post the tweet
            response = self.x_client.create_tweet(**params)
            
            if response and response.data:
                tweet_data = response.data
                return {
                    "success": True,
                    "tweet_id": tweet_data["id"],
                    "text": text,
                    "url": f"https://twitter.com/i/web/status/{tweet_data['id']}"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to post tweet - no response data"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    app = truffle.TruffleApp(XTool())
    app.launch() 