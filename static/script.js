console.log("✅ NINA carregada");

let pedidoAtualId = null;

/* ===============================
   PEDIDOS
================================ */
async function carregarPedidos() {
  const res = await fetch('/api/pedidos');
  const pedidos = await res.json();

  document.querySelector('.preparo .lista').innerHTML = '';
  document.querySelector('.balcao .lista').innerHTML = '';
  document.querySelector('.entrega .lista').innerHTML = '';

  pedidos.forEach(p => {
    const card = document.createElement('div');
    card.className = 'card';
    card.onclick = () => abrirNota(p.id);

    card.innerHTML = `
      <div class="numero">Pedido #${p.id}</div>
      <div class="info">${p.nome}</div>
    `;

    if (p.status === 'em_andamento')
      document.querySelector('.preparo .lista').appendChild(card);

    if (p.status === 'pronto_balcao')
      document.querySelector('.balcao .lista').appendChild(card);

    if (p.status === 'pronto_entrega')
      document.querySelector('.entrega .lista').appendChild(card);
  });
}

/* ===============================
   NOTA
================================ */
async function abrirNota(id) {
  pedidoAtualId = id;

  const res = await fetch(`/api/pedido/${id}`);
  const data = await res.json();

  document.getElementById('notaInfo').innerHTML = `
    <strong>${data.pedido.nome}</strong><br>
    ${data.pedido.telefone}<br>
    ${data.pedido.tipo}
  `;

  const itens = document.getElementById('notaItens');
  itens.innerHTML = '';

  data.itens.forEach(i => {
    itens.innerHTML += `
      <div class="nota-item">
        <span>${i.nome}</span>
        <input type="number" min="0" value="${i.quantidade}"
          onchange="editarItem(${i.id}, this.value)">
        <span>R$ ${(i.preco_unitario * i.quantidade).toFixed(2)}</span>
      </div>
    `;
  });

  configurarBotoes(data.pedido.status);
  document.getElementById('notaModal').classList.remove('hidden');
}

async function editarItem(id, qtd) {
  await fetch(`/api/pedido/item/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quantidade: Number(qtd) })
  });
  abrirNota(pedidoAtualId);
}

function configurarBotoes(status) {
  const pronto = document.getElementById('btnPronto');
  const entregar = document.getElementById('btnEntregar');

  pronto.style.display = 'none';
  entregar.style.display = 'none';

  if (status === 'em_andamento') {
    pronto.style.display = 'inline-block';
    pronto.onclick = marcarPronto;
  }

  if (status.startsWith('pronto')) {
    entregar.style.display = 'inline-block';
    entregar.onclick = entregarPedido;
  }
}

async function marcarPronto() {
  await fetch(`/api/pedido/${pedidoAtualId}/pronto`, { method: 'POST' });
  fecharNota();
  carregarPedidos();
}

async function entregarPedido() {
  await fetch(`/api/pedido/${pedidoAtualId}/entregar`, { method: 'POST' });
  fecharNota();
  carregarPedidos();
}

function fecharNota() {
  document.getElementById('notaModal').classList.add('hidden');
  pedidoAtualId = null;
}

/* ===============================
   CLIENTE
================================ */
document.getElementById("clienteTelefone").addEventListener("keydown", e => {
  if (e.key === "Enter") buscarCliente(e.target.value);
});

function buscarCliente(telefone) {
  fetch(`/api/cliente/${telefone}/perfil`)
    .then(r => r.json())
    .then(data => {
      if (data.novo) return alert("Cliente novo");
      abrirCliente(data);
    });
}

function abrirCliente(data) {
  document.getElementById('clienteInfo').innerHTML = `
    <strong>${data.cliente.nome}</strong><br>
    📞 ${data.cliente.telefone}
  `;

  const pedidos = document.getElementById('clientePedidos');
  pedidos.innerHTML = '';

  data.pedidos.forEach(p => {
    pedidos.innerHTML += `
      <div class="pedido-historico">
        🧾 ${p.tipo} • R$ ${p.total.toFixed(2)}
        <button onclick="reutilizarPedido(${p.id})">🔁</button>
      </div>
    `;
  });

  document.getElementById('clienteModal').classList.remove('hidden');
}

function reutilizarPedido(id) {
  fetch(`/api/pedido/${id}/reutilizar`, { method: 'POST' })
    .then(() => fecharCliente());
}

function fecharCliente() {
  document.getElementById('clienteModal').classList.add('hidden');
}

/* ===============================
   NINA
================================ */
function abrirNina() {
  document.getElementById("ninaMenu").classList.remove("hidden");
}

function fecharNina() {
  document.getElementById("ninaMenu").classList.add("hidden");
}

function irPara(url) {
  window.location.href = url;
}

/* ===============================
   START
================================ */
carregarPedidos();
setInterval(carregarPedidos, 5000);
