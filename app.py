import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageTk
import os
import sys

# ===== TEMA =====
THEME = {
    "bg":         "#F4F5F7",
    "sidebar":    "#FFFFFF",
    "card":       "#FFFFFF",
    "primary":    "#2E86DE",
    "primary_dk": "#1A6BBE",
    "success":    "#27AE60",
    "danger":     "#E74C3C",
    "warning":    "#F39C12",
    "text":       "#1C2B3A",
    "text_muted": "#6B7A8D",
    "border":     "#E0E4EA",
    "accent":     "#EBF4FF",
}

# ===== UTILS =====
def resource_path(relative_path):
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)

# ===== CONFIG PDF =====
PAGE_WIDTH, PAGE_HEIGHT = A4
HEADER_PATH  = resource_path("header.png")
HEADER_H     = 120
MARGIN_BOT   = 40
GAP          = 30
TITLE_SPACE  = 25

usable_h = PAGE_HEIGHT - HEADER_H - MARGIN_BOT
BOX_H    = (usable_h - GAP) / 2
IMG_Y_TOP    = MARGIN_BOT + BOX_H + GAP
IMG_Y_BOT    = MARGIN_BOT
TITLE_Y      = PAGE_HEIGHT - 110

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

itens = []

# ===== PDF =====
def desenhar_cabecalho(c):
    if not os.path.exists(HEADER_PATH):
        return
    img = Image.open(HEADER_PATH)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    w, h  = img.size
    scale = PAGE_WIDTH / w
    c.drawImage(ImageReader(img), 0, PAGE_HEIGHT - h * scale,
                width=PAGE_WIDTH, height=h * scale)

def desenhar_imagem(c, path, y_base, box_h, topico):
    img = Image.open(path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    iw, ih   = img.size
    max_w    = PAGE_WIDTH - 80
    max_h    = box_h - TITLE_SPACE - 10
    ratio    = min(max_w / iw, max_h / ih)
    nw, nh   = iw * ratio, ih * ratio
    x        = (PAGE_WIDTH - nw) / 2
    y        = y_base + TITLE_SPACE + (max_h - nh) / 2
    c.drawImage(ImageReader(img), x, y, width=nw, height=nh)
    c.setFont("Helvetica", 10)
    c.drawCentredString(PAGE_WIDTH / 2, y_base + 5, topico)

def gerar_pdf():
    validos = [i for i in itens if i["path"]]
    if not validos:
        messagebox.showwarning("Aviso", "Adicione pelo menos uma imagem antes de gerar o PDF.")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF", "*.pdf")],
        title="Salvar relatório como…"
    )
    if not path:
        return

    btn_gerar.config(state="disabled", text="Gerando…")
    root.update_idletasks()

    try:
        c = pdf_canvas.Canvas(path, pagesize=A4)
        sessoes = {}
        for item in validos:
            sessoes.setdefault(item["sessao"], []).append(item)

        for sessao, lista in sessoes.items():
            for i in range(0, len(lista), 2):
                desenhar_cabecalho(c)
                if i == 0:
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(40, TITLE_Y, sessao)
                for j, y_pos in enumerate([IMG_Y_TOP, IMG_Y_BOT]):
                    if i + j >= len(lista):
                        break
                    item = lista[i + j]
                    desenhar_imagem(c, item["path"], y_pos, BOX_H, item["topico"])
                c.showPage()
        c.save()
        messagebox.showinfo("Sucesso", f"PDF salvo em:\n{path}")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao gerar PDF:\n{e}")
    finally:
        btn_gerar.config(state="normal", text="  Gerar PDF  ")
        atualizar_status()

# ===== UI HELPERS =====
def fazer_botao(parent, texto, comando, cor=None, fg="#FFFFFF", small=False):
    cor  = cor or THEME["primary"]
    font = ("Segoe UI", 9) if small else ("Segoe UI", 10)
    btn  = tk.Button(
        parent, text=texto, command=comando,
        bg=cor, fg=fg, activebackground=THEME["primary_dk"],
        activeforeground="#FFFFFF", relief="flat",
        font=font, cursor="hand2",
        padx=10 if small else 14, pady=4 if small else 6,
        bd=0
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=_escurecer(cor)))
    btn.bind("<Leave>", lambda e: btn.config(bg=cor))
    return btn

