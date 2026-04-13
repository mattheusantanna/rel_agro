# app.py
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
@@ -9,6 +10,7 @@

# ===== HEADER DEFAULT =====
DEFAULT_HEADER_PATH = "header.png"
MAX_UPLOAD_MB       = 10

def carregar_header_padrao():
    if os.path.exists(DEFAULT_HEADER_PATH):
@@ -72,6 +74,20 @@ def carregar_header_padrao():
    ],
}

# ===== UTILS =====
def gerar_thumbnail(img_bytes, max_px=400):
    try:
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((max_px, max_px))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        buf.seek(0)
        return buf.read()
    except Exception:
        return img_bytes

# ===== PDF =====
def desenhar_cabecalho(c, header_bytes):
    if header_bytes is None:
@@ -93,40 +109,33 @@ def desenhar_imagem(c, img_bytes, y_base, box_h, topico):
        img = img.convert("RGB")
    iw, ih = img.size

    MARGIN_X   = 40        # margem lateral da caixa
    LABEL_H    = 18        # altura da faixa do tópico na parte inferior
    PADDING    = 6         # espaço interno entre borda e imagem
    MARGIN_X  = 40
    LABEL_H   = 18
    PADDING   = 6

    box_x = MARGIN_X
    box_w = PAGE_WIDTH - 2 * MARGIN_X
    box_y = y_base

    # Área disponível para a foto dentro da caixa
    img_area_w = box_w - 2 * PADDING
    img_area_h = box_h - LABEL_H - 2 * PADDING

    ratio  = min(img_area_w / iw, img_area_h / ih)
    nw, nh = iw * ratio, ih * ratio

    # Centraliza a foto dentro da área
    img_x = box_x + PADDING + (img_area_w - nw) / 2
    img_y = box_y + LABEL_H + PADDING + (img_area_h - nh) / 2

    # Desenha a imagem
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    c.drawImage(ImageReader(buf), img_x, img_y, width=nw, height=nh)

    # Borda externa da caixa inteira
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8)
    c.rect(box_x, box_y, box_w, box_h)

    # Linha separadora acima do tópico
    c.line(box_x, box_y + LABEL_H, box_x + box_w, box_y + LABEL_H)

    # Texto do tópico na faixa inferior
    c.setFont("Helvetica-Bold", 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(box_x + PADDING, box_y + 5, topico)
@@ -148,8 +157,8 @@ def gerar_pdf(itens, header_bytes):
            for j, y_pos in enumerate([IMG_Y_TOP, IMG_Y_BOT]):
                if i + j >= len(lista):
                    break
                item = lista[i + j]
                numero = itens.index(item) + 1
                item           = lista[i + j]
                numero         = itens.index(item) + 1
                topico_numerado = f"{numero}. {item['topico']}"
                desenhar_imagem(c, item["bytes"], y_pos, BOX_H, topico_numerado)
            c.showPage()
@@ -204,6 +213,18 @@ def gerar_pdf(itens, header_bytes):
if "preview_aberto" not in st.session_state:
    st.session_state.preview_aberto = set()

# ── Botão limpar tudo ──────────────────────────────────────────────
if st.session_state.itens:
    if st.button("🗑️ Limpar tudo", type="secondary"):
        # Remove também todas as chaves auxiliares de bytes/thumb
        for item in st.session_state.itens:
            uid = item["id"]
            st.session_state.pop(f"bytes_{uid}", None)
            st.session_state.pop(f"thumb_{uid}", None)
        st.session_state.itens          = []
        st.session_state.preview_aberto = set()
        st.rerun()

# ── Seções ──────────────────────────────────────────────
colunas = st.columns(3)

@@ -238,16 +259,16 @@ def gerar_pdf(itens, header_bytes):
            if item["sessao"] != nome_secao:
                continue

            uid = item["id"]
            uid       = item["id"]
            bytes_key = f"bytes_{uid}"
            thumb_key = f"thumb_{uid}"

            # Linha com nome do tópico e botão de toggle
            col_nome, col_toggle = st.columns([5, 1])
            with col_nome:
                numero = st.session_state.itens.index(item) + 1

                numero  = st.session_state.itens.index(item) + 1
                tem_img = "✓" if item["bytes"] else "○"
                st.markdown(f"{tem_img} **{numero}. {item['topico']}**")
                
            with col_toggle:
                aberto = uid in st.session_state.preview_aberto
                label  = "▲" if aberto else "▼"
@@ -258,21 +279,36 @@ def gerar_pdf(itens, header_bytes):
                        st.session_state.preview_aberto.add(uid)
                    st.rerun()

            # Upload sempre visível
            # Upload com validação de tamanho
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
            if uploaded is not None:
                if uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
                    st.warning(f"Imagem muito grande. Use arquivos menores que {MAX_UPLOAD_MB}MB.")
                else:
                    raw = uploaded.read()
                    st.session_state[bytes_key] = raw
                    st.session_state[thumb_key] = gerar_thumbnail(raw)
                    item["bytes"] = raw
                    item["nome"]  = uploaded.name

            # Se o widget foi limpo → usuário removeu
            if uploaded is None and bytes_key not in st.session_state:
                item["bytes"] = None
                item["nome"]  = None
            elif bytes_key in st.session_state:
                item["bytes"] = st.session_state[bytes_key]

            # Preview apenas se aberto E tem imagem
            if uid in st.session_state.preview_aberto:
                if item["bytes"]:
                    st.image(io.BytesIO(item["bytes"]), use_container_width=True)
                    thumb = st.session_state.get(thumb_key, item["bytes"])
                    st.image(io.BytesIO(thumb), use_container_width=True)
                else:
                    st.caption("⬆ Nenhuma imagem selecionada ainda")

@@ -292,29 +328,39 @@ def gerar_pdf(itens, header_bytes):
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
total   = len(st.session_state.itens)
validos   = [i for i in st.session_state.itens if i.get("bytes")]
sem_img   = [i for i in st.session_state.itens if not i.get("bytes")]
total     = len(st.session_state.itens)

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.caption(f"{total} tópico(s) adicionado(s) · {len(validos)} com imagem")
    if sem_img:
        nomes = ", ".join(i["topico"] for i in sem_img[:3])
        sufixo = f" e mais {len(sem_img) - 3}..." if len(sem_img) > 3 else ""
        st.warning(f"⚠️ {len(sem_img)} tópico(s) sem imagem e não entrarão no PDF: {nomes}{sufixo}")

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
        try:
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
        except Exception as e:
            st.error(f"Erro ao gerar o PDF: {e}")
