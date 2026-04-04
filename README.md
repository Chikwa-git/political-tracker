# Political Tracker

A Django web application for tracking and analyzing Brazilian federal deputies' voting behavior, political alignment, and legislative activity — powered by the Brazilian Chamber of Deputies open data API and AI-generated political analysis.

---

## Distinctiveness and Complexity

Political Tracker is fundamentally different from every project built throughout CS50W. Unlike the network, e-commerce, or mail applications — which operate on user-generated content stored in a local database — this project is built around a live, external government API that returns real parliamentary data. Every piece of information displayed is fetched, cached, processed, and analyzed in real time, making the technical challenges substantially different in nature.

### Why this project is distinctive

The core challenge of this application is not managing user accounts or rendering forms — it is the orchestration of an asynchronous data pipeline that handles unreliable external dependencies gracefully. The Brazilian Chamber of Deputies API (`dadosabertos.camara.leg.br`) is a public government service known for instability: it frequently returns 504 Gateway Timeout errors, drops SSL connections mid-request, and has inconsistent response times. Building a production-quality user experience on top of this required implementing a multi-layer caching strategy using SQLite, a custom TTL validation system, and comprehensive error handling that degrades gracefully rather than crashing the application.

The analytical layer of the application goes beyond simple data retrieval. The majority alignment algorithm, for instance, does not simply fetch a pre-computed number from the API — it fetches the last 50 plenary voting sessions, cross-references each deputy's individual vote against the chamber majority orientation (`siglaPartidoBloco == "Maioria"`), and computes a percentage in real time. The political alignment feature goes further: it compares the target deputy's vote against every other deputy who participated in the same sessions, accumulates a similarity score across all shared votes, and returns the five most and least aligned colleagues — a computation that involves processing thousands of individual vote records per request.

The Raio-X Político feature represents an integration that no other CS50W project in this context has attempted: combining structured parliamentary data (voting history, presence rate, majority alignment, political alignment, authored propositions) into a carefully engineered prompt sent to a large language model (Llama 3.3 70B via Groq API), which returns a structured JSON analysis covering the deputy's political positioning, behavioral coherence, and an executive summary. The prompt engineering required to produce consistent, valid JSON output — with meaningful political analysis rather than generic responses — involved multiple iterations of temperature tuning, output format specification, and context structuring.

The Deputy Comparator adds another layer of complexity: it uses `Promise.all()` to fire two simultaneous fetch requests to the `/deputy-data/` endpoint, waits for both to resolve, then dynamically constructs a side-by-side comparison interface entirely in JavaScript — including color-coded highlighting that identifies the lower value in each metric without any page reload.

### Technical complexity summary

The application combines: a Django backend with five distinct views serving both HTML templates and JSON API endpoints; a custom SQLite caching layer with TTL validation independent of Django's ORM; a JavaScript frontend with multiple asynchronous fetch flows, dynamic DOM construction, and URL parameter-based auto-search; integration with two external APIs (Brazilian Chamber of Deputies and Groq); and a prompt engineering layer that transforms structured data into natural language political analysis. No single CS50W project in the course curriculum requires this breadth of integration simultaneously.

---

## Project Structure

```
political-tracker/
├── config/
│   ├── settings.py         # Django project settings, loads .env for API keys
│   ├── urls.py             # Root URL configuration, delegates to tracker app
│   └── wsgi.py
├── tracker/
│   ├── templates/
│   │   └── tracker/
│   │       ├── index.html      # Home page with search and compare entry points
│   │       ├── deputy.html     # Deputy profile page with accordion and Raio-X
│   │       └── compare.html    # Side-by-side deputy comparator
│   ├── static/
│   │   └── tracker/
│   │       └── js/
│   │           ├── search.js   # Async search via fetch, auto-search on redirect
│   │           ├── deputy.js   # Accordion toggle and Raio-X AI generation
│   │           └── compare.js  # Dual-panel search, selection, and comparison logic
│   ├── views.py        # All Django views: index, deputy, compare, search, deputy_data, ai_analysis
│   ├── camara.py       # All calls to the Brazilian Chamber of Deputies API
│   ├── analysis.py     # Analytical functions: voting history, presence rate, majority alignment, political alignment, propositions
│   ├── database.py     # SQLite cache layer with TTL validation
│   └── apps.py         # AppConfig with ready() hook to initialize the cache database on startup
├── .env                # GROQ_API_KEY (not committed to version control)
├── manage.py
└── README.md
```

---

## File Descriptions

### `tracker/camara.py`

This module is the sole interface between the application and the Brazilian Chamber of Deputies REST API (`https://dadosabertos.camara.leg.br/api/v2`). It contains a private `_get_json()` helper that handles HTTP GET requests with a configurable timeout and raises on non-2xx responses. Public functions include:

- `search_congressman(name)` — searches deputies by name
- `get_congressman(id)` — fetches full profile data for a deputy
- `get_recent_votes()` — fetches the last 50 plenary voting sessions (PLEN organ only), paginating through multiple API pages as needed
- `get_vote_details(vote_id)` — fetches individual votes for a session
- `get_vote_orientation(vote_id)` — fetches party/bloc orientation for a session, used to find the chamber majority position
- `get_propositions(id)` / `get_proposition(id)` — fetches authored legislative propositions

