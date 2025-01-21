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


def load_credentials(user_id):
    try:
        # Fetch token data from the backend
        response = requests.get(
            f"{BACKEND_URL}/classroom/check/", params={"clientid": user_id}
        )
        response.raise_for_status()  # Ensure the request was successful

        creds = response.json().get("token")
        if not creds:
            logger.error("Token data not found")
            return None

        return json.loads(creds)
    except requests.RequestException as e:
        logger.error(f"Failed to load credentials: {e}")
        return None
    except ValueError as e:
        logger.error(f"Failed to parse token data: {e}")
        return None


def delete_credentials(user_id):
    try:
        response = requests.delete(
            f"{BACKEND_URL}/classroom/unsubscribe", params={"clientid": user_id}
        )
        response.raise_for_status()
        logger.info(f"Deleted credentials for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to delete credentials: {e}")
        raise


def get_credentials(user_id):
    creds = load_credentials(user_id)
    if creds:
        # If valid credentials are found, return them
        logger.info(f"Loaded valid credentials for user {user_id}")
        return {"data": creds, "type": "CRED"}

    # If no valid credentials, initiate the OAuth2 flow
    logger.info("Starting OAuth2 flow")
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri="http://localhost:8001/classroom/subscribe",
    )
    state_data = {"user_id": user_id}
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
    auth_url, _ = flow.authorization_url(prompt="consent", state=encoded_state)

    logger.info(f"Authorization URL generated for user {user_id}")
    return {"data": auth_url, "type": "AUTH"}


def get_classroom_service(user_id):
    try:
        creds = get_credentials(user_id)
        creds = Credentials.from_authorized_user_info(creds["data"])
        return build("classroom", "v1", credentials=creds)
    except Exception as e:
        logger.error(f"Failed to get classroom service: {e}")
        raise


def list_classrooms(user_id):
    try:
        service = get_classroom_service(user_id)
        results = service.courses().list(pageSize=10).execute()
        courses = results.get("courses", [])
        logger.info(f"Fetched {len(courses)} classrooms for user {user_id}")
        return courses
    except Exception as e:
        logger.error(f"Failed to fetch classrooms: {e}")
        raise


from googleapiclient.errors import HttpError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def list_announcements_by_course(course_id, user_id, username):
    """List announcements and coursework materials for a course."""
    try:
        # Get the Google Classroom service
        service = get_classroom_service(user_id, username)

        # Check if the response contains an error or auth_url
        if isinstance(service, dict) and "error" in service:
            return service  # Return the error message
        elif isinstance(service, str):
            return {"error": "Please authorize first to access Google Classroom."}

        # Fetch announcements and coursework materials
        announcements = (
            service.courses().announcements().list(courseId=int(course_id)).execute()
        ).get("announcements", [])

        coursework_materials = (
            service.courses()
            .courseWorkMaterials()
            .list(courseId=int(course_id))
            .execute()
        ).get("courseWorkMaterial", [])

        # Combine and sort items
        all_items = []
        for item in announcements:
            item["type"] = "announcement"
            all_items.append(item)
        for item in coursework_materials:
            item["type"] = "courseWorkMaterial"
            all_items.append(item)

        all_items.sort(key=lambda x: x.get("creationTime", ""), reverse=True)

        # Format top 3 items
        top_items = []
        for index, item in enumerate(all_items[:3], start=1):
            creation_time = item.get("creationTime", "")
            posted_date = (
                datetime.fromisoformat(creation_time.replace("Z", "+00:00")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if creation_time
                else "Unknown"
            )

            if item["type"] == "announcement":
                content = item.get("text", "No content provided.")
                materials = item.get("materials", [])
            elif item["type"] == "courseWorkMaterial":
                content = item.get("title", "No title provided.")
                materials = item.get("materials", [])

            materials_info = []
            for material in materials:
                try:
                    if "driveFile" in material:
                        drive_file = material["driveFile"]
                        title = drive_file.get("title", "Untitled")
                        file_id = drive_file.get("driveFile", {}).get(
                            "id", "Unknown ID"
                        )
                        drive_url = f"https://drive.google.com/file/d/{file_id}/view"
                        materials_info.append(
                            f"📄 Drive File: {title} (URL: {drive_url})"
                        )
                    elif "youtubeVideo" in material:
                        youtube_video = material["youtubeVideo"]
                        title = youtube_video.get("title", "Untitled")
                        url = youtube_video.get("alternateLink", "Unknown URL")
                        materials_info.append(f"🎥 YouTube Video: {title} (URL: {url})")
                    elif "link" in material:
                        link = material["link"]
                        title = link.get("title", "Untitled")
                        url = link.get("url", "Unknown URL")
                        materials_info.append(f"🔗 Link: {title} (URL: {url})")
                    else:
                        materials_info.append("📦 Unknown Material Type")
                except Exception as e:
                    logger.error(f"Failed to process material: {e}")
                    logger.debug(f"Material data: {material}")

            if materials_info:
                content += "\n**Materials:**\n" + "\n".join(materials_info)

            top_items.append(
                {
                    "title": f"{item['type'].capitalize()} {index}",
                    "content": content,
                    "posted_date": posted_date,
                    "type": item["type"],
                }
            )

        if not top_items:
            logger.info(f"No items found for course {course_id}.")
            return {"error": "No items found for this course."}

        logger.info(f"Fetched {len(top_items)} top items for course {course_id}.")
        return top_items

    except HttpError as e:
        logger.error(f"Google API error: {e}")
        return {"error": f"Google API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Failed to fetch items: {e}")
        return {"error": "Failed to fetch items. Please try again later."}
