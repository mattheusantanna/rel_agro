import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import io
import os
import uuid

# ===== HEADER DEFAULT =====
DEFAULT_HEADER_PATH = "header.png"

def carregar_header_padrao():
    if os.path.exists(DEFAULT_HEADER_PATH):
        with open(DEFAULT_HEADER_PATH, "rb") as f:
            return f.read()
    return None

# ===== CONFIG PDF =====
PAGE_WIDTH, PAGE_HEIGHT = A4
HEADER_H    = 120
MARGIN_BOT  = 40
GAP         = 30
TITLE_SPACE = 25

usable_h  = PAGE_HEIGHT - HEADER_H - MARGIN_BOT
BOX_H     = (usable_h - GAP) / 2
IMG_Y_TOP = MARGIN_BOT + BOX_H + GAP
IMG_Y_BOT = MARGIN_BOT
TITLE_Y   = PAGE_HEIGHT - 110

# ===== DADOS =====
ESTRUTURA = {
    "Avaliação do Campo de Produção": [
        "PROPRIEDADE",
        "VISTA 1 – TALHÃO AUDITADO",
        "VISTA 2 – TALHÃO AUDITADO",
    ],
    "Colheita – Operação e Máquinas": [
        "GRANELEIRO VÁZIO – COLHEDORA",
        "CAMINHÃO 1 – CAÇAMBA VÁZIA",
    ],
    "Transbordo de Produção Auditada": [
        "CAMINHÕES – PLACA FRONTAL",
        "PESO DE ENTRADA",
        "CERTIFICADO DE CALIBRAÇÃO",
    ],
}

# ===== PDF =====
def desenhar_cabecalho(c, header_bytes):
    if header_bytes is None:
        return
    img = Image.open(io.BytesIO(header_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    w, h  = img.size
    scale = PAGE_WIDTH / w
    buf   = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    c.drawImage(ImageReader(buf), 0, PAGE_HEIGHT - h * scale,
                width=PAGE_WIDTH, height=h * scale)

def desenhar_imagem(c, img_bytes, y_base, box_h, topico):
    img = Image.open(io.BytesIO(img_bytes))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    iw, ih = img.size
    max_w  = PAGE_WIDTH - 80
    max_h  = box_h - TITLE_SPACE - 10
    ratio  = min(max_w / iw, max_h / ih)
    nw, nh = iw * ratio, ih * ratio
    x      = (PAGE_WIDTH - nw) / 2
    y      = y_base + TITLE_SPACE + (max_h - nh) / 2
    buf    = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    c.drawImage(ImageReader(buf), x, y, width=nw, height=nh)
    c.setFont("Helvetica", 10)
    c.drawCentredString(PAGE_WIDTH / 2, y_base + 5, topico)

def gerar_pdf(itens, header_bytes):
    buf = io.BytesIO()
    c   = pdf_canvas.Canvas(buf, pagesize=A4)

    sessoes = {}
    for item in itens:
        sessoes.setdefault(item["sessao"], []).append(item)

    for sessao, lista in sessoes.items():
        for i in range(0, len(lista), 2):
            desenhar_cabecalho(c, header_bytes)
            if i == 0:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, TITLE_Y, sessao)
            for j, y_pos in enumerate([IMG_Y_TOP, IMG_Y_BOT]):
                if i + j >= len(lista):
                    break
                item = lista[i + j]
                desenhar_imagem(c, item["bytes"], y_pos, BOX_H, item["topico"])
            c.showPage()

    c.save()
    buf.seek(0)
    return buf

# ===== UI =====
st.set_page_config(
    page_title="Relatório Fotográfico",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Relatório Fotográfico")
st.caption("Auditoria de Campo · Configure as seções e gere o PDF")
st.divider()

# ── Cabeçalho ─────────────────────
with st.expander("🖼️ Cabeçalho do PDF"):
    header_file = st.file_uploader("Substituir cabeçalho", type=["png","jpg","jpeg"])
    if header_file:
        header_bytes = header_file.read()
        st.image(header_bytes, use_container_width=True)
    else:
        header_bytes = carregar_header_padrao()

# ── Estado ─────────────────────
if "itens" not in st.session_state:
    st.session_state.itens = []

if "preview_aberto" not in st.session_state:
    st.session_state.preview_aberto = set()

# ── UI ─────────────────────
colunas = st.columns(3)

for col_idx, (nome_secao, topicos) in enumerate(ESTRUTURA.items()):
    with colunas[col_idx]:

        st.markdown(f"**{nome_secao}**")

        topico_sel = st.selectbox(
            "Tópico",
            topicos,
            key=f"sel_{col_idx}",
            label_visibility="collapsed"
        )

        if st.button("＋ Adicionar", key=f"add_{col_idx}"):
            st.session_state.itens.append({
                "id": str(uuid.uuid4()),
                "sessao": nome_secao,
                "topico": topico_sel,
                "bytes": None,
            })
            st.rerun()

        st.markdown("---")

        for idx, item in enumerate(st.session_state.itens):
            if item["sessao"] != nome_secao:
                continue

            uid = item["id"]
            bytes_key = f"bytes_{uid}"

            col_nome, col_toggle = st.columns([5,1])

            with col_nome:
                status = "✓" if item["bytes"] else "○"
                st.markdown(f"{status} **{item['topico']}**")

            with col_toggle:
                aberto = uid in st.session_state.preview_aberto
                if st.button("▲" if aberto else "▼", key=f"tg_{uid}"):
                    if aberto:
                        st.session_state.preview_aberto.discard(uid)
                    else:
                        st.session_state.preview_aberto.add(uid)
                    st.rerun()

            uploaded = st.file_uploader(
                "Imagem",
                type=["jpg","png","jpeg"],
                key=f"img_{uid}",
                label_visibility="collapsed"
            )

            # ✅ lógica correta
            if uploaded is not None:
                file_bytes = uploaded.read()
                st.session_state[bytes_key] = file_bytes

            item["bytes"] = st.session_state.get(bytes_key, None)

            # preview
            if uid in st.session_state.preview_aberto:
                if item["bytes"]:
                    st.image(item["bytes"], use_container_width=True)
                else:
                    st.caption("Nenhuma imagem")

            # ações
            c1, c2, c3 = st.columns(3)

            with c1:
                if st.button("↑", key=f"up_{uid}") and idx > 0:
                    st.session_state.itens[idx], st.session_state.itens[idx-1] = \
                    st.session_state.itens[idx-1], st.session_state.itens[idx]
                    st.rerun()

            with c2:
                if st.button("↓", key=f"dn_{uid}") and idx < len(st.session_state.itens)-1:
                    st.session_state.itens[idx], st.session_state.itens[idx+1] = \
                    st.session_state.itens[idx+1], st.session_state.itens[idx]
                    st.rerun()

            with c3:
                if st.button("🗑", key=f"rm_{uid}"):
                    st.session_state.itens.pop(idx)
                    st.session_state.preview_aberto.discard(uid)
                    st.session_state.pop(bytes_key, None)
                    st.rerun()

# ── PDF ─────────────────────
st.divider()

validos = [i for i in st.session_state.itens if i.get("bytes")]

if st.button("📄 Gerar PDF", disabled=len(validos)==0):
    pdf = gerar_pdf(validos, header_bytes)
    st.download_button("⬇ Baixar", pdf, "relatorio.pdf")
