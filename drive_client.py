"""List and download videos from a Google Drive folder.

Recursive: follows subfolders AND Google Drive shortcuts, so a top folder
that only contains shortcuts to other bundle folders is handled correctly.
"""
import io
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

FOLDER_MIME = "application/vnd.google-apps.folder"
SHORTCUT_MIME = "application/vnd.google-apps.shortcut"
VIDEO_EXTS = (".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".flv",
              ".wmv", ".3gp", ".mpeg", ".mpg")


def build_drive(creds):
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _is_video(name, mime, mime_prefixes):
    if mime and any(mime.startswith(p) for p in mime_prefixes):
        return True
    return name.lower().endswith(VIDEO_EXTS)


def _list_children(drive, folder_id):
    files = []
    page_token = None
    query = f"'{folder_id}' in parents and trashed = false"
    while True:
        resp = drive.files().list(
            q=query,
            spaces="drive",
            fields=("nextPageToken, files(id, name, mimeType, size, "
                    "createdTime, shortcutDetails(targetId, targetMimeType))"),
            orderBy="createdTime",
            pageSize=1000,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def list_videos(drive, folder_id, mime_prefixes,
                _visited=None, _depth=0, _max_depth=10):
    """Recursively collect every video under folder_id, following
    subfolders and shortcuts. Returns list of {id, name, size, mimeType}."""
    if _visited is None:
        _visited = set()
    if folder_id in _visited or _depth > _max_depth:
        return []
    _visited.add(folder_id)

    results = []
    for f in _list_children(drive, folder_id):
        mime = f.get("mimeType", "")
        name = f.get("name", "")

        if mime == FOLDER_MIME:
            results.extend(list_videos(drive, f["id"], mime_prefixes,
                                       _visited, _depth + 1, _max_depth))

        elif mime == SHORTCUT_MIME:
            sd = f.get("shortcutDetails", {}) or {}
            tid = sd.get("targetId")
            tmime = sd.get("targetMimeType", "")
            if not tid:
                continue
            if tmime == FOLDER_MIME:
                results.extend(list_videos(drive, tid, mime_prefixes,
                                           _visited, _depth + 1, _max_depth))
            elif _is_video(name, tmime, mime_prefixes):
                try:
                    m = drive.files().get(
                        fileId=tid, fields="id,name,size,mimeType",
                        supportsAllDrives=True).execute()
                    results.append({"id": m["id"],
                                    "name": name or m.get("name", ""),
                                    "size": m.get("size", "0"),
                                    "mimeType": m.get("mimeType", "")})
                except Exception:
                    pass

        elif _is_video(name, mime, mime_prefixes):
            results.append({"id": f["id"], "name": name,
                            "size": f.get("size", "0"), "mimeType": mime})

    return results


def download_file(drive, file_id, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    request = drive.files().get_media(fileId=file_id, supportsAllDrives=True)
    with io.FileIO(dest_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024 * 8)
        done = False
        while not done:
            _status, done = downloader.next_chunk()
    return dest_path
