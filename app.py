"""Flask routes for searching and displaying congressman data."""

import analysis
import camara
import database
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


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
            deputy_data = database.get_cache(cache_key)
        else:
            deputy_data = camara.get_congressman(congressman_id)
            database.save_cache(cache_key, deputy_data)

        return render_template("deputy.html", deputy=deputy_data)

    return redirect(url_for("index"))

if __name__ == "__main__":
    database.init_db()
    app.run(debug=True)

