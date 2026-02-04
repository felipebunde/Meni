from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime
import random
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
DB = "hotdog.db"

UPLOAD_FOLDER = "static/produtos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ======================================================
# BANCO
# ======================================================

def get_db():
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ======================================================
# FUNÇÕES AUXILIARES (NOVAS – NECESSÁRIAS)
# ======================================================

def get_cliente_por_telefone(telefone):
    db = get_db()
    cliente = db.execute("""
        SELECT id, nome, telefone, endereco, observacoes
        FROM clientes
        WHERE telefone = ?
    """, (telefone,)).fetchone()
    db.close()
    return dict(cliente) if cliente else None


def get_ultimos_pedidos_do_cliente(cliente_id, limite=5):
    db = get_db()
    rows = db.execute("""
        SELECT
            p.id,
            p.tipo,
            p.status,
            p.id as data,
            SUM(pi.quantidade * pi.preco_unitario) AS total
        FROM pedidos p
        JOIN pedido_itens pi ON pi.pedido_id = p.id
        WHERE p.cliente_id = ?
          AND p.status = 'entregue'
        GROUP BY p.id
        ORDER BY p.id DESC
        LIMIT ?
    """, (cliente_id, limite)).fetchall()
    db.close()
    return [dict(r) for r in rows]


def clonar_pedido(pedido_id):
    db = get_db()

    pedido = db.execute("""
        SELECT cliente_id, tipo
        FROM pedidos
        WHERE id = ?
    """, (pedido_id,)).fetchone()

    if not pedido:
        db.close()
        raise Exception("Pedido não encontrado")

    cur = db.execute("""
        INSERT INTO pedidos (cliente_id, tipo, status)
        VALUES (?, ?, 'em_andamento')
    """, (pedido["cliente_id"], pedido["tipo"]))

    novo_pedido_id = cur.lastrowid

    itens = db.execute("""
        SELECT produto_id, quantidade, preco_unitario
        FROM pedido_itens
        WHERE pedido_id = ?
    """, (pedido_id,)).fetchall()

    for i in itens:
        db.execute("""
            INSERT INTO pedido_itens
            (pedido_id, produto_id, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?)
        """, (
            novo_pedido_id,
            i["produto_id"],
            i["quantidade"],
            i["preco_unitario"]
        ))

    db.commit()
    db.close()
    return novo_pedido_id


# ======================================================
# PÁGINAS
# ======================================================

@app.route("/")
def painel():
    return render_template("index.html")


@app.route("/cardapio")
def cardapio():
    return render_template("cardapio.html")


@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


# ======================================================
# API — LISTAR PEDIDOS (PAINEL)
# ======================================================

