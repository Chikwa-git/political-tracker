const selected = { a: null, b: null }

async function searchDeputy(panel) {
  const input = document.getElementById(`input-${panel}`)
  const resultsDiv = document.getElementById(`results-${panel}`)
  const name = input.value.trim()
  if (!name) return

  resultsDiv.innerHTML = '<div style="padding:1rem;font-family:monospace;font-size:0.7rem;color:#666">Buscando...</div>'
  resultsDiv.classList.add("visible")

  const response = await fetch(`/search/?name=${encodeURIComponent(name)}`)
  const data = await response.json()

  if (data.results.length === 0) {
    resultsDiv.innerHTML = '<div style="padding:1rem;font-family:monospace;font-size:0.7rem;color:#666">Nenhum resultado</div>'
    return
  }

  resultsDiv.innerHTML = data.results.map(d => `
    <div class="result-item" onclick="selectDeputy('${panel}', ${d.id}, '${d.nome.replace(/'/g, "\\'")}', '${d.siglaPartido}', '${d.siglaUf}', '${d.urlFoto}')">
      <img class="result-avatar" src="${d.urlFoto}" onerror="this.style.display='none'">
      <div>
        <div class="result-name">${d.nome}</div>
        <div class="result-meta">
          <span class="tag tag-party">${d.siglaPartido}</span>
          <span class="tag">${d.siglaUf}</span>
        </div>
      </div>
    </div>
  `).join("")
}

function selectDeputy(panel, id, nome, partido, uf, foto) {
  selected[panel] = { id, nome, partido, uf, foto }

  document.getElementById(`results-${panel}`).classList.remove("visible")
  document.getElementById(`form-${panel}`).style.display = "none"

  document.getElementById(`photo-${panel}`).src = foto
  document.getElementById(`name-${panel}`).textContent = nome
  document.getElementById(`meta-${panel}`).textContent = `${partido} · ${uf}`
  document.getElementById(`selected-${panel}`).classList.add("visible")

  if (selected.a && selected.b) {
    document.getElementById("compare-action").classList.add("visible")
  }
}

function clearSelection(panel) {
  selected[panel] = null
  document.getElementById(`selected-${panel}`).classList.remove("visible")
  document.getElementById(`form-${panel}`).style.display = "flex"
  document.getElementById(`input-${panel}`).value = ""
  document.getElementById("compare-action").classList.remove("visible")
  document.getElementById("compare-result").classList.remove("visible")
}

async function runComparison() {
  const resultDiv = document.getElementById("compare-result")
  resultDiv.innerHTML = '<div class="loading-state">Carregando dados...</div>'
  resultDiv.classList.add("visible")

  const [dataA, dataB] = await Promise.all([
    fetch(`/deputy-data/?id=${selected.a.id}`).then(r => r.json()),
    fetch(`/deputy-data/?id=${selected.b.id}`).then(r => r.json()),
  ])

  const presA = dataA.presence ?? "—"
  const presB = dataB.presence ?? "—"
  const majA = dataA.majority_alignment ?? "—"
  const majB = dataB.majority_alignment ?? "—"

  const presLower = typeof presA === "number" && typeof presB === "number" ? (presA < presB ? "a" : "b") : null
  const majLower  = typeof majA  === "number" && typeof majB  === "number" ? (majA  < majB  ? "a" : "b") : null

  resultDiv.innerHTML = `
    <div class="compare-grid">
      ${buildCol("a", dataA.deputy, presA, majA, presLower === "a", majLower === "a")}
      ${buildCol("b", dataB.deputy, presB, majB, presLower === "b", majLower === "b")}
    </div>
  `
}

function buildCol(panel, deputy, presence, majority, presLow, majLow) {
  return `
    <div class="compare-col">
      <div class="compare-deputy-header">
        <img class="compare-photo" src="${deputy.urlFoto}" onerror="this.style.display='none'">
        <div>
          <div class="compare-name">${deputy.nome}</div>
          <div class="compare-party">${deputy.siglaPartido} · ${deputy.siglaUf}</div>
        </div>
      </div>
      <div class="stat-row">
        <div>
          <div class="stat-label-text">Presença em votações</div>
          <div class="bar-track"><div class="bar-fill ${presLow ? 'lower' : ''}" style="width:${typeof presence === 'number' ? presence : 0}%"></div></div>
        </div>
        <div class="stat-val ${presLow ? 'lower' : ''}">${typeof presence === 'number' ? presence + '%' : '—'}</div>
      </div>
      <div class="stat-row">
        <div>
          <div class="stat-label-text">Alinhamento com maioria da Câmara</div>
          <div class="bar-track"><div class="bar-fill ${majLow ? 'lower' : ''}" style="width:${typeof majority === 'number' ? majority : 0}%"></div></div>
        </div>
        <div class="stat-val ${majLow ? 'lower' : ''}">${typeof majority === 'number' ? majority + '%' : '—'}</div>
      </div>
    </div>
  `
}

// Enter key nos inputs
document.getElementById("input-a").addEventListener("keydown", e => { if (e.key === "Enter") searchDeputy("a") })
document.getElementById("input-b").addEventListener("keydown", e => { if (e.key === "Enter") searchDeputy("b") })