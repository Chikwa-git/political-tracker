# Radar Político
#### Video Demo: <URL HERE>
#### Description:

Radar Político is a web application that tracks and visualizes the behavior of Brazilian federal congressmen (Deputados Federais). It allows users to search for any member of the Chamber of Deputies, view their voting history, presence rate, alignment with the parliamentary majority, and the legislation they have authored. The project was built as the final project for CS50X and uses real, live data from the official Brazilian Chamber of Deputies open data API.

## Motivation

Brazil has 513 federal deputies, and most citizens have little visibility into how their representatives actually vote. Radar Político was created to make this information accessible and easy to understand — turning raw government data into a clear, visual profile for each congressman.

## Technologies Used

- **Python 3** and **Flask** — backend web framework handling routing and template rendering
- **SQLite** — used as a local cache database to avoid redundant API calls
- **Jinja2** — Flask's templating engine for rendering dynamic HTML pages
- **HTML and CSS** — frontend, with a dark mode design using the Bebas Neue and IBM Plex Mono fonts
- **Câmara dos Deputados Open Data API** — the official Brazilian government API at `dadosabertos.camara.leg.br`, which provides free, unauthenticated access to congressional data

## Project Structure

### `app.py`
The main Flask application. Defines two routes: `/` for the search page and `/deputy` for the congressman profile page. The deputy route handles cache validation — if fresh cached data exists for a given congressman, it is loaded from the database instead of making new API calls. If not, it triggers the full data fetching and analysis pipeline and saves the results to the cache. The route also contains a `_normalize_deputy_data()` helper function that flattens the nested API response into the flat format expected by the template.

### `camara.py`
A module that wraps all direct calls to the Câmara dos Deputados API. Each function corresponds to a specific API endpoint: searching for congressmen by name, fetching a congressman's full profile, retrieving recent voting sessions, fetching individual votes for each session, retrieving party/bloc orientations for a vote, and fetching propositions authored by a congressman. Centralizing all API calls in this module makes the rest of the codebase cleaner and easier to maintain.

### `analysis.py`
Contains all the data analysis logic. The key functions are:

- `get_congressman_history()` — fetches recent plenary votes and checks whether the congressman voted in each one. If the congressman's ID does not appear in a vote's records, they are marked as "Ausente" (absent). This uses Python's `for/else` pattern, where the `else` block executes only when the loop completes without a `break`.
- `get_presence_rate()` — calculates the percentage of votes where the congressman was present, based on the history returned above.
- `get_majority_alignment()` — compares the congressman's vote against the orientation of the "Maioria" (parliamentary majority) for each vote. This metric was chosen over party alignment because the API does not consistently publish individual party orientations — most parties operate within blocs, and many smaller parties have no registered orientation at all. Aligning against the majority is a reliable and politically meaningful alternative.
- `get_political_alignment()` — compares the congressman's votes against every other deputy who voted in the same sessions and calculates a similarity score. Returns the top 5 most and least similar voters.
- `get_congressman_propositions()` — fetches the 20 most recent bills authored by the congressman and classifies each one as approved, rejected, or pending, based on the `codSituacao` field returned by the API.

### `database.py`
Handles all SQLite operations. The cache table stores a key, a JSON-serialized value, and a timestamp. The `is_valid_cache()` function checks whether a cache entry exists and is within the allowed time window (24 hours for voting data, 168 hours for deputy profiles). This cache layer was essential to make the application usable — without it, loading a single deputy profile requires over 100 sequential API calls, which takes several minutes. With the cache, repeat visits are instantaneous.

### `templates/index.html`
The search page. Contains a search form and a grid of results when a name is submitted. Each result card shows the congressman's photo, name, party, and state, and links to their profile page.

### `templates/deputy.html`
The main profile page. Displays the congressman's photo, name, party, state, and email in a hero section, along with their presence rate and majority alignment percentage. Below, a voting history section lists each recent plenary vote with a color-coded badge (SIM, NÃO, ABSTENÇÃO, AUSENTE). A sidebar shows the majority alignment bar, the top 5 most and least aligned deputies, and a list of recent propositions.

## Design Decisions

**Majority alignment over party alignment** — The original design called for showing how often a congressman follows their own party's orientation. During development, it became clear that the API does not reliably publish individual party orientations. Most parties vote as part of larger blocs, and many smaller parties have no recorded orientation at all. The majority alignment metric — which measures how often a congressman votes with the parliamentary majority — is both more reliable and arguably more informative, as it reveals whether a deputy tends to support or oppose the dominant congressional coalition.

**SQLite cache** — A cache was necessary from the start because the application depends on many sequential API calls. The design choice was to use SQLite rather than an in-memory dictionary so that the cache persists between server restarts. Each data type (profile, history, alignment, propositions) is cached under a separate key with a 24-hour TTL, balancing freshness with performance.

**Filtering for nominal votes** — The API returns all types of plenary votes, including symbolic votes where only the final result is recorded and individual votes are not tracked. The application filters these out by discarding any vote session with fewer than 50 individual vote records, ensuring the history and alignment calculations are based only on roll-call votes where each deputy's position is actually registered.
