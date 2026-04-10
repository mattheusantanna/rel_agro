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
        "ARQUITETURA DE PLANTA",
        "AFERIÇÃO DA TAXA DE SEMEADURA EFETIVA (1 METRO) – PONTO 1",
        "AFERIÇÃO DA TAXA DE SEMEADURA EFETIVA (1 METRO) – PONTO 2",
        "AFERIÇÃO DA TAXA DE SEMEADURA EFETIVA (1 METRO) – PONTO 3",
        "ALTURA DE INSERÇÃO DE 1ª VAGEM",
        "ESPAÇAMENTO ENTRE LINHAS",
        "NÚMERO DE GRÃOS POR VAGEM",
    ],
    "Colheita – Operação e Máquinas": [
        "GRANELEIRO VÁZIO – COLHEDORA",
        "CAMINHÃO 1 – CAÇAMBA VÁZIA (VISTA FRONTAL)",
        "COLHEDORA – VISTA LATERAL",
        "PERDA DE PRODUTIVIDADE",
    ],
    "Transbordo de Produção Auditada": [
        "CAMINHÕES – PLACA FRONTAL",
        "CAMINHÕES – PLACA TRASEIRA",
        "LACRES - FIXAÇÃO",
        "LACRE - ROMPIMENTO",
        "PESAGEM DO CAMINHÃO - VEÍCULO SOB A BALANÇA (VISTA FRONTAL)",
        "PESAGEM DO CAMINHÃO – VEÍCULO SOB A BALANÇA (VISTA TRASEIRA)",
        "PESO DE ENTRADA",
        "CERTIFICADO DE CALIBRAÇÃO",
        "MEDIDOR DE UMIDADE – DISPLAY",
        "IMPUREZA",
        "PESO DE SAIDA",
        "ROMANEIO DE CARGA",
        "AMOSTRA DE MATÉRIA SECA",
        "PESO DE 1.000 GRÃOS – AMOSTRA 1",
        "PESO DE 1.000 GRÃOS – AMOSTRA 2",
        "PESO DE 1.000 GRÃOS – AMOSTRA 3",
        "AFERIÇÃO DE GPS- MEDIÇÃO 1",
        "AFERIÇÃO DE GPS- MEDIÇÃO 2",
        "AFERIÇÃO DE GPS- MEDIÇÃO 3",
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
                numero = lista.index(item) + 1
                topico_numerado = f"{numero}. {item['topico']}"
                desenhar_imagem(c, item["bytes"], y_pos, BOX_H, topico_numerado)
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

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .stButton > button { border-radius: 8px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ── Título ──────────────────────────────────────────────
st.title("📋 Relatório Fotográfico")
st.caption("Auditoria de Campo · Configure as seções e gere o PDF")
st.divider()

# ── Cabeçalho do PDF ──────────────────────────────────────────────
with st.expander("🖼️ Cabeçalho do PDF", expanded=False):
    header_file = st.file_uploader(
        "Substituir cabeçalho (opcional)",
        type=["png", "jpg", "jpeg"],
        key="header"
    )
    if header_file:
        header_file.seek(0)
        header_bytes = header_file.read()
        st.image(io.BytesIO(header_bytes), use_container_width=True)
        st.caption("✓ Usando cabeçalho enviado")
    else:
        header_bytes = carregar_header_padrao()
        if header_bytes:
            st.image(io.BytesIO(header_bytes), use_container_width=True)
            st.caption("✓ Usando cabeçalho padrão · Envie um arquivo acima para substituir")
        else:
            st.caption("Nenhum cabeçalho encontrado. Envie uma imagem ou adicione header.png ao projeto.")

# ── Inicializa estado ──────────────────────────────────────────────
if "itens" not in st.session_state:
    st.session_state.itens = []

if "preview_aberto" not in st.session_state:
    st.session_state.preview_aberto = set()

# ── Seções ──────────────────────────────────────────────
colunas = st.columns(3)

for col_idx, (nome_secao, topicos) in enumerate(ESTRUTURA.items()):
    with colunas[col_idx]:
        itens_secao = [i for i in st.session_state.itens if i["sessao"] == nome_secao]
        com_img     = sum(1 for i in itens_secao if i.get("bytes"))

        st.markdown(f"**{nome_secao}**")
        st.caption(f"{len(itens_secao)} tópico(s) · {com_img} imagem(ns)")

        topico_sel = st.selectbox(
            "Tópico",
            topicos,
            key=f"sel_{col_idx}",
            label_visibility="collapsed"
        )

        if st.button("＋ Adicionar tópico", key=f"add_{col_idx}", use_container_width=True):
            st.session_state.itens.append({
                "id":     str(uuid.uuid4()),
                "sessao": nome_secao,
                "topico": topico_sel,
                "bytes":  None,
                "nome":   None,
            })
            st.rerun()

        st.markdown("---")

        for global_idx, item in enumerate(st.session_state.itens):
            if item["sessao"] != nome_secao:
                continue

            uid = item["id"]

            # Linha com nome do tópico e botão de toggle
        with col_nome:
            # calcula índice do item dentro da seção
                itens_da_secao = [i for i in st.session_state.itens if i["sessao"] == nome_secao]
                numero = itens_da_secao.index(item) + 1
            
                tem_img = "✓" if item["bytes"] else "○"
                st.markdown(f"{tem_img} **{numero}. {item['topico']}**")
        
            tem_img = "✓" if item["bytes"] else "○"
            st.markdown(f"{tem_img} **{numero}. {item['topico']}**")
            with col_toggle:
                aberto = uid in st.session_state.preview_aberto
                label  = "▲" if aberto else "▼"
                if st.button(label, key=f"toggle_{uid}"):
                    if aberto:
                        st.session_state.preview_aberto.discard(uid)
                    else:
                        st.session_state.preview_aberto.add(uid)
                    st.rerun()

            # Upload sempre visível
            uploaded = st.file_uploader(
                "Imagem",
                type=["jpg", "jpeg", "png"],
                key=f"img_{uid}",
                label_visibility="collapsed"
            )
            if uploaded:
                item["bytes"] = uploaded.read()
                item["nome"]  = uploaded.name

            # Preview apenas se aberto
            if uid in st.session_state.preview_aberto:
                if item["bytes"]:
                    st.image(io.BytesIO(item["bytes"]), use_container_width=True)
                else:
                    st.caption("⬆ Nenhuma imagem selecionada ainda")

            # Botões de ação
            btn_cols = st.columns([1, 1, 1, 2])
            with btn_cols[0]:
                if st.button("↑", key=f"up_{uid}") and global_idx > 0:
                    l = st.session_state.itens
                    l[global_idx], l[global_idx - 1] = l[global_idx - 1], l[global_idx]
                    st.rerun()
            with btn_cols[1]:
                if st.button("↓", key=f"dn_{uid}") and global_idx < len(st.session_state.itens) - 1:
                    l = st.session_state.itens
                    l[global_idx], l[global_idx + 1] = l[global_idx + 1], l[global_idx]
                    st.rerun()
            with btn_cols[3]:
                if st.button("Remover", key=f"rm_{uid}", type="secondary"):
                    st.session_state.itens.pop(global_idx)
                    st.session_state.preview_aberto.discard(uid)
                    st.rerun()

            st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ── Gerar PDF ──────────────────────────────────────────────
st.divider()

validos = [i for i in st.session_state.itens if i.get("bytes")]
total   = len(st.session_state.itens)

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.caption(f"{total} tópico(s) adicionado(s) · {len(validos)} com imagem")

with col_btn:
    if st.button("📄 Gerar PDF", type="primary", use_container_width=True, disabled=len(validos) == 0):
        with st.spinner("Gerando PDF…"):
            pdf_buf = gerar_pdf(validos, header_bytes)
        st.success("PDF gerado com sucesso!")
        st.download_button(
            label="⬇ Baixar PDF",
            data=pdf_buf,
            file_name="relatorio_fotografico.pdf",
            mime="application/pdf",
            use_container_width=True
        )