@app.route("/api/pedidos")
def api_pedidos():
    db = get_db()
    rows = db.execute("""
        SELECT
            p.id,
            p.tipo,
            p.status,
            c.nome
        FROM pedidos p
        JOIN clientes c ON c.id = p.cliente_id
        WHERE p.status != 'entregue'
        ORDER BY p.id
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ======================================================
# API — PRODUTOS
# ======================================================

@app.route("/api/produtos")
def api_produtos():
    db = get_db()
    rows = db.execute("""
        SELECT id, nome, preco, imagem
        FROM produtos
        WHERE ativo = 1
        ORDER BY nome
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# ======================================================
# API — CLIENTE SIMPLES (CHECKOUT)
# ======================================================

@app.route("/api/cliente/<telefone>")
def api_cliente(telefone):
    db = get_db()
    cliente = db.execute("""
        SELECT *
        FROM clientes
        WHERE telefone = ?
    """, (telefone,)).fetchone()
    db.close()

    if cliente:
        return jsonify(dict(cliente))
    return jsonify({"novo": True})


# ======================================================
# API — PERFIL DO CLIENTE (NOVO)
# ======================================================

@app.route("/api/cliente/<telefone>/perfil")
def perfil_cliente(telefone):
    cliente = get_cliente_por_telefone(telefone)

    if not cliente:
        return jsonify({"novo": True})

    pedidos = get_ultimos_pedidos_do_cliente(cliente["id"])

    return jsonify({
        "cliente": cliente,
        "pedidos": pedidos
    })


# ======================================================
# API — NOVO PROTOCOLO
# ======================================================

@app.route("/api/novo_protocolo")
def novo_protocolo():
    protocolo = f"PED-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
    return jsonify({"protocolo": protocolo})


# ======================================================
# API — CONFIRMAR PEDIDO (CRIA EM ANDAMENTO)
# ======================================================

@app.route("/api/confirmar_pedido", methods=["POST"])
def confirmar_pedido():
    data = request.json

    telefone = data.get("telefone")
    nome = data.get("nome", "Cliente")
    endereco = data.get("endereco")
    observacoes = data.get("observacoes")
    tipo = data.get("tipo")
    pedido = data.get("pedido")

    if not telefone or not tipo or not pedido or not pedido.get("itens"):
        return jsonify({"erro": "Dados inválidos"}), 400

    db = get_db()

    cliente = db.execute(
        "SELECT id FROM clientes WHERE telefone = ?",
        (telefone,)
    ).fetchone()

    if cliente:
        cliente_id = cliente["id"]
        db.execute("""
            UPDATE clientes
            SET nome = ?, endereco = ?, observacoes = ?
            WHERE id = ?
        """, (nome, endereco, observacoes, cliente_id))
    else:
        cur = db.execute("""
            INSERT INTO clientes (telefone, nome, endereco, observacoes)
            VALUES (?, ?, ?, ?)
        """, (telefone, nome, endereco, observacoes))
        cliente_id = cur.lastrowid

    cur = db.execute("""
        INSERT INTO pedidos (cliente_id, tipo, status)
        VALUES (?, ?, 'em_andamento')
    """, (cliente_id, tipo))

    pedido_id = cur.lastrowid

    for item in pedido["itens"]:
        db.execute("""
            INSERT INTO pedido_itens
            (pedido_id, produto_id, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?)
        """, (
            pedido_id,
            item["id"],
            item["qtd"],
            item["preco"]
        ))

    db.commit()
    db.close()

    return jsonify({"ok": True, "pedido_id": pedido_id})


# ======================================================
# API — PEDIDO (VISUALIZAÇÃO / EDIÇÃO)
# ======================================================

@app.route("/api/pedido/<int:pedido_id>")
def api_pedido(pedido_id):
    db = get_db()

    pedido = db.execute("""
        SELECT p.id, p.status, p.tipo, c.nome, c.telefone
        FROM pedidos p
        JOIN clientes c ON c.id = p.cliente_id
        WHERE p.id = ?
    """, (pedido_id,)).fetchone()

    itens = db.execute("""
        SELECT
            pi.id,
            pr.nome,
            pi.quantidade,
            pi.preco_unitario
        FROM pedido_itens pi
        JOIN produtos pr ON pr.id = pi.produto_id
        WHERE pi.pedido_id = ?
    """, (pedido_id,)).fetchall()

    db.close()

    return jsonify({
        "pedido": dict(pedido),
        "itens": [dict(i) for i in itens]
    })


@app.route("/api/pedido/item/<int:item_id>", methods=["PUT"])
def atualizar_item(item_id):
    data = request.json
    qtd = data.get("quantidade")

    db = get_db()

    if qtd <= 0:
        db.execute("DELETE FROM pedido_itens WHERE id = ?", (item_id,))
    else:
        db.execute("""
            UPDATE pedido_itens
            SET quantidade = ?
            WHERE id = ?
        """, (qtd, item_id))

    db.commit()
    db.close()

    return {"ok": True}


# ======================================================
# API — STATUS DO PEDIDO (SEM DUPLICAÇÃO)
# ======================================================

@app.route("/api/pedido/<int:pedido_id>/pronto", methods=["POST"])
def marcar_pronto(pedido_id):
    db = get_db()

    pedido = db.execute(
        "SELECT tipo FROM pedidos WHERE id = ?",
        (pedido_id,)
    ).fetchone()

    if not pedido:
        return jsonify({"erro": "Pedido não encontrado"}), 404

    novo_status = (
        "pronto_balcao"
        if pedido["tipo"] == "balcao"
        else "pronto_entrega"
    )

    db.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id)
    )

    db.commit()
    db.close()

    return jsonify({"ok": True})


@app.route("/api/pedido/<int:pedido_id>/entregar", methods=["POST"])
def entregar_pedido(pedido_id):
    db = get_db()
    db.execute(
        "UPDATE pedidos SET status = 'entregue' WHERE id = ?",
        (pedido_id,)
    )
    db.commit()
    db.close()
    return jsonify({"ok": True})


