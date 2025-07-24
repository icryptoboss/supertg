import aiohttp, json, base64, re
from functools import lru_cache
import time
import os

# ------------------- 🔒 Classplus Token -------------------
# This should be configured in your bot's environment variables
X_ACCESS_TOKEN = os.environ.get('X_ACCESS_TOKEN', "eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTU0ODk2NzExLCJvcmdJZCI6Nzk1NjAyLCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTc2NTE4NjkxODUiLCJuYW1lIjoicm9reSIsImVtYWlsIjoiaHVtbWluZ2JpcmQ4MTY1NEBtYWlsc2hhbi5jb20iLCJpc0ZpcnN0TG9naW4iOnRydWUsImRlZmF1bHRMYW5ndWFnZSI6IkVOIiwiY291bnRyeUNvZGUiOiJJTiIsImlzSW50ZXJuYXRpb25hbCI6MCwiaXNEaXkiOnRydWUsImxvZ2luVmlhIjoiT3RwIiwiZmluZ2VycHJpbnRJZCI6IjJlOGVlMGMzYjM5MjNlZTZhMTU5ZDgzNWFmYjZjYjYxIiwiaWF0IjoxNzUxMDkxNDE4LCJleHAiOjE3NTE2OTYyMTh9.g6qaHUAeRY3etEl2GG6kBjDwIX1wnEPHKRcqyFOaqh6enfoIkf6Pn-JNnKjcPTjF")

HEADERS = {
    "x-access-token": X_ACCESS_TOKEN,
    "user-agent": "Mobile/15.2",
    "content-type": "application/json"
}

async def get_org_id(org_code):
    url = f"https://{org_code}.courses.store/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as res:
                res.raise_for_status()
                text = await res.text()
                if res.status == 200 and "orgId" in text:
                    start = text.find('"orgId":') + len('"orgId":')
                    end = text.find(",", start)
                    return int(text[start:end])
    except aiohttp.ClientError as e:
        print(f"Error fetching org ID for {org_code}: {e}")
        return None

async def get_course_list(org_id):
    if not X_ACCESS_TOKEN:
        raise ValueError("X_ACCESS_TOKEN is not set.")

    payload = base64.b64encode(json.dumps({
        "orgId": org_id,
        "tutorId": None,
        "categoryId": None
    }).encode()).decode()

    url = f"https://api.classplusapp.com/v2/course/preview/similar/{payload}?filterId=[1]&sortId=[7]&limit=500&offset=0"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS) as res:
                res.raise_for_status()
                data = await res.json()
                return data.get("data", {}).get("coursesData", [])
    except aiohttp.ClientError as e:
        print(f"Error fetching course list: {e}")
        return []
    except json.JSONDecodeError:
        print("Failed to decode JSON from course list response.")
        return []

def encode_payload(orgid, courseid):
    payload = {
        "courseId": str(courseid),
        "tutorId": None,
        "orgId": int(orgid),
        "categoryId": None
    }
    return base64.b64encode(json.dumps(payload).encode()).decode()

async def fetch_folder_contents(encoded_payload, folder_id):
    url = f"https://api.classplusapp.com/v2/course/preview/content/list/{encoded_payload}?folderId={folder_id}&limit=200&offset=0"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS) as resp:
                resp.raise_for_status()
                return await resp.json()
    except aiohttp.ClientError as e:
        print(f"Error fetching folder contents: {e}")
        return {}
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from folder contents response for folder_id {folder_id}.")
        return {}

async def get_all_content(orgid, courseid):
    """
    Crawls all folders and videos for a given course and returns them.
    """
    print(f"Starting content crawl for course {courseid}")
    start_time = time.time()

    all_content = []
    encoded_payload = encode_payload(orgid, courseid)

    # A queue to manage folders to visit: (folder_id, folder_path_string)
    queue = [(0, "")]  # Start with root folder (ID 0)

    while queue:
        current_folder_id, current_path = queue.pop(0)

        data = await fetch_folder_contents(encoded_payload, current_folder_id)

        if data.get("status") != "success":
            print(f"Failed to fetch content for folder ID {current_folder_id}")
            continue

        # Sort items by sequence number before processing
        items = sorted(data.get("data", []), key=lambda x: x.get("sequenceNo", 0))

        for item in items:
            item_name = item.get("name", "Unnamed")

            if item.get("contentType") == 1:  # It's a folder
                sub_folder_id = item.get("id")
                new_path = f"{current_path}/{item_name}" if current_path else item_name
                queue.append((sub_folder_id, new_path))

            elif item.get("thumbnailUrl"):  # It's a video
                video_url = transform_thumbnail_to_video(item.get("thumbnailUrl"))
                if video_url:
                    all_content.append({
                        "folder": current_path,
                        "name": item_name,
                        "vid_url": video_url,
                    })

    end_time = time.time()
    print(f"Content crawl completed in {end_time - start_time:.2f} seconds. Found {len(all_content)} videos.")
    return all_content

@lru_cache(maxsize=1000)
def transform_thumbnail_to_video(url_val):
    if not url_val:
        return None

    # This logic is specific and kept as is from the original file
    if "media-cdn.classplusapp.com/tencent/" in url_val:
        return url_val.rsplit('/', 1)[0] + "/master.m3u8"
    elif "media-cdn.classplusapp.com" in url_val and url_val.endswith('.jpg'):
        identifier = url_val.split('/')[-3]
        return f'https://media-cdn.classplusapp.com/alisg-cdn-a.classplusapp.com/{identifier}/master.m3u8'
    elif "tencdn.classplusapp.com" in url_val and url_val.endswith('.jpg'):
        identifier = url_val.split('/')[-2]
        return f'https://media-cdn.classplusapp.com/tencent/{identifier}/master.m3u8'
    elif "4b06bf8d61c41f8310af9b2624459378203740932b456b07fcf817b737fbae27" in url_val and url_val.endswith('.jpeg'):
        video_id = url_val.split('/')[-1].split('.')[0]
        return f'https://media-cdn.classplusapp.com/alisg-cdn-a.classplusapp.com/b08bad9ff8d969639b2e43d5769342cc62b510c4345d2f7f153bec53be84fe35/{video_id}/master.m3u8'
    elif "cpvideocdn.testbook.com" in url_val and url_val.endswith('.png'):
        match = re.search(r'/streams/([a-f0-9]{24})/', url_val)
        video_id = match.group(1) if match else url_val.split('/')[-2]
        return f'https://cpvod.testbook.com/{video_id}/playlist.m3u8'
    elif "media-cdn.classplusapp.com/drm/" in url_val and url_val.endswith('.png'):
        video_id = url_val.split('/')[-3]
        return f'https://media-cdn.classplusapp.com/drm/{video_id}/playlist.m3u8'
    elif "https://media-cdn.classplusapp.com" in url_val and any(x in url_val for x in ["cc/", "lc/", "uc/", "dy/"]) and url_val.endswith('.png'):
        return url_val.replace('thumbnail.png', 'master.m3u8')
    elif "https://tb-video.classplusapp.com" in url_val and url_val.endswith('.jpg'):
        video_id = url_val.split('/')[-1].split('.')[0]
        return f'https://tb-video.classplusapp.com/{video_id}/master.m3u8'
    return None
    
