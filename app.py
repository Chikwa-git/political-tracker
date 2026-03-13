"""Flask routes for searching and displaying congressman data."""

import analysis
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
                
        congressman_id_int = int(congressman_id)

        # Use cached analysis data when fresh; otherwise compute and cache.
        if database.is_valid_cache(f"history_{congressman_id}", hours=24):
            history = database.get_cache(f"history_{congressman_id}")
            presence = database.get_cache(f"presence_{congressman_id}")
            majority_alignment = database.get_cache(f"majority_{congressman_id}")
            political_alignment = database.get_cache(f"political_{congressman_id}")
        else:
            history = analysis.get_congressman_history(congressman_id_int)
            presence = analysis.get_presence_rate(history)
            majority_alignment = analysis.get_majority_alignment(congressman_id_int)
            political_alignment = analysis.get_political_alignment(congressman_id_int)

            database.save_cache(f"history_{congressman_id}", history)
            database.save_cache(f"presence_{congressman_id}", presence)
            database.save_cache(f"majority_{congressman_id}", majority_alignment)
            database.save_cache(f"political_{congressman_id}", political_alignment)

        return render_template("deputy.html", 
            deputy=deputy_flat,
            history=history,
            presence=presence,
            majority_alignment=majority_alignment,
            political_alignment=political_alignment)

    return redirect(url_for("index"))

if __name__ == "__main__":
    database.init_db()
    app.run(debug=True)

