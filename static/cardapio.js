let pedido = {};
let total = 0;

const grid = document.getElementById('produtos');
const lista = document.getElementById('listaPedido');
const totalEl = document.getElementById('total');
const btnFinalizar = document.getElementById('finalizar');

async function carregarProdutos() {
  const res = await fetch('/api/produtos');
  const produtos = await res.json();

  grid.innerHTML = '';

  produtos.forEach(p => {
    const card = document.createElement('div');
    card.className = 'card';

    card.innerHTML = `
      <img src="/static/produtos/${p.imagem}" alt="${p.nome}">
      <h3>${p.nome}</h3>
      <span>R$ ${p.preco.toFixed(2)}</span>
    `;

    card.onclick = () => adicionarProduto(p);

    grid.appendChild(card);
  });
}

function adicionarProduto(produto) {
  if (!pedido[produto.id]) {
    pedido[produto.id] = { ...produto, qtd: 1 };
  } else {
    pedido[produto.id].qtd++;
  }
  renderPedido();
}

function removerProduto(id) {
  pedido[id].qtd--;
  if (pedido[id].qtd <= 0) {
    delete pedido[id];
  }
  renderPedido();
}

function renderPedido() {
  lista.innerHTML = '';
  total = 0;

  Object.values(pedido).forEach(p => {
    total += p.preco * p.qtd;

    const item = document.createElement('div');
    item.className = 'item';

    item.innerHTML = `
      <span>${p.nome}</span>
      <div class="controles">
        <button class="menos">−</button>
        <span>${p.qtd}</span>
        <button class="mais">+</button>
      </div>
    `;

    item.querySelector('.mais').onclick = () => adicionarProduto(p);
    item.querySelector('.menos').onclick = () => removerProduto(p.id);

    lista.appendChild(item);
  });

  totalEl.textContent = total.toFixed(2);
  btnFinalizar.onclick = () => {
  abrirCheckout();
};
}

carregarProdutos();
let protocolo = null;

async function iniciarPedido() {
  const res = await fetch('/api/novo_protocolo');
  const data = await res.json();
  protocolo = data.protocolo;

  document.title = `Pedido ${protocolo}`;
}

iniciarPedido();

function abrirCheckout() {
  // Monta o pedido atual em formato serializável
  const pedidoAtual = {
    protocolo: protocolo || 'TEMP',
    itens: Object.values(pedido).map(p => ({
      id: p.id,
      nome: p.nome,
      preco: p.preco,
      qtd: p.qtd
    })),
    total
  };

  // Salva no localStorage (ponte entre telas)
  localStorage.setItem('pedidoAtual', JSON.stringify(pedidoAtual));

  // Vai para o checkout
  window.location.href = '/checkout';
}
