import aiohttp, json, base64, re, asyncio
from functools import lru_cache
import time
import os

# This should be configured in your bot's environment variables
X_ACCESS_TOKEN = os.environ.get('X_ACCESS_TOKEN', "eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTU0ODk2NzExLCJvcmdJZCI6Nzk1NjAyLCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTc2NTE4NjkxODUiLCJuYW1lIjoicm9reSIsImVtYWlsIjoiaHVtbWluZ2JpcmQ4MTY1NEBtYWlsc2hhbi5jb20iLCJpc0ZpcnN0TG9naW4iOnRydWUsImRlZmF1bHRMYW5ndWFnZSI6IjJlOGVlMGMzYjM5MjNlZTZhMTU5ZDgzNWFmYjZjYjYxIiwiaWF0IjoxNzUxMDkxNDE4LCJleHAiOjE3NTE2OTYyMTh9.g6qaHUAeRY3etEl2GG6kBjDwIX1wnEPHKRcqyFOaqh6enfoIkf6Pn-JNp2KjcPTjF")

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

async def fetch_folder_contents(session, encoded_payload, folder_id):
    url = f"https://api.classplusapp.com/v2/course/preview/content/list/{encoded_payload}?folderId={folder_id}&limit=200&offset=0"
    try:
        async with session.get(url, headers=HEADERS) as resp:
            resp.raise_for_status()
            return folder_id, await resp.json() # Return folder_id along with data
    except (aiohttp.ClientError, json.JSONDecodeError) as e:
        print(f"Worker failed for folder {folder_id}: {e}")
        return folder_id, None

async def get_course_content_fast(orgid, courseid):
    """Crawls the entire course content in a single, fast pass."""
    print(f"Starting fast content crawl for course {courseid}")
    start_time = time.time()
    encoded_payload = encode_payload(orgid, courseid)
    
    root = {'id': 0, 'name': 'Root', 'subfolders': [], 'videos': [], 'parent_id': None, 'path': ''}
    all_folders_data = {0: root} # Map folder_id to its dictionary representation

    folders_to_fetch = {0} # Start with the root folder ID
    fetched_folders = set()

    async with aiohttp.ClientSession() as session:
        while folders_to_fetch:
            current_batch_ids = list(folders_to_fetch)
            folders_to_fetch.clear()

            tasks = [fetch_folder_contents(session, encoded_payload, fid) for fid in current_batch_ids]
            results = await asyncio.gather(*tasks)

            for folder_id, data in results:
                if not data or data.get("status") != "success":
                    continue

                fetched_folders.add(folder_id)
                items = sorted(data.get("data", []), key=lambda x: x.get("sequenceNo", 0))

                current_folder_dict = all_folders_data[folder_id]

                for item in items:
                    if item.get("contentType") == 1:  # It's a folder
                        sub_folder_id = item.get("id")
                        if sub_folder_id not in all_folders_data: # Avoid re-adding existing folders
                            new_folder = {
                                'id': sub_folder_id,
                                'name': item.get("name", "Unnamed"),
                                'subfolders': [],
                                'videos': [],
                                'parent_id': folder_id,
                                'path': os.path.join(current_folder_dict['path'], item.get("name", "Unnamed"))
                            }
                            current_folder_dict['subfolders'].append(new_folder)
                            all_folders_data[sub_folder_id] = new_folder
                            folders_to_fetch.add(sub_folder_id) # Add to next batch to fetch
                    elif item.get("thumbnailUrl"): # It's a video
                        video_url = transform_thumbnail_to_video(item.get("thumbnailUrl"))
                        if video_url:
                            current_folder_dict['videos'].append({
                                'name': item.get("name", "Unnamed"),
                                'vid_url': video_url,
                                'folder_path': current_folder_dict['path'] # Store the full path
                            })
    
    print(f"Content crawl completed in {time.time() - start_time:.2f} seconds.")
    return root

async def get_videos_from_folder_id(folder_structure, folder_id):
    """
    Recursively gets all videos from a specific folder ID using the cached structure.
    """
    all_videos = []
    
    def find_folder(structure, target_id):
        if structure['id'] == target_id:
            return structure
        for subfolder in structure['subfolders']:
            found = find_folder(subfolder, target_id)
            if found:
                return found
        return None

    folder_to_search = find_folder(folder_structure, folder_id)

    def collect_videos(folder):
        all_videos.extend(folder['videos'])
        for subfolder in folder['subfolders']:
            collect_videos(subfolder)

    if folder_to_search:
        collect_videos(folder_to_search)
        
    return all_videos

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
