function toggleAccordion(id) {
  const item = document.getElementById(id)
  item.classList.toggle("open")
}

async function generateRaioX() {
  const btn = document.getElementById("raiox-btn")
  const body = document.getElementById("raiox-body")
  const deputyId = new URLSearchParams(window.location.search).get("id")

  btn.disabled = true
  btn.textContent = "Analisando..."
  body.innerHTML = '<div class="raiox-loading">⚡ Gerando análise com IA...</div>'
  body.style.display = "block"
  body.classList.remove("visible")

  const response = await fetch(`/ai-analysis/?id=${deputyId}`)
  const data = await response.json()

  if (data.error) {
    body.innerHTML = `<div class="raiox-loading" style="color:var(--no)">${data.error}</div>`
    btn.disabled = false
    btn.textContent = "Tentar novamente"
    return
  }

  const { posicionamento, coerencia, resumo } = data.analysis
  const nivelClass = coerencia.nivel.toLowerCase().replace("é", "e")

  body.innerHTML = `
    <div class="raiox-card">
      <div class="raiox-card-title">Posicionamento</div>
      <div class="raiox-perfil">${posicionamento.perfil}</div>
      <div class="raiox-temas">
        ${posicionamento.temas.map(t => `<span class="raiox-tema">${t}</span>`).join("")}
      </div>
      <div class="raiox-desc">${posicionamento.descricao}</div>
    </div>

    <div class="raiox-card">
      <div class="raiox-card-title">Coerência</div>
      <div class="raiox-nivel ${nivelClass}">${coerencia.nivel}</div>
      <div class="raiox-desc">${coerencia.descricao}</div>
    </div>

    <div class="raiox-card">
      <div class="raiox-card-title">Resumo Executivo</div>
      <div class="raiox-desc">${resumo}</div>
    </div>
  `

  body.classList.add("visible")
  body.style.display = ""
  btn.textContent = "Regenerar"
  btn.disabled = false
}