def _escurecer(hex_cor):
    r = max(0, int(hex_cor[1:3], 16) - 20)
    g = max(0, int(hex_cor[3:5], 16) - 20)
    b = max(0, int(hex_cor[5:7], 16) - 20)
    return f"#{r:02X}{g:02X}{b:02X}"

def atualizar_status():
    total   = len(itens)
    com_img = sum(1 for i in itens if i["path"])
    status_var.set(f"  {total} tópico(s) adicionado(s)  ·  {com_img} imagem(ns) selecionada(s)")
    badge_vars[0].set(str(sum(1 for i in itens if i["sessao"] == list(ESTRUTURA)[0] and i["path"])))
    badge_vars[1].set(str(sum(1 for i in itens if i["sessao"] == list(ESTRUTURA)[1] and i["path"])))
    badge_vars[2].set(str(sum(1 for i in itens if i["sessao"] == list(ESTRUTURA)[2] and i["path"])))

# ===== SEÇÃO =====
def criar_secao(parent, nome_secao, badge_var):
    card = tk.Frame(parent, bg=THEME["card"],
                    highlightbackground=THEME["border"],
                    highlightthickness=1)
    card.pack(fill="both", expand=True, padx=6, pady=6)

    # Cabeçalho do card
    header = tk.Frame(card, bg=THEME["card"])
    header.pack(fill="x", padx=14, pady=(12, 0))

    tk.Label(header, text=nome_secao, bg=THEME["card"],
             fg=THEME["text"], font=("Segoe UI", 11, "bold")).pack(side="left")

    badge = tk.Label(header, textvariable=badge_var,
                     bg=THEME["accent"], fg=THEME["primary"],
                     font=("Segoe UI", 9, "bold"),
                     padx=8, pady=2, relief="flat")
    badge.pack(side="right")

    sep = tk.Frame(card, bg=THEME["border"], height=1)
    sep.pack(fill="x", padx=14, pady=8)

    # Dropdown de tópico
    ctrl = tk.Frame(card, bg=THEME["card"])
    ctrl.pack(fill="x", padx=14, pady=(0, 8))

    tk.Label(ctrl, text="Tópico:", bg=THEME["card"],
             fg=THEME["text_muted"], font=("Segoe UI", 9)).pack(side="left")

    topico_var = tk.StringVar(value=ESTRUTURA[nome_secao][0])
    menu = ttk.Combobox(ctrl, textvariable=topico_var,
                        values=ESTRUTURA[nome_secao],
                        state="readonly", width=30, font=("Segoe UI", 9))
    menu.pack(side="left", padx=(6, 0))

    # Lista com scroll
    scroll_wrap = tk.Frame(card, bg=THEME["card"])
    scroll_wrap.pack(fill="both", expand=True, padx=8)

    canvas_s = tk.Canvas(scroll_wrap, bg=THEME["card"],
                         highlightthickness=0, bd=0)
    scrollbar = tk.Scrollbar(scroll_wrap, orient="vertical",
                             command=canvas_s.yview)

    inner = tk.Frame(canvas_s, bg=THEME["card"])
    inner.bind("<Configure>",
               lambda e: canvas_s.configure(scrollregion=canvas_s.bbox("all")))
    canvas_s.create_window((0, 0), window=inner, anchor="nw")
    canvas_s.configure(yscrollcommand=scrollbar.set)

    canvas_s.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_mouse_wheel(event):
        canvas_s.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas_s.bind("<MouseWheel>", _on_mouse_wheel)

    def adicionar():
        topico = topico_var.get()
        item   = {"sessao": nome_secao, "topico": topico, "path": None, "frame": None}

        row = tk.Frame(inner, bg=THEME["card"],
                       highlightbackground=THEME["border"],
                       highlightthickness=1)
        row.pack(fill="x", padx=4, pady=3)
        item["frame"] = row

        # Linha de info
        info = tk.Frame(row, bg=THEME["card"])
        info.pack(fill="x", padx=10, pady=(6, 2))

        tk.Label(info, text=topico, bg=THEME["card"],
                 fg=THEME["text"], font=("Segoe UI", 9, "bold")).pack(side="left")

        lbl_img = tk.Label(info, text="Nenhuma imagem selecionada",
                           bg=THEME["card"], fg=THEME["text_muted"],
                           font=("Segoe UI", 8))
        lbl_img.pack(side="left", padx=(8, 0))

        # Botões de ação
        acoes = tk.Frame(row, bg=THEME["card"])
        acoes.pack(fill="x", padx=10, pady=(0, 6))

        def escolher():
            path = filedialog.askopenfilename(
                title="Selecionar imagem",
                filetypes=[("Imagens", "*.jpg *.jpeg *.png")]
            )
            if path:
                item["path"] = path
                nome = os.path.basename(path)
                lbl_img.config(text=f"✓ {nome}", fg=THEME["success"])
                atualizar_status()

        def remover():
            row.destroy()
            itens.remove(item)
            atualizar_status()

        def subir():
            idx = itens.index(item)
            if idx > 0:
                itens[idx], itens[idx - 1] = itens[idx - 1], itens[idx]
                _refresh(inner)

        def descer():
            idx = itens.index(item)
            if idx < len(itens) - 1:
                itens[idx], itens[idx + 1] = itens[idx + 1], itens[idx]
                _refresh(inner)

        itens.append(item)

        fazer_botao(acoes, "Selecionar", escolher, small=True).pack(side="left", padx=(0, 4))
        fazer_botao(acoes, "↑", subir, cor="#F0F2F5", fg=THEME["text"], small=True).pack(side="left", padx=2)
        fazer_botao(acoes, "↓", descer, cor="#F0F2F5", fg=THEME["text"], small=True).pack(side="left", padx=2)
        fazer_botao(acoes, "Remover", remover, cor=THEME["danger"], small=True).pack(side="left", padx=(8, 0))

        atualizar_status()

    # Botão adicionar
    sep2 = tk.Frame(card, bg=THEME["border"], height=1)
    sep2.pack(fill="x", padx=14, pady=(4, 0))

    fazer_botao(card, "+ Adicionar Tópico", adicionar,
                cor=THEME["primary"]).pack(pady=10)

