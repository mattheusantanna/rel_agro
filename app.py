import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageOps
import io
import os
import uuid

# ===== HEADER DEFAULT =====
DEFAULT_HEADER_PATH = "header.png"
MAX_UPLOAD_MB       = 10
IMG_MAX_PX          = 1200
IMG_QUALIDADE       = 82
THUMB_MAX_PX        = 400

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
        "REPONSÁVEL POR ACOMPANHAR A AUDITORIA",
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

# ===== UTILS =====
def processar_imagem_upload(img_bytes):
    """Reduz para resolução adequada ao PDF, corrige orientação EXIF e comprime na entrada."""
    try:
        img = Image.open(io.BytesIO(img_bytes))
        img = ImageOps.exif_transpose(img)  # ✅ corrige orientação EXIF
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((IMG_MAX_PX, IMG_MAX_PX), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=IMG_QUALIDADE, optimize=True)
        buf.seek(0)
        return buf.read()
    except Exception:
        return img_bytes

def gerar_thumbnail(img_bytes):
    """Gera versão pequena para preview na UI."""
    try:
        img = Image.open(io.BytesIO(img_bytes))
        img = ImageOps.exif_transpose(img)  # ✅ corrige orientação EXIF
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((THUMB_MAX_PX, THUMB_MAX_PX), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        buf.seek(0)
        return buf.read()
    except Exception:
        return img_bytes

# ===== PDF =====
def desenhar_cabecalho(c, header_bytes):
    if header_bytes is None:
        return
    try:
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
    except Exception:
        pass  # Cabeçalho opcional — continua sem ele se falhar

def desenhar_imagem(c, img_bytes, y_base, box_h, topico):
    img = Image.open(io.BytesIO(img_bytes))
    img = ImageOps.exif_transpose(img)  # ✅ corrige orientação EXIF no PDF
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    iw, ih = img.size

    MARGIN_X = 40
    LABEL_H  = 18
    PADDING  = 6

    box_x = MARGIN_X
    box_w = PAGE_WIDTH - 2 * MARGIN_X
    box_y = y_base

    img_area_w = box_w - 2 * PADDING
    img_area_h = box_h - LABEL_H - 2 * PADDING

    ratio  = min(img_area_w / iw, img_area_h / ih)
    nw, nh = iw * ratio, ih * ratio

    img_x = box_x + PADDING + (img_area_w - nw) / 2
    img_y = box_y + LABEL_H + PADDING + (img_area_h - nh) / 2

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    c.drawImage(ImageReader(buf), img_x, img_y, width=nw, height=nh)

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8)
    c.rect(box_x, box_y, box_w, box_h)
    c.line(box_x, box_y + LABEL_H, box_x + box_w, box_y + LABEL_H)

    c.setFont("Helvetica-Bold", 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(box_x + PADDING, box_y + 5, topico)

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
                item            = lista[i + j]
                numero          = item["numero"]
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
            header_bytes = None
            st.caption("Nenhum cabeçalho encontrado. Envie uma imagem ou adicione header.png ao projeto.")

# ── Inicializa estado ──────────────────────────────────────────────
if "itens" not in st.session_state:
    st.session_state.itens = []

if "preview_aberto" not in st.session_state:
    st.session_state.preview_aberto = set()

# ── Botão limpar tudo ──────────────────────────────────────────────
if st.session_state.itens:
    if st.button("🗑️ Limpar tudo", type="secondary"):
        for item in st.session_state.itens:
            uid = item["id"]
            st.session_state.pop(f"bytes_{uid}", None)
            st.session_state.pop(f"thumb_{uid}", None)
        st.session_state.itens          = []
        st.session_state.preview_aberto = set()
        st.rerun()

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

            uid       = item["id"]
            bytes_key = f"bytes_{uid}"
            thumb_key = f"thumb_{uid}"

            col_nome, col_toggle = st.columns([5, 1])
            with col_nome:
                numero  = global_idx + 1
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

            uploaded = st.file_uploader(
                "Imagem",
                type=["jpg", "jpeg", "png"],
                key=f"img_{uid}",
                label_visibility="collapsed"
            )

            if uploaded is not None:
                if uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
                    st.warning(f"Imagem muito grande. Use arquivos menores que {MAX_UPLOAD_MB}MB.")
                else:
                    raw        = uploaded.read()
                    processado = processar_imagem_upload(raw)
                    thumb      = gerar_thumbnail(processado)
                    st.session_state[bytes_key] = processado
                    st.session_state[thumb_key] = thumb
                    item["bytes"] = processado
                    item["nome"]  = uploaded.name

            if uploaded is None and bytes_key not in st.session_state:
                item["bytes"] = None
                item["nome"]  = None
            elif bytes_key in st.session_state:
                item["bytes"] = st.session_state[bytes_key]

            if uid in st.session_state.preview_aberto:
                if item["bytes"]:
                    thumb = st.session_state.get(thumb_key, item["bytes"])
                    st.image(io.BytesIO(thumb), use_container_width=True)
                else:
                    st.caption("⬆ Nenhuma imagem selecionada ainda")

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
                    st.session_state.pop(bytes_key, None)
                    st.session_state.pop(thumb_key, None)
                    st.rerun()

            st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ── Gerar PDF ──────────────────────────────────────────────
st.divider()

validos = [i for i in st.session_state.itens if i.get("bytes")]
sem_img = [i for i in st.session_state.itens if not i.get("bytes")]
total   = len(st.session_state.itens)

# Atualiza número de cada item antes de gerar o PDF
for idx, item in enumerate(st.session_state.itens):
    item["numero"] = idx + 1

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.caption(f"{total} tópico(s) adicionado(s) · {len(validos)} com imagem")
    if sem_img:
        nomes  = ", ".join(i["topico"] for i in sem_img[:3])
        sufixo = f" e mais {len(sem_img) - 3}..." if len(sem_img) > 3 else ""
        st.warning(f"⚠️ {len(sem_img)} tópico(s) sem imagem não entrarão no PDF: {nomes}{sufixo}")

with col_btn:
    if st.button("📄 Gerar PDF", type="primary", use_container_width=True, disabled=len(validos) == 0):
        try:
            barra  = st.progress(0, text="Iniciando geração…")
            status = st.empty()

            barra.progress(0.2, text="Processando imagens…")
            pdf_buf = gerar_pdf(validos, header_bytes)
            barra.progress(1.0, text="Concluído!")
            status.success("PDF gerado com sucesso!")

            st.download_button(
                label="⬇ Baixar PDF",
                data=pdf_buf,
                file_name="relatorio_fotografico.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Erro ao gerar o PDF: {e}")