### `tracker/analysis.py`

Contains all business logic for transforming raw API data into meaningful political metrics:

- `get_congressman_history(id)` — builds a voting history list for the last 50 plenary sessions, marking sessions where the deputy did not appear as "Ausente" using Python's `for/else` construct
- `get_presence_rate(history)` — computes the percentage of sessions where the deputy was not absent
- `get_majority_alignment(id)` — cross-references each deputy vote against the chamber majority orientation and computes an alignment percentage
- `get_political_alignment(id)` — compares the deputy's votes against every other deputy across all shared sessions, returning the five most and least aligned colleagues (minimum 10 shared votes to avoid statistical noise)
- `get_congressman_propositions(id)` — fetches and classifies the deputy's last 20 authored propositions as approved, rejected, or in progress

### `tracker/database.py`

A lightweight caching layer built directly on Python's `sqlite3` module, independent of Django's ORM. The cache table stores JSON-serialized data with a timestamp. Key functions:

- `init_db()` — creates the cache table if it does not exist, called on app startup via `apps.py`
- `save_cache(key, data)` — serializes data as JSON and stores with current timestamp using `INSERT OR REPLACE`
- `get_cache(key)` — retrieves and deserializes cached data
- `is_valid_cache(key, hours)` — computes the time difference between now and the stored timestamp and returns whether it falls within the TTL window

The choice to use raw SQLite rather than Django models was deliberate: the cache is not application data — it is an infrastructure concern. Using Django's ORM would require migrations every time the cache schema changed, and would conflate ephemeral API responses with persistent application state.

### `tracker/views.py`

Contains six views:

- `index(request)` — handles GET (render home page) and POST (redirect to `/?search=name` for JS-driven search)
- `deputy(request)` — handles GET (load deputy profile with full analysis from cache or API) and POST (redirect to index with search term)
- `search(request)` — JSON endpoint returning deputy search results, consumed by `search.js`
- `compare(request)` — renders the comparator template
- `deputy_data(request)` — JSON endpoint returning a deputy's pre-computed metrics (presence, majority alignment), consumed by `compare.js` and `deputy.js`
- `ai_analysis(request)` — reads cached data for a deputy, constructs a structured prompt, calls the Groq API with Llama 3.3 70B, parses the JSON response, and returns the political analysis

### `tracker/static/tracker/js/search.js`

Intercepts the search form's submit event with `e.preventDefault()`, fires a fetch request to `/search/`, and dynamically renders deputy cards into the results section without any page reload. Also detects the `?search=` URL parameter on page load and automatically triggers a search — this handles the redirect flow from the deputy page's search form.

### `tracker/static/tracker/js/deputy.js`

Contains two functions: `toggleAccordion(id)` which toggles the `open` class on accordion items (controlling `max-height` via CSS transition), and `generateRaioX()` which reads the deputy ID from the URL, disables the button, shows a loading state, fires a fetch to `/ai-analysis/`, and renders the three-card Raio-X layout with posicionamento, coerência, and resumo executivo.

### `tracker/static/tracker/js/compare.js`

Manages the full comparator flow: `searchDeputy(panel)` fetches search results and renders them as selectable items; `selectDeputy(panel, ...)` records the selection, shows the selected card, and reveals the compare button when both panels are filled; `clearSelection(panel)` resets a panel; `runComparison()` fires two simultaneous requests via `Promise.all()` and renders the comparison grid with color-coded metrics highlighting the lower value in red.

---

## How to Run Locally

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/Chikwa-git/political-tracker
cd political-tracker

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install django requests groq python-dotenv

# Create .env file with your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env
# Get a free API key at: https://console.groq.com

# Start the development server
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

### Notes

- No `python manage.py migrate` is required — the application does not use Django's ORM. The SQLite cache database is created automatically on first run via the `ready()` hook in `apps.py`.
- The first time you load a deputy profile, the application makes multiple sequential requests to the Chamber of Deputies API. This can take 30–60 seconds depending on API availability. Subsequent loads within 24 hours are served from cache and load instantly.
- The Raio-X Político feature requires a valid Groq API key. The feature is on-demand — it only fires when the user clicks "Gerar análise". A free Groq account provides sufficient quota for development use.
- The Brazilian Chamber of Deputies API is a public government service and can be unstable. If you encounter 504 errors or connection timeouts, wait a few minutes and try again. The application handles these errors gracefully and displays a user-friendly message.

---

## Data Sources

- **Brazilian Chamber of Deputies Open Data API** — `https://dadosabertos.camara.leg.br/api/v2`
- **Groq API** (Llama 3.3 70B Versatile) — `https://api.groq.com`

---

## Author

Lincoln Neves — CS50W Final Project, 2026  
GitHub: [Chikwa-git](https://github.com/Chikwa-git)  
LinkedIn: [linkedin.com/in/lincoln-neves100](https://linkedin.com/in/lincoln-neves100)
