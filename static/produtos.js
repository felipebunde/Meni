document.addEventListener("DOMContentLoaded", carregarProdutos);

async function carregarProdutos() {
  const res = await fetch("/api/produtos/gestao");
  const produtos = await res.json();

  const lista = document.getElementById("listaProdutos");
  lista.innerHTML = "";

  produtos.forEach(p => {
    const card = document.createElement("div");
    card.className = "card";
    if (!p.ativo) card.classList.add("inativo");

    card.innerHTML = `
      <div class="card-header">
        <strong>${p.nome}</strong>
        <span class="preco">R$ ${p.preco.toFixed(2)}</span>
      </div>

      <div class="card-body">
        <span class="status ${p.ativo ? "on" : "off"}">
          ${p.ativo ? "Ativo" : "Inativo"}
        </span>
      </div>

      <div class="acoes">
        <button onclick="toggleAtivo(${p.id}, ${p.ativo})">
          ${p.ativo ? "Desativar" : "Ativar"}
        </button>
        <button disabled>Editar</button>
        <button disabled>Excluir</button>
      </div>
    `;

    lista.appendChild(card);
  });
}

async function toggleAtivo(id, ativoAtual) {
  await fetch(`/api/produtos/${id}/ativo`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ativo: ativoAtual ? 0 : 1 })
  });

  carregarProdutos();
}
