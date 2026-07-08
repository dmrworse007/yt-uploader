"""Upload a single video file to YouTube via the Data API v3."""
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def build_youtube(creds):
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_video(youtube, file_path, meta, privacy_status,
                 category_id, made_for_kids):
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": str(category_id),
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": bool(made_for_kids),
        },
    }
    media = MediaFileUpload(file_path, chunksize=1024 * 1024 * 8, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )
    response = None
    while response is None:
        _status, response = request.next_chunk()
    return response  # contains the new video id in response["id"]
