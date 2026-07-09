# YouTube Auto-Uploader 

A hands-off system that automatically publishes Shorts from your Google Drive
bundles to your YouTube channel, running 24/7 in the cloud (GitHub Actions) —
no computer needs to stay on.

- **Repo:** https://github.com/dmrworse007/yt-uploader
- **Source (Drive):** folder `1FjS82kBjBZaMKZ0qkREY8opmO1r71A7M` ("Viral Reels Bundle")
- **Channel:** your YouTube channel (authorized via Google OAuth)
- **Schedule:** every 4 hours (up to 6 uploads/day)
- **Cost:** free (public GitHub repo = unlimited Actions minutes)

---

## 1. What it does, in one paragraph

Every 4 hours GitHub runs the workflow on its own servers. It reads your Drive
"Viral Reels Bundle" folder (following the shortcuts into all 30 sub-bundles),
skips editing junk (transitions, overlays, effects, etc.), picks a **random**
reel it hasn't posted yet, reformats it into a vertical 1080×1920 Short,
auto-writes a title/description/hashtags, uploads it to your channel, records
it so it's never posted twice, and stops after 6 uploads/day. Your computer
can be off the entire time.

---

## 2. How it works (cloud architecture)

```
GitHub Actions scheduler  (cron: every 4 hours)
        │
        ▼
 .github/workflows/upload.yml
        │  git clone repo  →  install deps  →  write secrets to files
        ▼
   python run_once.py
        │
        ├─ auth.py .......... logs in to Google with your cached token (auto-refresh)
        ├─ drive_client.py .. crawls the folder + shortcuts, lists every video
        ├─ (skip filter) .... drops transitions/overlays/effects by filename
        ├─ (random pick) .... shuffles remaining clips, takes the next one
        ├─ metadata.py ...... generates title + description + hashtags
        ├─ shorts.py ........ ffmpeg → vertical 1080×1920 Short (blurred-fill)
        ├─ uploader.py ...... uploads to YouTube (Data API v3)
        └─ state.py ......... records the upload + daily counter
        │
        ▼
   git commit + push  →  state.json saved back to the repo (remembers progress)
```

**Credentials** live as encrypted GitHub Actions **secrets**, never in the code:
- `GDRIVE_TOKEN` — your Google login token (from `token.json`)
- `GOOGLE_CLIENT_SECRET` — your OAuth app credentials (from `client_secret.json`)

---

## 3. Files in the repo

| File | Purpose |
|------|---------|
|
