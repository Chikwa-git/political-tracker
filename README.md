# Radar Político

> Real-time parliamentary transparency — track how any Brazilian federal deputy votes, with AI-powered analysis.

![Radar Político](docs/screenshot.png)

---

## About

Radar Político consumes the Brazilian Chamber of Deputies open data API to display voting history, presence rate, political alignment, and legislative propositions for any federal deputy. An AI layer (Llama 3.3 via Groq) generates an on-demand political profile, cross-referencing voting data and authored propositions to produce a positioning analysis, behavioral coherence score, and executive summary.

The project started as a CS50X final project built with Flask and was fully rewritten in Django as a CS50W final project — evolving from a simple search MVP into a full application with a deputy comparator, AI analysis, and asynchronous search.

---

## Features

- **Asynchronous search** — results appear without page reload, using the Fetch API
- **Full deputy profile** — voting history, presence rate, majority alignment, Top 5 most/least aligned colleagues, latest propositions
- **Political X-Ray** — on-demand AI analysis: political positioning, coherence between votes and propositions, and executive summary
- **Comparator** — search two deputies and compare presence and alignment side by side
- **Smart cache** — data stored for 24h in SQLite to avoid redundant API calls

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python · Django |
| Frontend | JavaScript (Vanilla) · CSS Grid/Flexbox |
| Data | Brazilian Chamber of Deputies API |
| AI | Groq API · Llama 3.3 70B |
| Cache | SQLite |

---

## Running Locally

```bash
# Clone the repository
git clone https://github.com/Chikwa-git/political-tracker.git
cd political-tracker

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env
# Free API key at: https://console.groq.com

# Start the server
python manage.py runserver
```

Open `http://127.0.0.1:8000`.

> The cache database is created automatically on first run. No migrations needed.

---

## Author

Lincoln Neves  
[LinkedIn](https://linkedin.com/in/lincoln-neves100) · [GitHub](https://github.com/Chikwa-git)
