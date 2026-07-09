# YouTube Auto-Uploader — Full README

A hands-off system that automatically publishes Shorts from your Google Drive
bundles to your YouTube channel, running 24/7 in the cloud (GitHub Actions) —
no computer needs to stay on.

- **Repo:** https://github.com/dmrworse007/yt-uploader
- **Source (Drive):** folder ("Viral Reels Bundle")
- **Channel:** [YouTube channel](https://www.youtube.com/@Hunters_dpk) (authorized via Google OAuth)
- **Schedule:** every 4 hours (up to 6 uploads/day)
- **Cost:** free (public GitHub repo = unlimited Actions minutes)

---

## 1. What it does, in one paragraph

Every 4 hours GitHub runs the workflow on its own servers. It reads a Drive (following the shortcuts into all 30 sub-bundles containing 10k+ reels),
skips editing junk (transitions, overlays, effects, etc.), picks a **random**
reel it hasn't posted yet, reformats it into a vertical 1080×1920 Short,
auto-writes a title/description/hashtags, uploads it to the channel, records
it so it's never posted twice, and stops after 6 uploads/day. The computer
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
        ├─ auth.py .......... logs in to Google with my cached token (auto-refresh)
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
- `GDRIVE_TOKEN` — my Google login token (from `token.json`)
- `GOOGLE_CLIENT_SECRET` — my OAuth app credentials (from `client_secret.json`)

---

## 3. Files in the repo

| File | Purpose |
|------|---------|
| `.github/workflows/upload.yml` | The scheduler + runner (this is what GitHub executes). |
| `run_once.py` | Main program: pick → format → upload → record (one run). |
| `auth.py` | Google sign-in / token refresh. |
| `drive_client.py` | Lists & downloads videos; follows shortcuts + subfolders. |
| `metadata.py` | Auto-generates each video's title, description, hashtags. |
| `shorts.py` | Reformats any clip into a vertical Short via ffmpeg. |
| `uploader.py` | Uploads to YouTube. |
| `state.py` | Tracks uploaded videos + per-day count. |
| `config.yaml` | **All your settings** — edit this to change behavior. |
| `requirements.txt` | Python dependencies. |
| `state.json` | Auto-created log of every upload (don't delete — prevents repeats). |

---

## 4. Settings (`config.yaml`)

Edit `config.yaml` in the repo (pencil icon → edit → Commit). Changes apply on
the next scheduled run.

| Setting | Current | Meaning |
|---------|---------|---------|
| `uploads_per_run` | `1` | Videos posted per workflow run. |
| `max_uploads_per_day` | `6` | Hard daily ceiling (safe max on free API quota). |
| `privacy_status` | `public` | `public`, `unlisted`, or `private`. |
| `category_id` | `24` | 24=Entertainment, 22=People&Blogs, 10=Music, 20=Gaming. |
| `make_shorts` | `true` | Reformat every clip to vertical 1080×1920. |
| `short_max_seconds` | `60` | Trim length for Shorts. |
| `short_fit` | `auto` | `auto` (blurred-fill, no crop), `crop` (fill+trim), `pad` (bars). |
| `skip_name_keywords` | list | Clip names containing these words are skipped (transitions, overlays, effects, intro, outro, watermark, logo, preset, template, green screen, lut, glitch, frame, border, bonus, sample, …). |

**Change how often it posts:** edit the schedule line in
`.github/workflows/upload.yml`:
```
- cron: '0 */4 * * *'   # every 4 hours. '0 */3 * * *' = every 3h (8/day), etc.
```
Keep the cadence in line with `max_uploads_per_day`.

---

## 5. Managing it

**Run one right now:** GitHub → **Actions** tab → **YouTube Auto Uploader** →
**Run workflow** → **Run workflow**.

**See what it did:** GitHub → **Actions** → click the latest run → **upload**
job → read the log (look for `Uploaded OK: https://youtu.be/...`).

**Pause it:** GitHub → **Actions** → **YouTube Auto Uploader** → **⋯** menu
(top-right) → **Disable workflow**.

**Resume it:** same menu → **Enable workflow**.

**Change a setting:** edit `config.yaml` (or `upload.yml` for the schedule) in
the repo → Commit.

---

## 6. Random selection

The uploader shuffles the remaining un-posted clips and takes one at random each
run, so consecutive uploads come from different bundles/themes rather than in
sequence. Already-uploaded clips are excluded via `state.json`, so nothing
repeats.

---

## 7. Costs & limits

- **GitHub Actions:** free. Public repos get unlimited minutes; each run is
  ~1.5 minutes.
- **YouTube API quota:** each upload costs 1,600 of a 10,000/day quota → 6/day
  is the safe max. To go higher, request a quota increase in Google Cloud
  Console (APIs & Services → YouTube Data API → Quotas) and raise
  `max_uploads_per_day`.
- **Runway:** ~16,000 clips at 6/day ≈ 7+ years of content.

---

## 8. Troubleshooting

- **A run is red (failed):** open the run → **upload** job → read the last log
  lines. Most issues are printed plainly.
- **"Daily cap reached":** normal — it already posted 6 today.
- **Login expired / auth error:** your Google app is set to "In production" so
  the token shouldn't expire, but if it does, re-authorize locally
  (`python run_once.py` on your PC after deleting `token.json`) and update the
  `GDRIVE_TOKEN` secret with the new `token.json` contents.
- **Encoding / "null bytes" errors:** re-upload the affected `.py` file from a
  clean copy (file uploads preserve bytes; the issue was a one-time source glitch).

---
