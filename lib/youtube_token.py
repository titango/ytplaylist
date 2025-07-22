import json
import subprocess
from typing import Tuple

from lib.file import log_message

def generate_youtube_token() -> dict:
    """
    Generates a YouTube authentication token by executing a Node.js script.

    Returns:
        dict: A dictionary containing visitor data and PO token.
    """
    log_message("Generating YouTube token")
    result = subprocess.run(
        ["node", "youtube-token-generator.js"],
        capture_output=True,
        text=True,
        check=True
    )
    data = json.loads(result.stdout)
    log_message(f"Result: {data}")
    return data
  
def po_token_verifier() -> Tuple[str, str]:
    """
    Verifies and returns YouTube visitor data and PO token.

    Returns:
        Tuple[str, str]: A tuple containing visitor data and PO token.
    """
    token_object = generate_youtube_token()
    return token_object["visitorData"], token_object["poToken"]