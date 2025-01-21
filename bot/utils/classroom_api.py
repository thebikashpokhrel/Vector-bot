import datetime
from bot.utils.google_auth import get_credentials, logger
from googleapiclient.discovery import build
from dateutil import parser


# Use the Google Classroom Service
def get_classroom_service(client_id):
    try:
        creds = get_credentials(client_id)

        if isinstance(creds, dict) and "auth_url" in creds:
            return creds["auth_url"]  # Return the auth URL for the user to authorize
        elif isinstance(creds, dict) and "error" in creds:
            logger.error(f"Error in credentials: {creds['error']}")
            return {"error": creds["error"]}
        elif creds:
            # If valid credentials are found, build the Classroom service
            return build("classroom", "v1", credentials=creds)
        else:
            logger.error("No valid credentials found.")
            return {"error": "No valid credentials found. Please authorize first."}

    except Exception as e:
        logger.error(f"Failed to get classroom service: {e}")
        return {"error": "Failed to get classroom service. Please try again later."}


# List all the classrooms
def list_classrooms(client_id):
    try:
        service = get_classroom_service(client_id)

        # Check if the response contains an error or auth_url
        if isinstance(service, dict) and "error" in service:
            return service  # Return the error message
        elif isinstance(service, str):
            return {"error": "Please authorize first to access classrooms."}

        # Fetch the list of classrooms
        results = service.courses().list(pageSize=10).execute()
        courses = results.get("courses", [])
        logger.info(f"Fetched {len(courses)} classrooms for user {client_id}")
        return courses

    except Exception as e:
        logger.error(f"Failed to fetch classrooms: {e}")
        return {"error": "Failed to fetch classrooms. Please try again later."}


# List Top 3 announcements for each course
def list_announcements(course_id, client_id):
    try:
        service = get_classroom_service(client_id)
        if isinstance(service, dict) and "error" in service:
            return service
        elif isinstance(service, str):
            return {"error": "Please authorize first to access Google Classroom."}

        # Fetch announcements and coursework materials
        announcements = (
            service.courses()
            .announcements()
            .list(courseId=int(course_id), pageSize=3)
            .execute()
        ).get("announcements", [])

        coursework_materials = (
            service.courses()
            .courseWorkMaterials()
            .list(courseId=int(course_id), pageSize=3)
            .execute()
        ).get("courseWorkMaterial", [])

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
                parser.isoparse(creation_time.replace("Z", "+00:00")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if creation_time
                else "Unknown"
            )

            if item["type"] == "announcement":
                content = item.get("text", "No content provided.")
                description = item.get("description")
                materials = item.get("materials", [])
            elif item["type"] == "courseWorkMaterial":
                content = item.get("title", "No title provided.")
                description = item.get("description")
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
                    "description": description,
                    "posted_date": posted_date,
                    "type": item["type"],
                }
            )

        if not top_items:
            logger.info(f"No items found for course {course_id}.")
            return {"error": "No items found for this course."}

        logger.info(f"Fetched {len(top_items)} top items for course {course_id}.")
        return top_items
    except Exception as e:
        logger.error(f"Failed to fetch items: {e}")
        return {"error": "Failed to fetch items. Please try again later."}
