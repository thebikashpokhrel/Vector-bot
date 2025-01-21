import os
import logging
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import base64
import json
import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google API scopes and backend URL
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.announcements",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
]
BACKEND_URL = "http://localhost:8001"


# Load token from backend and convert it to Credentials Object
def load_credentials(client_id):
    try:
        # Fetch token data from the backend
        response = requests.get(
            f"{BACKEND_URL}/classroom/check/", params={"clientid": client_id}
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)

        # Parse the JSON response
        data = response.json()

        # Check if the response contains an error
        if "error" in data:
            logger.error(f"Error from backend: {data['error']}")
            return None

        # Extract the token from the response
        token = data.get("token")
        if not token:
            logger.error(f"Token data not found for client id: {client_id}")
            return None

        # Convert token to JSON and return Credentials object
        token = json.loads(token)
        creds = Credentials.from_authorized_user_info(token)
        return creds

    except requests.RequestException as e:
        logger.error(f"Failed to load credentials: {e}")
        return None
    except ValueError as e:
        logger.error(f"Failed to parse token data: {e}")
        return None


# Delete the token of a particular clientid
def delete_token(client_id):
    try:
        response = requests.delete(
            f"{BACKEND_URL}/classroom/unsubscribe", params={"clientid": client_id}
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx, 5xx)

        # Parse the JSON response
        data = response.json()

        # Check if the response contains an error
        if "error" in data:
            logger.error(f"Error from backend: {data['error']}")
            return {"error": data["error"]}

        # Return the success message
        logger.info(f"Deleted token for client id: {client_id}")
        return data

    except requests.RequestException as e:
        logger.error(f"Failed to delete token: {e}")
        return {"error": f"Failed to delete token:{e.response.json()["error"]}"}


# Get the credentials for a particular user if they exist, otherwise start the OAuth flow and return the auth URL
def get_credentials(client_id):
    creds = load_credentials(client_id)
    if creds and creds.valid:
        if creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials.")
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                return {"error": "Failed to refresh credentials. Please reauthorize."}
        return creds
    else:
        # If no valid credentials, initiate the OAuth2 flow
        logger.info("Starting OAuth2 flow")
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json",
            scopes=SCOPES,
            redirect_uri=f"{BACKEND_URL}/classroom/subscribe",
        )

        state_data = {"clientid": client_id}
        encoded_state = base64.urlsafe_b64encode(
            json.dumps(state_data).encode()
        ).decode()
        auth_url, _ = flow.authorization_url(prompt="consent", state=encoded_state)
        logger.info(f"Authorization URL generated for user {client_id}")
        return {"auth_url": auth_url}
