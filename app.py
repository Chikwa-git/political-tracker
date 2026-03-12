"""Flask routes for searching and displaying congressman data."""

import camara
import database
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


def _normalize_deputy_data(raw_data):
    """Return deputy data in the flat format expected by deputy.html."""

    if not raw_data:
        return None

    # Already normalized format (new cache schema).
    if "nome" in raw_data and "siglaPartido" in raw_data:
        return raw_data

    # Legacy/full API format where relevant fields are under ultimoStatus.
    status = raw_data.get("ultimoStatus", {})
    gabinete = status.get("gabinete", {})

    return {
        "id": raw_data.get("id"),
        "nome": status.get("nome"),
        "siglaPartido": status.get("siglaPartido"),
        "siglaUf": status.get("siglaUf"),
        "urlFoto": status.get("urlFoto"),
        "email": gabinete.get("email"),
        "idLegislatura": status.get("idLegislatura"),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    """Render the search page and handle congressman name lookup."""

    if request.method == "GET":
        return render_template("index.html")
    
    if request.method == "POST":
        # Read the name submitted by the search form and query the API.
        name = request.form.get("name")
        results = camara.search_congressman(name)
        return render_template("index.html", results=results)


@app.route("/deputy", methods=["GET", "POST"])
def deputy():
    """Render deputy details, using cache to avoid repeated API calls."""

    if request.method == "POST":
        # Reuse the search flow when the user submits a new name from this page.
        name = request.form.get("name")
        results = camara.search_congressman(name)
        return render_template("index.html", results=results)
    
    if request.method == "GET":
        # Deputy ID is expected in the URL query string: /deputy?id=<id>
        congressman_id = request.args.get("id")

        if not congressman_id:
            # Guard clause: redirect to home if no ID is provided.
            return redirect(url_for("index"))
        
        cache_key = f"deputy_{congressman_id}"
        cache_hours = 24

        # Use cached deputy data when fresh; otherwise fetch and update cache.
        if database.is_valid_cache(cache_key, cache_hours):
            deputy_flat = _normalize_deputy_data(database.get_cache(cache_key))
        else:
            deputy_data = camara.get_congressman(congressman_id)
            deputy_flat = _normalize_deputy_data(deputy_data)
            database.save_cache(cache_key, deputy_flat)

        if not deputy_flat:
            return redirect(url_for("index"))

        return render_template("deputy.html", deputy=deputy_flat)

    return redirect(url_for("index"))

if __name__ == "__main__":
    database.init_db()
    app.run(debug=True)

