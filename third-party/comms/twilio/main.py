import os
from typing import Optional, Dict, Any, List
import truffle
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class TwilioTool:
    def __init__(self):
        self.client = truffle.TruffleClient()
        
        # Initialize Twilio credentials from environment variables
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.default_from = os.getenv("TWILIO_DEFAULT_FROM")
        self.messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
        
        if not all([self.account_sid, self.auth_token]):
            raise ValueError("Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables")
        
        if not any([self.default_from, self.messaging_service_sid]):
            raise ValueError("Please set either TWILIO_DEFAULT_FROM or TWILIO_MESSAGING_SERVICE_SID environment variable")
        
        # Initialize Twilio client
        self.twilio_client = Client(self.account_sid, self.auth_token)
    
    @truffle.tool(
        description="Send an SMS message",
        icon="message"
    )
    @truffle.args(
        to="Recipient phone number (E.164 format: +1234567890)",
        body="Message content",
        from_number="Optional: Override default sender number",
        media_urls="Optional: List of media URLs to send as MMS"
    )
    def SendMessage(
        self,
        to: str,
        body: str,
        from_number: Optional[str] = None,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sends an SMS/MMS message using Twilio.
        Returns information about the sent message.
        """
        try:
            # Validate phone number format
            if not to.startswith("+"):
                return {
                    "success": False,
                    "error": "Phone number must be in E.164 format (e.g., +1234567890)"
                }
            
            # Prepare message parameters
            params = {
                "to": to,
                "body": body
            }
            
            # Add sender information
            if from_number:
                params["from_"] = from_number
            elif self.default_from:
                params["from_"] = self.default_from
            else:
                params["messaging_service_sid"] = self.messaging_service_sid
            
            # Add media URLs if provided
            if media_urls:
                params["media_url"] = media_urls
            
            # Send the message
            message = self.twilio_client.messages.create(**params)
            
            return {
                "success": True,
                "message_sid": message.sid,
                "to": message.to,
                "from": message.from_,
                "body": message.body,
                "status": message.status,
                "direction": message.direction,
                "date_created": str(message.date_created),
                "media_urls": message.media_url if hasattr(message, 'media_url') else None
            }
            
        except TwilioRestException as e:
            return {
                "success": False,
                "error": f"Twilio error: {str(e)}",
                "code": e.code,
                "status": e.status
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @truffle.tool(
        description="Send a bulk message to multiple recipients",
        icon="messages"
    )
    @truffle.args(
        to_numbers="List of recipient phone numbers (E.164 format: +1234567890)",
        body="Message content",
        media_urls="Optional: List of media URLs to send as MMS"
    )
    def SendBulkMessages(
        self,
        to_numbers: List[str],
        body: str,
        media_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sends the same message to multiple recipients.
        Returns information about all sent messages.
        """
        try:
            results = []
            failed = []
            
            for to_number in to_numbers:
                result = self.SendMessage(
                    to=to_number,
                    body=body,
                    media_urls=media_urls
                )
                
                if result["success"]:
                    results.append(result)
                else:
                    failed.append({
                        "number": to_number,
                        "error": result["error"]
                    })
            
            return {
                "success": True,
                "total_recipients": len(to_numbers),
                "successful_sends": len(results),
                "failed_sends": len(failed),
                "results": results,
                "failures": failed
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    app = truffle.TruffleApp(TwilioTool())
    app.launch() 