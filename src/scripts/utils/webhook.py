import os
import requests

WEBHOOK_AVATAR = "https://cdn.discordapp.com/icons/1280127901852893244/ea65cd62d0824f7aab1f0bf751364818.webp"
WEBHOOK_USERNAME = "WerZatSong"

def post_webhook(url: str, content: str, file_path: str = None) -> bool:
    """
    Send a message (and optionally a text file) to a Discord webhook.
    Returns True if Discord returned HTTP 204 No Content, False otherwise.
    """
    try:
        if file_path and os.path.exists(file_path):
            # Prepare multipart/form-data payload
            with open(file_path, "rb") as f:
                files = {
                    # The “file” field will contain the file bytes
                    "file": (os.path.basename(file_path), f, "text/plain")
                }
                data = {
                    "content": f"`{content}`",  # wrap content in backticks
                    "username": WEBHOOK_USERNAME,
                    "avatar_url": WEBHOOK_AVATAR,
                }
                response = requests.post(url, data=data, files=files)
        else:
            # Send JSON payload
            json_payload = {
                "content": content,
                "username": WEBHOOK_USERNAME,
                "avatar_url": WEBHOOK_AVATAR,
            }
            response = requests.post(url, json=json_payload)

        return response.status_code == 204
    except Exception(BaseException):
        return False
