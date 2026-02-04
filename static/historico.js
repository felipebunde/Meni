document.addEventListener("DOMContentLoaded", () => {
  fetch("/api/historico")
    .then(r => r.json())
    .then(data => {
      const lista = document.getElementById("listaHistorico");
      lista.innerHTML = "";

      data.forEach(p => {
        const div = document.createElement("div");
        div.className = "card historico-card";

        div.innerHTML = `
          <div class="linha">
            <strong>${p.nome}</strong>
            <span>🧾 #${p.id}</span>
          </div>

          <div class="linha">
            📞 ${p.telefone}
          </div>

          <div class="linha destaque">
            ${p.tipo.toUpperCase()} • R$ ${p.total.toFixed(2)}
          </div>
        `;

        lista.appendChild(div);
      });
    });
});
