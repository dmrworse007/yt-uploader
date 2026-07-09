"""Pick the next un-uploaded clip from Drive, skip editing-asset clips,
reformat to a vertical Short, generate metadata, upload, record state."""
import logging
import os
import random
import sys

import yaml

import auth
import drive_client
import metadata
import shorts
import state as state_mod
import uploader

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(HERE, log_file), encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def p(cfg, key):
    return os.path.join(HERE, cfg[key])


def main():
    cfg = load_config()
    setup_logging(cfg["log_file"])
    log = logging.getLogger("uploader")

    dry_run = "--dry-run" in sys.argv

    if cfg.get("make_shorts", False) and not dry_run and not shorts.ffmpeg_available():
        log.error("make_shorts is ON but ffmpeg not found. Run: pip install imageio-ffmpeg")
        return

    skip_words = [w.lower() for w in cfg.get("skip_name_keywords", [])]

    def is_junk(name):
        n = name.lower()
        return any(w in n for w in skip_words)

    state = state_mod.load(p(cfg, "state_file"))

    done_today = state_mod.uploads_today(state)
    remaining = cfg["max_uploads_per_day"] - done_today
    if remaining <= 0:
        log.info("Daily cap reached (%s today). Nothing to do.", done_today)
        return
    to_upload = min(cfg["uploads_per_run"], remaining)

    creds = auth.get_credentials(p(cfg, "client_secret_file"), p(cfg, "token_file"))
    drive = drive_client.build_drive(creds)

    log.info("Listing videos in Drive folder %s ...", cfg["drive_folder_id"])
    videos = drive_client.list_videos(drive, cfg["drive_folder_id"], cfg["video_mime_prefixes"])
    log.info("Found %s video files total.", len(videos))

    skipped_junk = 0
    pending = []
    for v in videos:
        if state_mod.already_uploaded(state, v["id"]):
            continue
        if int(v.get("size", "0") or 0) < cfg["min_file_bytes"]:
            continue
        if is_junk(v["name"]):
            skipped_junk += 1
            continue
        pending.append(v)

    log.info("Skipped %s junk/asset clips by name filter.", skipped_junk)

    if not pending:
        log.info("No new content videos left to upload. All caught up!")
        return
    log.info("%s content videos still pending. Uploading up to %s now.", len(pending), to_upload)

    yt = None if dry_run else uploader.build_youtube(creds)
    uploaded = 0
    random.shuffle(pending)  # random order so consecutive uploads differ
    for v in pending[:to_upload]:
        meta = metadata.generate(v["name"])
        if dry_run:
            log.info("[DRY-RUN] Would upload %s -> title=%r", v["name"], meta["title"])
            uploaded += 1
            continue

        dest = os.path.join(p(cfg, "download_dir"), v["id"] + "_" + v["name"])
        log.info("Downloading %s ...", v["name"])
        drive_client.download_file(drive, v["id"], dest)

        upload_path = dest
        short_path = None
        if cfg.get("make_shorts", False):
            short_path = dest + ".short.mp4"
            log.info("Formatting as vertical Short ...")
            try:
                shorts.to_short(dest, short_path, cfg.get("short_max_seconds", 60),
                                cfg.get("short_fit", "auto"))
                upload_path = short_path
            except Exception as e:
                log.error("ffmpeg formatting failed (%s). Uploading original.", e)
                short_path = None

        log.info("Uploading %s ...", v["name"])
        resp = uploader.upload_video(yt, upload_path, meta,
                                     cfg["privacy_status"], cfg["category_id"], cfg["made_for_kids"])
        video_id = resp["id"]
        log.info("Uploaded OK: https://youtu.be/%s", video_id)

        state = state_mod.record_upload(state, v["id"], v["name"], video_id)
        state_mod.save(p(cfg, "state_file"), state)

        if cfg.get("cleanup_after_upload", True):
            for pth in (dest, short_path):
                if pth and os.path.exists(pth):
                    try:
                        os.remove(pth)
                    except OSError:
                        pass
        uploaded += 1

    log.info("Run complete. Uploaded %s this run, %s total today.", uploaded, state_mod.uploads_today(state))


if __name__ == "__main__":
    main()
