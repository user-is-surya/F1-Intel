# F1Intel — Important Setup Notes

## Required Streamlit Version

F1Intel requires **Streamlit 1.35+**.

To check your version:
```
streamlit --version
```

To upgrade:
```
pip install --upgrade streamlit
```

---

## Why Flags Show as Broken Images (Windows)

On Windows, Unicode flag emoji (🇬🇧 🇮🇹) show as two-letter codes (GB, IT) because
Windows does not include flag emoji in its system fonts.

F1Intel uses flagcdn.com images to fix this. If you see broken image icons:

1. **Check your internet connection** — flagcdn.com must be reachable
2. **Corporate firewalls** may block external images. If so, the app will automatically
   fall back to colored ISO code badges (e.g. a blue "GB" badge)

No code change needed — the fallback is automatic via the `onerror` handler.

---

## Why Live Page May Show "No Live Session"

The Live page uses the **OpenF1 API** which provides data for:
- Formula 1 races from **2023 onwards**
- All session types: FP1, FP2, FP3, Qualifying, Sprint Qualifying, Sprint, Race

**OpenF1 only shows live data during an active F1 session.**

If there IS a live session but the page says there isn't:
1. OpenF1 may have a delay of 30-60 seconds in recognizing the session start
2. The `get_live_session()` function checks if `now` falls between `date_start` and `date_end`
3. Try refreshing the page manually

**During a live race weekend**, the page auto-refreshes every 6 seconds.
Outside race weekends, it shows the most recent completed session as a replay.

---

## Track Map Data Availability

The Track Map page uses OpenF1's `/location` endpoint (GPS transponder data).

This is available for:
- Sessions from **2023 onwards**
- Only when OpenF1 has indexed the session (usually within minutes of session end)

For older sessions, the map will show "No Transponder Data Available".

---

## FastF1 First Load

The Telemetry, Strategy, Race Analysis, and Track Map (FastF1 mode) pages
download session data from the F1 CDN on first load.

**First load per session: 1-5 minutes** (downloads ~50-200MB)
**Subsequent loads: instant** (cached in `data/cache/`)

Do not click away or refresh during the first load.

---

## Performance Tips

1. The `data/cache/` folder stores FastF1 session data. It grows over time.
   Safe to delete if you need space — data will re-download on next access.

2. All API responses are cached in Streamlit's memory cache.
   If data looks stale, use the **Clear Cache** button in the Streamlit menu (⋮).

3. For best performance on Windows, run with:
   ```
   streamlit run app.py --server.fileWatcherType none
   ```
