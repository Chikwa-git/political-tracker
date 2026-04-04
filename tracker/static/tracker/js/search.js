const form = document.querySelector(".search-form");
const input = document.querySelector(".search-input");
const resultsSection = document.querySelector(".results-section");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = input.value.trim();
  if (!name) return;

  // Visual feedback while loading
  resultsSection.innerHTML = `
        <div class="empty-state">
            <p>Buscando...</p>
        </div>
    `;

  const response = await fetch(`/search/?name=${encodeURIComponent(name)}`);
  const data = await response.json();
  const results = data.results;

  if (results.length === 0) {
    resultsSection.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⊘</div>
                <p>Nenhum deputado encontrado</p>
            </div>
        `;
    return;
  }

  // Render cards
  const cards = results
    .map(
      (deputy) => `
        <a class="deputy-card" href="/deputy/?id=${deputy.id}">
            <img class="deputy-avatar" src="${deputy.urlFoto}" alt="${deputy.nome}" onerror="this.style.display='none'">
            <div class="deputy-info">
                <div class="deputy-name">${deputy.nome}</div>
                <div class="deputy-meta">
                    <span class="tag tag-party">${deputy.siglaPartido}</span>
                    <span class="tag">${deputy.siglaUf}</span>
                </div>
            </div>
            <span class="arrow">→</span>
        </a>
    `,
    )
    .join("");

  resultsSection.innerHTML = `
        <div class="results-header">
            <span class="results-label">Resultados encontrados</span>
            <span class="results-count">${results.length}</span>
        </div>
        <div class="results-grid">${cards}</div>
    `;
});


const params = new URLSearchParams(window.location.search)
const autoSearch = params.get("search")
if (autoSearch) {
  input.value = autoSearch
  input.dispatchEvent(new Event("input"))
  form.dispatchEvent(new Event("submit"))
}