# ======================================================
# API — REUTILIZAR PEDIDO (NOVO)
# ======================================================

@app.route("/api/pedido/<int:pedido_id>/reutilizar", methods=["POST"])
def reutilizar_pedido(pedido_id):
    novo_pedido_id = clonar_pedido(pedido_id)
    return jsonify({"pedido_id": novo_pedido_id})


# ======================================================
# Histórico
# ======================================================

@app.route("/historico")
def historico():
    return render_template("historico.html")
@app.route("/api/historico")
def api_historico():
    db = get_db()
    rows = db.execute("""
        SELECT
            p.id,
            p.tipo,
            p.status,
            c.nome,
            c.telefone,
            SUM(pi.quantidade * pi.preco_unitario) AS total
        FROM pedidos p
        JOIN clientes c ON c.id = p.cliente_id
        JOIN pedido_itens pi ON pi.pedido_id = p.id
        WHERE p.status = 'entregue'
        GROUP BY p.id
        ORDER BY p.id DESC
        LIMIT 100
    """).fetchall()
    db.close()

    return jsonify([dict(r) for r in rows])

@app.route("/produtos")
def novo_produto():
    return render_template("produtos.html")

@app.route("/api/produtos", methods=["POST"])
def criar_produto():
    db = get_db()

    codigo = request.form.get("codigo")
    nome = request.form.get("nome")
    custo = request.form.get("custo")
    preco = request.form.get("preco")
    observacoes = request.form.get("observacoes", "")

    imagem_file = request.files.get("imagem")
    imagem_nome = None

    if imagem_file:
        imagem_nome = secure_filename(imagem_file.filename)
        caminho = os.path.join(UPLOAD_FOLDER, imagem_nome)
        imagem_file.save(caminho)

    db.execute("""
        INSERT INTO produtos
        (codigo, nome, custo, preco, observacoes, imagem, ativo, disponivel, ordem)
        VALUES (?, ?, ?, ?, ?, ?, 1, 1, 999)
    """, (
        codigo,
        nome,
        custo,
        preco,
        observacoes,
        imagem_nome
    ))

    db.commit()
    db.close()

    return jsonify({"ok": True})

@app.route("/api/produtos/<int:produto_id>", methods=["PUT"])
def editar_produto(produto_id):
    data = request.json

    nome = data.get("nome")
    preco = data.get("preco")
    ativo = data.get("ativo")

    db = get_db()
    db.execute("""
        UPDATE produtos
        SET nome = ?, preco = ?, ativo = ?
        WHERE id = ?
    """, (
        nome,
        preco,
        ativo,
        produto_id
    ))
    db.commit()
    db.close()

    return jsonify({"ok": True})

@app.route("/api/produtos/<int:produto_id>/toggle", methods=["POST"])
def toggle_produto(produto_id):
    db = get_db()
    db.execute("""
        UPDATE produtos
        SET ativo = CASE WHEN ativo = 1 THEN 0 ELSE 1 END
        WHERE id = ?
    """, (produto_id,))
    db.commit()
    db.close()

    return jsonify({"ok": True})

@app.route("/api/produtos/<int:produto_id>/ordem", methods=["POST"])
def atualizar_ordem_produto(produto_id):
    data = request.json
    nova_ordem = data.get("ordem")

    db = get_db()
    db.execute("""
        UPDATE produtos
        SET ordem = ?
        WHERE id = ?
    """, (nova_ordem, produto_id))
    db.commit()
    db.close()

    return jsonify({"ok": True})



# ======================================================
# CARDAPIO-GESTAO
# ======================================================
@app.route("/api/produtos/gestao")
def api_produtos_gestao():
    db = get_db()
    rows = db.execute("""
        SELECT id, nome, preco, ativo
        FROM produtos
        ORDER BY nome
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/produtos/<int:id>/ativo", methods=["PUT"])
def atualizar_produto_ativo(id):
    ativo = request.json.get("ativo")
    db = get_db()
    db.execute("UPDATE produtos SET ativo = ? WHERE id = ?", (ativo, id))
    db.commit()
    db.close()
    return jsonify({"ok": True})


# ======================================================
# START
# ======================================================

if __name__ == "__main__":
    app.run(debug=True)
