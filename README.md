# 🏎️ F1Intel — Formula 1 Intelligence Platform

A premium, production-grade Formula 1 analytics platform built with Python & Streamlit.

---

## ✨ Features

| Page | Description |
|------|-------------|
| 🏠 Dashboard | Championship leaders, countdown, KPIs, points progression |
| 🏆 Standings | Full driver & constructor standings with gap analysis |
| 👤 Drivers | Profiles, career stats, season results, radar charts, H2H |
| 🏎️ Teams | Constructor profiles, driver lineups, historical history |
| 🗺️ Circuits | Track specs, weather forecasts, historical winners |
| 📊 Race Analysis | Results, qualifying, sectors, pit stops, strategy |
| 📡 Telemetry | Speed/throttle/brake/RPM/gear, delta time, racing lines |
| 🔧 Strategy | Tire stints, degradation, pit windows, compound analysis |
| ⚡ Live | Real-time leaderboard, intervals, tire tracking, race control |
| 🗺️ Track Map | Circuit layout, driver positions, lap animation |
| 📚 Historical | Champions history, season browser, all-time records |
| ⭐ Power Rankings | Form index, consistency, qualifying specialists, analytics |

---

## 🚀 Setup Guide (Beginner-Friendly)

### Step 1 — Install Python

1. Go to **https://www.python.org/downloads/**
2. Download **Python 3.12** (or newer)
3. Run the installer
4. ✅ **IMPORTANT**: Check **"Add Python to PATH"** before clicking Install
5. Click **Install Now**

Verify it worked — open Command Prompt (Windows) or Terminal (Mac/Linux) and type:
```
python --version
```
You should see something like `Python 3.12.x`

---

### Step 2 — Download / Create the Project

**Option A — If you received the project as a ZIP:**
1. Unzip the file
2. Open PyCharm
3. File → Open → select the `F1Intel` folder

**Option B — Create manually:**
1. Open PyCharm
2. File → New Project → name it `F1Intel`
3. Create all files as shown in the project structure

---

### Step 3 — Open Terminal in PyCharm

In PyCharm, go to **View → Tool Windows → Terminal**

(Or press `Alt+F12` on Windows / `Cmd+F12` on Mac)

---

### Step 4 — Install Dependencies

In the PyCharm terminal, run:

```bash
pip install -r requirements.txt
```

This installs all required packages. Wait for it to complete (may take 2–5 minutes).

---

### Step 5 — Create the Project Structure

Make sure your folder looks exactly like this:

```
F1Intel/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── assets/
│   ├── logo.png          ← add your logo here (optional)
│   └── style.css
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── teams.py
├── services/
│   ├── __init__.py
│   ├── jolpica_service.py
│   ├── openf1_service.py
│   ├── fastf1_service.py
│   ├── cache_service.py
│   └── weather_service.py
├── pages/
│   ├── 01_standings.py
│   ├── 02_drivers.py
│   ├── 03_teams.py
│   ├── 04_circuits.py
│   ├── 05_race_analysis.py
│   ├── 06_telemetry.py
│   ├── 07_strategy.py
│   ├── 08_live.py
│   ├── 09_track_map.py
│   ├── 10_historical.py
│   └── 11_power_rankings.py
├── components/
│   ├── __init__.py
│   ├── kpi_cards.py
│   ├── countdown.py
│   ├── standings_table.py
│   ├── driver_card.py
│   ├── team_card.py
│   ├── circuit_card.py
│   ├── track_map.py
│   ├── telemetry_charts.py
│   ├── strategy_charts.py
│   ├── live_leaderboard.py
│   └── sidebar.py
├── utils/
│   ├── __init__.py
│   ├── flags.py
│   ├── colors.py
│   ├── formatters.py
│   └── helpers.py
└── data/
    └── cache/            ← FastF1 cache (auto-created)
```

---

### Step 6 — Run the Application

In the PyCharm terminal:

```bash
streamlit run app.py
```

Your browser will automatically open at:
```
http://localhost:8501
```

---

### Step 7 — Replace the Logo (Optional)

1. Prepare your logo as a PNG file (recommended: 300×100 px)
2. Name it `logo.png`
3. Place it in the `assets/` folder
4. Replace the existing `logo.png` — no code changes needed

---

## 🔄 Updating the Application

The app auto-updates data from APIs. To update the code itself:

1. Replace any `.py` files with new versions
2. Stop Streamlit (`Ctrl+C` in terminal)
3. Run again: `streamlit run app.py`

---

## 🌐 Deploying Online (Free)

### Option A — Streamlit Cloud (Recommended)

1. Create a free account at **https://streamlit.io/cloud**
2. Push your project to a **GitHub repository**
3. In Streamlit Cloud: **New app** → connect your GitHub repo
4. Set main file as `app.py`
5. Click **Deploy** — your app gets a public URL!

### Option B — Railway

1. Sign up at **https://railway.app**
2. Connect your GitHub repo
3. Add a `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```
4. Deploy

---

## 📡 Data Sources

| Source | What it provides | Rate limit |
|--------|-----------------|------------|
| [Jolpica (Ergast)](https://api.jolpi.ca/ergast/f1) | Standings, results, circuits, history | 4 req/sec |
| [OpenF1](https://openf1.org) | Live timing, telemetry, positions, stints | Generous |
| [FastF1](https://docs.fastf1.dev) | Detailed lap/telemetry data (2018+) | Cached locally |
| [Open-Meteo](https://open-meteo.com) | Weather forecasts | Free, no key needed |

All APIs are **free** and require **no API key**.

---

## 🛠️ Troubleshooting

**"Module not found" error:**
```bash
pip install -r requirements.txt
```

**FastF1 slow to load:**
- First load of any session downloads ~50-200MB
- After that, it's cached in `data/cache/` and loads instantly

**Live page shows no data:**
- Live data only available during F1 race weekends (FP1 through Race)
- Outside of race weekends, the latest available session is shown

**App shows blank/white page:**
- Check the terminal for error messages
- Ensure all files are in the correct folders

**Port already in use:**
```bash
streamlit run app.py --server.port 8502
```

---

## ⚙️ Configuration

Edit `config/settings.py` to change:
- Cache durations
- Minimum seasons for FastF1
- Plotly chart styling

Edit `.streamlit/config.toml` to change:
- Theme colors
- Server settings

---

## 📝 Notes

- F1Intel is a fan project. Not affiliated with Formula 1, FIA, or any F1 team.
- Data provided by third-party APIs; accuracy depends on those sources.
- FastF1 telemetry data is available from the 2018 season onwards.
- Live timing requires an active OpenF1 session (race weekends only).
