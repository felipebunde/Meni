document.addEventListener('DOMContentLoaded', () => {

  // ===============================
  // CARREGA PEDIDO
  // ===============================
  let pedido = JSON.parse(localStorage.getItem('pedidoAtual'));

  if (!pedido || !pedido.itens || pedido.itens.length === 0) {
    alert('Pedido vazio. Volte ao cardápio.');
    window.location.href = '/cardapio';
    return;
  }

  document.getElementById('protocolo').textContent = pedido.protocolo;
  document.getElementById('total').textContent = pedido.total.toFixed(2);

  const itensDiv = document.getElementById('itens');

  pedido.itens.forEach(i => {
    const div = document.createElement('div');
    div.className = 'resumo-item';
    div.innerHTML = `
      <span>${i.nome} x${i.qtd}</span>
      <span>R$ ${(i.preco * i.qtd).toFixed(2)}</span>
    `;
    itensDiv.appendChild(div);
  });

  // ===============================
  // BUSCAR CLIENTE
  // ===============================
  document.getElementById('buscar').onclick = async () => {
    const telefone = document.getElementById('telefone').value.trim();
    if (!telefone) return;

    const res = await fetch(`/api/cliente/${telefone}`);
    const data = await res.json();

    document.getElementById('clienteInfo').classList.remove('hidden');

    if (!data.novo) {
      document.getElementById('nome').value = data.nome || '';
      document.getElementById('endereco').value = data.endereco || '';
      document.getElementById('observacoes').value = data.observacoes || '';
    }
  };

  // ===============================
  // GERAR PEDIDO
  // ===============================
  document.getElementById('gerarPedido').onclick = async (e) => {
    e.preventDefault(); // 👈 EVITA SUBMIT MALUCO

    const tipoSelecionado = document.querySelector(
      'input[name="tipo_pedido"]:checked'
    );

    if (!tipoSelecionado) {
      alert('Selecione se o pedido é Balcão ou Entrega');
      return;
    }

    const payload = {
      telefone: document.getElementById('telefone').value.trim(),
      nome: document.getElementById('nome').value.trim(),
      endereco: document.getElementById('endereco').value.trim(),
      observacoes: document.getElementById('observacoes').value.trim(),
      tipo: tipoSelecionado.value, // balcao | entrega
      pedido
    };

    const res = await fetch('/api/confirmar_pedido', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      alert('Erro ao gerar pedido');
      return;
    }

    localStorage.removeItem('pedidoAtual');
    window.location.href = '/';
  };

});
