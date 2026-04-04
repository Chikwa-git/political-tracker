from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from tracker import analysis, camara, database
import os 
from groq import Groq


def _normalize_deputy_data(raw_data):
    """Return deputy data in the flat format expected by deputy.html."""

    if not raw_data:
        return None

    if "nome" in raw_data and "siglaPartido" in raw_data:
        return raw_data

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


def index(request):
    """Render the home page and optional search results for deputies."""

    if request.method == "POST":
        name = request.POST.get("name")
        results = camara.search_congressman(name)
        return render(request, "tracker/index.html", {"results": results})

    return render(request, "tracker/index.html")


def deputy(request):
    """Render detailed deputy information, using cache and fallback API calls."""

    if request.method == "POST":
        name = request.POST.get("name")
        return redirect(f"/?search={name}")

    if request.method == "GET":
        congressman_id = request.GET.get("id")

        if not congressman_id:
            return redirect(reverse("index"))

        cache_key = f"deputy_{congressman_id}"

        if database.is_valid_cache(cache_key, 24):
            deputy_flat = _normalize_deputy_data(database.get_cache(cache_key))
        else:
            deputy_data = camara.get_congressman(congressman_id)
            deputy_flat = _normalize_deputy_data(deputy_data)
            database.save_cache(cache_key, deputy_flat)

        if not deputy_flat:
            return redirect(reverse("index"))

        congressman_id_int = int(congressman_id)

        if database.is_valid_cache(f"history_{congressman_id}", hours=24):
            history = database.get_cache(f"history_{congressman_id}")
            presence = database.get_cache(f"presence_{congressman_id}")
            majority_alignment = database.get_cache(f"majority_{congressman_id}")
            political_alignment = database.get_cache(f"political_{congressman_id}")
            propositions = database.get_cache(f"propositions_{congressman_id}")
        else:
            try:
                history = analysis.get_congressman_history(congressman_id_int)
                presence = analysis.get_presence_rate(history)
                majority_alignment = analysis.get_majority_alignment(congressman_id_int)
                political_alignment = analysis.get_political_alignment(congressman_id_int)
                propositions = analysis.get_congressman_propositions(congressman_id_int)

                database.save_cache(f"history_{congressman_id}", history)
                database.save_cache(f"presence_{congressman_id}", presence)
                database.save_cache(f"majority_{congressman_id}", majority_alignment)
                database.save_cache(f"political_{congressman_id}", political_alignment)
                database.save_cache(f"propositions_{congressman_id}", propositions)

            except Exception:
                return render(request, "tracker/deputy.html", {
                    "deputy": deputy_flat,
                    "error": "A API da Câmara está temporariamente indisponível. Tente novamente em alguns minutos.",
                    "history": None,
                    "presence": None,
                    "majority_alignment": None,
                    "political_alignment": None,
                    "propositions": None,
            })
            
        for item in history:
            item["vote_class"] = (
                item["vote"]
                .lower()
                .replace("ã", "a")
                .replace("ç", "c")
                .replace("é", "e")
                .replace(" ", "")
            )

        for prop in propositions:
            prop["situacao_class"] = (
                prop["situacao"]
                .lower()
                .replace(" ", "")
                .replace("ã", "a")
            )

        return render(request, "tracker/deputy.html", {
            "deputy": deputy_flat,
            "history": history,
            "presence": presence,
            "majority_alignment": majority_alignment,
            "political_alignment": political_alignment,
            "propositions": propositions,
        })

    return redirect(reverse("index"))


def search(request):
    """Return deputy search results as JSON for the provided query name."""

    name = request.GET.get("name", "")
    results = camara.search_congressman(name)
    return JsonResponse({"results": results})


def compare(request):
    """Render the deputy comparison page."""

    return render(request, "tracker/compare.html")


