import os
import logging
import sqlite3
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.announcements",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
]

DATABASE_DIR = "database"
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE = os.path.join(DATABASE_DIR, "tokens.db")


def ensure_database():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens (
                user_id TEXT PRIMARY KEY,
                token_data BLOB
            )
            """
        )
        conn.commit()
    logger.info("Ensured the 'tokens' database and table exist.")


def save_credentials(user_id, creds):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO tokens (user_id, token_data)
            VALUES (?, ?)
            """,
            (user_id, creds.to_json()),
        )
        conn.commit()
    logger.info(f"Saved credentials for user {user_id}.")


def load_credentials(user_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT token_data FROM tokens WHERE user_id = ?
            """,
            (user_id,),
        )
        result = cursor.fetchone()
    return Credentials.from_authorized_user_info(eval(result[0])) if result else None


def get_credentials(user_id):
    creds = load_credentials(user_id)

    # If no valid credentials, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials.")
            creds.refresh(Request())
        else:
            logger.info("Starting OAuth2 flow.")
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", scopes=SCOPES
            )
            creds = flow.run_local_server(
                port=8000, access_type="offline", prompt="consent"
            )

        # Save the credentials for future use
        save_credentials(user_id, creds)

    return creds


def get_classroom_service(user_id):
    try:
        creds = get_credentials(user_id)
        return build("classroom", "v1", credentials=creds)
    except HttpError as e:
        if "redirect_uri_mismatch" in str(e):
            logger.error(
                "Redirect URI mismatch. Check your Google Cloud Console settings."
            )
        else:
            logger.error(f"Google API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to get classroom service: {e}")
        raise


def list_classrooms(user_id):
    try:
        service = get_classroom_service(user_id)
        results = service.courses().list(pageSize=10).execute()
        courses = results.get("courses", [])
        logger.info(f"Fetched {len(courses)} classrooms for user {user_id}.")
        return courses
    except HttpError as e:
        logger.error(f"Google API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to fetch classrooms: {e}")
        raise


def list_announcements_by_course(course_id, user_id):
    try:
        # Get the Google Classroom service
        service = get_classroom_service(user_id)

        # Fetch announcements for the specific course
        result = (
            service.courses().announcements().list(courseId=int(course_id)).execute()
        )
        print(
            service.courses().courseWork().list(courseId=int(course_id)).execute()
        )  # Debugging: Print the raw API response
        course_announcements = result.get("announcements", [])

        # Sort announcements by creationTime in descending order
        course_announcements.sort(key=lambda x: x.get("creationTime", ""), reverse=True)

        # List to store top 3 announcements
        announcements = []

        # Get the top 3 announcements
        for index, announcement in enumerate(course_announcements[:3], start=1):
            # Extract and format the creationTime
            creation_time = announcement.get("creationTime", "")
            posted_date = (
                datetime.fromisoformat(creation_time.replace("Z", "+00:00")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if creation_time
                else "Unknown"
            )

            # Prepare content with materials information
            announcement_text = announcement.get("text", "No content provided.")
            materials = announcement.get("materials", [])
            materials_info = []

            # Format materials if they exist
            for material in materials:
                material_type = material.get(
                    "driveFile", material.get("youtubeVideo", material.get("link", {}))
                )
                if "driveFile" in material:
                    materials_info.append(
                        f"📄 Drive File: {material['driveFile']['title']} (ID: {material['driveFile']['driveFile']['id']})"
                    )
                elif "youtubeVideo" in material:
                    materials_info.append(
                        f"🎥 YouTube Video: {material['youtubeVideo']['title']} (URL: {material['youtubeVideo']['alternateLink']})"
                    )
                elif "link" in material:
                    materials_info.append(
                        f"🔗 Link: {material['link']['title']} (URL: {material['link']['url']})"
                    )
                else:
                    materials_info.append("📦 Unknown Material Type")

            # Combine announcement text and materials
            content = announcement_text
            if materials_info:
                content += "\n\n**Materials:**\n" + "\n".join(materials_info)

            # Create announcement dictionary
            announcements.append(
                {
                    "title": f"Announcement {index}",
                    "content": content,
                    "posted_date": posted_date,
                }
            )

        if not announcements:
            logger.info(f"No announcements found for course {course_id}.")
            return []

        logger.info(
            f"Fetched {len(announcements)} announcements for course {course_id}."
        )
        return announcements

    except HttpError as e:
        logger.error(f"Google API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to fetch announcements: {e}")
        raise


def delete_credentials(user_id):
    """Delete credentials for a user."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tokens WHERE user_id = ?", (user_id,))
        conn.commit()
    logger.info(f"Deleted credentials for user {user_id}.")


# Initialize database
ensure_database()