def _refresh(container):
    for w in container.winfo_children():
        w.pack_forget()
    for item in itens:
        item["frame"].pack(fill="x", padx=4, pady=3)

# ===== APP =====
root = tk.Tk()
root.title("Relatório Fotográfico")
root.geometry("1140x680")
root.minsize(900, 560)
root.configure(bg=THEME["bg"])

# TTK style
style = ttk.Style()
style.theme_use("clam")
style.configure("TCombobox",
                fieldbackground=THEME["bg"],
                background=THEME["bg"],
                foreground=THEME["text"],
                arrowcolor=THEME["text_muted"],
                relief="flat")

# ── Topbar ──────────────────────────────────────────────
topbar = tk.Frame(root, bg="#FFFFFF",
                  highlightbackground=THEME["border"],
                  highlightthickness=1)
topbar.pack(fill="x")

tk.Label(topbar, text="Relatório Fotográfico",
         bg="#FFFFFF", fg=THEME["text"],
         font=("Segoe UI", 14, "bold")).pack(side="left", padx=20, pady=12)

tk.Label(topbar, text="Auditoria de Campo",
         bg="#FFFFFF", fg=THEME["text_muted"],
         font=("Segoe UI", 10)).pack(side="left", padx=(0, 0), pady=12)

btn_gerar = fazer_botao(topbar, "  Gerar PDF  ", gerar_pdf, cor=THEME["success"])
btn_gerar.pack(side="right", padx=20, pady=10)

# ── Colunas ──────────────────────────────────────────────
badge_vars = [tk.StringVar(value="0") for _ in range(3)]

cols_frame = tk.Frame(root, bg=THEME["bg"])
cols_frame.pack(fill="both", expand=True, padx=10, pady=10)

nomes = list(ESTRUTURA.keys())
for i in range(3):
    col = tk.Frame(cols_frame, bg=THEME["bg"])
    col.pack(side="left", fill="both", expand=True)
    criar_secao(col, nomes[i], badge_vars[i])

# ── Statusbar ──────────────────────────────────────────────
status_var = tk.StringVar(value="  Nenhum tópico adicionado")

statusbar = tk.Frame(root, bg="#FFFFFF",
                     highlightbackground=THEME["border"],
                     highlightthickness=1, height=30)
statusbar.pack(fill="x", side="bottom")
statusbar.pack_propagate(False)

tk.Label(statusbar, textvariable=status_var,
         bg="#FFFFFF", fg=THEME["text_muted"],
         font=("Segoe UI", 9)).pack(side="left", pady=5)

root.mainloop()