def deputy_data(request):
    """Return cached or freshly computed deputy metrics as a JSON payload."""

    congressman_id = request.GET.get("id")
    if not congressman_id:
        return JsonResponse({"error": "ID não fornecido"}, status=400)

    cache_key = f"deputy_{congressman_id}"

    if database.is_valid_cache(cache_key, 24):
        deputy_flat = _normalize_deputy_data(database.get_cache(cache_key))
    else:
        deputy_raw = camara.get_congressman(congressman_id)
        deputy_flat = _normalize_deputy_data(deputy_raw)
        database.save_cache(cache_key, deputy_flat)

    congressman_id_int = int(congressman_id)

    if database.is_valid_cache(f"history_{congressman_id}", 24):
        history = database.get_cache(f"history_{congressman_id}")
        presence = database.get_cache(f"presence_{congressman_id}")
        majority_alignment = database.get_cache(f"majority_{congressman_id}")
    else:
        try:
            history = analysis.get_congressman_history(congressman_id_int)
            presence = analysis.get_presence_rate(history)
            majority_alignment = analysis.get_majority_alignment(congressman_id_int)
            database.save_cache(f"history_{congressman_id}", history)
            database.save_cache(f"presence_{congressman_id}", presence)
            database.save_cache(f"majority_{congressman_id}", majority_alignment)
        except Exception:
            return JsonResponse({"error": "API indisponível"}, status=503)

    return JsonResponse({
        "deputy": deputy_flat,
        "presence": presence,
        "majority_alignment": majority_alignment,
    })


def ai_analysis(request):
    """Generate an AI-based political profile from cached deputy data."""

    congressman_id = request.GET.get("id")
    if not congressman_id:
        return JsonResponse({"error": "ID não fornecido"}, status=400)

    # Search for all data in cache first
    history = database.get_cache(f"history_{congressman_id}")
    presence = database.get_cache(f"presence_{congressman_id}")
    majority_alignment = database.get_cache(f"majority_{congressman_id}")
    political_alignment = database.get_cache(f"political_{congressman_id}")
    propositions = database.get_cache(f"propositions_{congressman_id}")
    deputy = database.get_cache(f"deputy_{congressman_id}")

    if not history or not deputy:
        return JsonResponse({"error": "Carregue os dados do deputado antes de gerar a análise."}, status=400)

    # Summarize votes for prompt
    vote_summary = {}
    for item in history:
        vote_summary[item["vote"]] = vote_summary.get(item["vote"], 0) + 1

    most_aligned = [d["name"] for d in (political_alignment or {}).get("most_aligned", [])]
    least_aligned = [d["name"] for d in (political_alignment or {}).get("least_aligned", [])]

    prop_sample = [p["ementa"] for p in (propositions or [])[:5] if p.get("ementa")]

    prompt = f"""Você é um analista político brasileiro especializado em comportamento parlamentar.
Analise o seguinte deputado federal com base nos dados fornecidos e produza uma análise estruturada em JSON.

DEPUTADO: {deputy.get("nome")}
PARTIDO: {deputy.get("siglaPartido")}
ESTADO: {deputy.get("siglaUf")}

DADOS DE VOTAÇÃO (últimas votações):
- Votou SIM: {vote_summary.get("Sim", 0)} vezes
- Votou NÃO: {vote_summary.get("Não", 0)} vezes
- Ausente: {vote_summary.get("Ausente", 0)} vezes
- Abstenção: {vote_summary.get("Abstenção", 0)} vezes
- Obstrução: {vote_summary.get("Obstrução", 0)} vezes

MÉTRICAS:
- Taxa de presença: {presence}%
- Alinhamento com a maioria da Câmara: {majority_alignment}%

DEPUTADOS QUE MAIS VOTAM IGUAL: {", ".join(most_aligned)}
DEPUTADOS QUE MAIS VOTAM DIFERENTE: {", ".join(least_aligned)}

ÚLTIMAS PROPOSIÇÕES APRESENTADAS:
{chr(10).join(f"- {p}" for p in prop_sample)}

Responda APENAS com um JSON válido, sem markdown, sem texto antes ou depois:
{{
  "posicionamento": {{
    "perfil": "governista | oposição | independente | centro",
    "temas": ["tema1", "tema2", "tema3"],
    "descricao": "2-3 frases sobre o posicionamento político"
  }},
  "coerencia": {{
    "nivel": "alta | média | baixa",
    "descricao": "2-3 frases explicando a coerência entre presença, votações e proposições"
  }},
  "resumo": "3-4 frases diretas resumindo o perfil político completo deste deputado"
}}"""

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        raw = response.choices[0].message.content.strip()
        import json
        analysis = json.loads(raw)
        return JsonResponse({"analysis": analysis})
    except Exception as e:
        return JsonResponse({"error": f"Erro na análise: {str(e)}"}, status=500)