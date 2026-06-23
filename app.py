import sys
import os
import csv
import json
import uuid
import time
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QLineEdit, QTextEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QFormLayout, QFileDialog,
    QMessageBox, QSplitter, QScrollArea, QFrame, QGridLayout,
    QSpinBox, QCheckBox, QTabWidget, QListWidget, QListWidgetItem,
    QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPainter, QPixmap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from datetime import date as dt_date
import datetime as dt_module

import database as db

# ─── PALETTE ──────────────────────────────────────────────────────────────────
INK       = "#1a1a2e"
PAPER     = "#f5f0e8"
RED_SEAL  = "#c0392b"
JADE      = "#2d6a4f"
GOLD      = "#d4a017"
MUTED     = "#8a7f72"
CARD_BG   = "#faf7f2"
BORDER    = "#d4c9b8"
SIDEBAR   = "#16213e"
SB_ACTIVE = "#c0392b"
SB_TEXT   = "#e8e0d4"
WHITE     = "#ffffff"
LIGHT_RED = "#fdecea"
LIGHT_GRN = "#e8f5e9"


STYLE = f"""
QMainWindow, QDialog {{
    background: {PAPER};
}}
QWidget {{
    background: {PAPER};
    color: {INK};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}}
QLabel {{
    background: transparent;
}}
QPushButton {{
    background: {INK};
    color: {PAPER};
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background: {RED_SEAL};
}}
QPushButton:pressed {{
    background: #922b21;
}}
QPushButton.secondary {{
    background: transparent;
    color: {INK};
    border: 1.5px solid {BORDER};
}}
QPushButton.secondary:hover {{
    border-color: {INK};
    background: {CARD_BG};
}}
QPushButton.danger {{
    background: {RED_SEAL};
}}
QPushButton.success {{
    background: {JADE};
}}
QLineEdit, QTextEdit, QComboBox, QSpinBox {{
    background: {WHITE};
    border: 1.5px solid {BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    color: {INK};
    selection-background-color: {RED_SEAL};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {RED_SEAL};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}
QTableWidget {{
    background: {WHITE};
    alternate-background-color: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
}}
QTableWidget::item {{
    padding: 6px 8px;
}}
QTableWidget::item:selected {{
    background: {RED_SEAL};
    color: {WHITE};
}}
QHeaderView::section {{
    background: {INK};
    color: {PAPER};
    padding: 8px;
    border: none;
    font-weight: 600;
}}
QScrollBar:vertical {{
    background: {CARD_BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {MUTED};
    border-radius: 4px;
    min-height: 30px;
}}
QTabWidget::pane {{
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    background: {WHITE};
}}
QTabBar::tab {{
    background: {CARD_BG};
    color: {MUTED};
    padding: 8px 20px;
    border: 1.5px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {WHITE};
    color: {INK};
    font-weight: 600;
    border-color: {RED_SEAL};
}}
QFrame#card {{
    background: {WHITE};
    border: 1.5px solid {BORDER};
    border-radius: 10px;
}}
QFrame#sidebar {{
    background: {SIDEBAR};
}}
"""


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def make_btn(text, cls="", parent=None):
    btn = QPushButton(text, parent)
    if cls:
        btn.setProperty("class", cls)
        btn.setStyleSheet(btn.styleSheet())  # force refresh
    return btn


def card_frame():
    f = QFrame()
    f.setObjectName("card")
    return f


def section_label(text):
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    lbl.setStyleSheet(f"color: {MUTED}; letter-spacing: 1px; background: transparent;")
    return lbl


def h_sep():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {BORDER};")
    return line


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

class SidebarBtn(QPushButton):
    def __init__(self, text, icon_char="", parent=None):
        super().__init__(parent)
        self.setText(f"  {icon_char}  {text}")
        self.setCheckable(True)
        self.setFixedHeight(46)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {SB_TEXT};
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 12px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.08); }}
            QPushButton:checked {{
                background: {SB_ACTIVE};
                color: white;
                font-weight: 700;
            }}
        """)


class Sidebar(QWidget):
    page_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(210)
        self.setStyleSheet(f"background: {SIDEBAR};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 20, 12, 20)
        lay.setSpacing(4)

        logo = QLabel("漢語")
        logo.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {RED_SEAL}; background: transparent; letter-spacing: 4px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("Mandarin Study")
        sub.setStyleSheet(f"color: {MUTED}; background: transparent; font-size: 10px; letter-spacing: 2px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo)
        lay.addWidget(sub)
        lay.addSpacing(20)
        lay.addWidget(self._sep())

        pages = [
            ("Dashboard", "⬛"),
            ("Vocabulário", "字"),
            ("Anotações", "📝"),
            ("Estudar (SRS)", "🃏"),
            ("Estatísticas", "📊"),
        ]
        self.btns = []
        for i, (name, icon) in enumerate(pages):
            btn = SidebarBtn(name, icon)
            btn.clicked.connect(lambda _, idx=i: self._select(idx))
            lay.addWidget(btn)
            self.btns.append(btn)

        lay.addStretch()
        lay.addWidget(self._sep())
        ver = QLabel("v1.0  •  SQLite")
        ver.setStyleSheet(f"color: {MUTED}; font-size: 10px; background: transparent;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(ver)

        self._select(0)

    def _sep(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: rgba(255,255,255,0.08);")
        return line

    def _select(self, idx):
        for i, btn in enumerate(self.btns):
            btn.setChecked(i == idx)
        self.page_changed.emit(idx)


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, label, value, color=None):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(100)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        self.val_lbl.setStyleSheet(f"color: {color or RED_SEAL}; background: transparent;")
        txt = QLabel(label)
        txt.setStyleSheet(f"color: {MUTED}; font-size: 11px; background: transparent;")
        lay.addWidget(self.val_lbl)
        lay.addWidget(txt)

    def set_value(self, v):
        self.val_lbl.setText(str(v))


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)

        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {INK};")
        lay.addWidget(title)

        # stat cards
        grid = QHBoxLayout()
        self.sc_total   = StatCard("Total de palavras", 0, INK)
        self.sc_mastered= StatCard("Dominadas", 0, JADE)
        self.sc_due     = StatCard("Para revisar hoje", 0, RED_SEAL)
        self.sc_today   = StatCard("Estudadas hoje", 0, GOLD)
        for sc in [self.sc_total, self.sc_mastered, self.sc_due, self.sc_today]:
            grid.addWidget(sc)
        lay.addLayout(grid)

        # chart
        chart_card = card_frame()
        chart_lay = QVBoxLayout(chart_card)
        chart_lay.setContentsMargins(16, 16, 16, 16)
        chart_lay.addWidget(section_label("PALAVRAS ESTUDADAS — ÚLTIMOS 30 DIAS"))
        self.figure, self.ax = plt.subplots(figsize=(8, 2.8))
        self.figure.patch.set_facecolor("#faf7f2")
        self.canvas = FigureCanvas(self.figure)
        chart_lay.addWidget(self.canvas)
        lay.addWidget(chart_card)
        lay.addStretch()

    def refresh(self):
        stats = db.get_overall_stats()
        self.sc_total.set_value(stats["total_words"])
        self.sc_mastered.set_value(stats["mastered"])
        self.sc_due.set_value(stats["due_today"])
        self.sc_today.set_value(stats["studied_today"])
        self._draw_chart()

    def _draw_chart(self):
        data = db.get_daily_stats(30)
        self.ax.clear()
        if data:
            days   = [d["day"] for d in data]
            totals = [d["total"] for d in data]
            corrects = [d["correct"] or 0 for d in data]
            self.ax.bar(days, totals, color=f"{INK}33", label="Total")
            self.ax.bar(days, corrects, color=RED_SEAL, alpha=0.8, label="Corretas")
            self.ax.set_facecolor("#faf7f2")
            self.ax.tick_params(labelsize=8, colors=MUTED)
            self.ax.spines[:].set_visible(False)
            self.ax.legend(fontsize=8)
            plt.xticks(rotation=45, ha="right")
        else:
            self.ax.text(0.5, 0.5, "Sem dados ainda — comece a estudar!",
                         ha="center", va="center", color=MUTED,
                         transform=self.ax.transAxes, fontsize=11)
            self.ax.set_facecolor("#faf7f2")
            self.ax.axis("off")
        self.figure.tight_layout()
        self.canvas.draw()


# ─── WORD DIALOG ──────────────────────────────────────────────────────────────

class WordDialog(QDialog):
    def __init__(self, parent=None, word=None):
        super().__init__(parent)
        self.word = word
        self.setWindowTitle("Editar palavra" if word else "Nova palavra")
        self.setMinimumWidth(480)
        self.setStyleSheet(STYLE)

        form = QFormLayout(self)
        form.setSpacing(12)
        form.setContentsMargins(24, 24, 24, 24)

        def field(placeholder=""):
            e = QLineEdit()
            e.setPlaceholderText(placeholder)
            return e

        self.f_char   = field("e.g. 你好")
        self.f_pinyin = field("e.g. nǐ hǎo")
        self.f_trans  = field("e.g. Olá")
        self.f_gram   = QComboBox()
        self.f_gram.setEditable(True)
        self.f_gram.addItems(["", "n.", "v.", "adj.", "adv.", "p.l.", "p.c.",
                               "pron.", "conj.", "part.", "expr."])
        self.f_exam   = QTextEdit()
        self.f_exam.setPlaceholderText("Exemplo de uso…")
        self.f_exam.setFixedHeight(70)
        self.f_chap   = field("e.g. 14")
        self.f_notes  = QTextEdit()
        self.f_notes.setPlaceholderText("Observações…")
        self.f_notes.setFixedHeight(70)
        self.f_diff   = QComboBox()
        self.f_diff.addItems(["1 – Fácil", "2 – Médio", "3 – Difícil"])
        self.f_mast   = QComboBox()
        self.f_mast.addItems(["Normal", "Dominada ✓", "Precisa revisar ⚠"])

        form.addRow("Caractere *", self.f_char)
        form.addRow("Pinyin *",    self.f_pinyin)
        form.addRow("Tradução *",  self.f_trans)
        form.addRow("Tipo gram.",  self.f_gram)
        form.addRow("Exemplo",     self.f_exam)
        form.addRow("Capítulo",    self.f_chap)
        form.addRow("Observações", self.f_notes)
        form.addRow("Dificuldade", self.f_diff)
        form.addRow("Status",      self.f_mast)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        form.addRow(btns)

        if word:
            self.f_char.setText(word["character"])
            self.f_pinyin.setText(word["pinyin"])
            self.f_trans.setText(word["translation"])
            self.f_gram.setCurrentText(word.get("gram_type", ""))
            self.f_exam.setPlainText(word.get("example", ""))
            self.f_chap.setText(word.get("chapter", ""))
            self.f_notes.setPlainText(word.get("notes", ""))
            self.f_diff.setCurrentIndex(int(word.get("difficulty", 1)) - 1)
            self.f_mast.setCurrentIndex(int(word.get("mastered", 0)))

    def _save(self):
        if not self.f_char.text().strip() or not self.f_pinyin.text().strip() \
                or not self.f_trans.text().strip():
            QMessageBox.warning(self, "Campos obrigatórios",
                                "Preencha Caractere, Pinyin e Tradução.")
            return
        self.accept()

    def get_data(self):
        return dict(
            character   = self.f_char.text().strip(),
            pinyin      = self.f_pinyin.text().strip(),
            translation = self.f_trans.text().strip(),
            gram_type   = self.f_gram.currentText().strip(),
            example     = self.f_exam.toPlainText().strip(),
            chapter     = self.f_chap.text().strip(),
            notes       = self.f_notes.toPlainText().strip(),
            difficulty  = self.f_diff.currentIndex() + 1,
            mastered    = self.f_mast.currentIndex(),
        )


# ─── VOCABULARY PAGE ──────────────────────────────────────────────────────────

class VocabPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        # header
        hdr = QHBoxLayout()
        title = QLabel("Vocabulário")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()
        btn_import = QPushButton("⬆  Importar CSV")
        btn_import.setStyleSheet(f"background:{JADE};")
        btn_add    = QPushButton("＋  Nova palavra")
        btn_import.clicked.connect(self._import_csv)
        btn_add.clicked.connect(self._add_word)
        hdr.addWidget(btn_import)
        hdr.addWidget(btn_add)
        lay.addLayout(hdr)

        # filters
        filt = QHBoxLayout()
        self.s_search = QLineEdit(); self.s_search.setPlaceholderText("🔍  Buscar…")
        self.s_chap   = QComboBox(); self.s_chap.addItem("Todos os capítulos")
        self.s_gram   = QComboBox(); self.s_gram.addItem("Todos os tipos")
        self.s_diff   = QComboBox(); self.s_diff.addItems(["Dificuldade", "1 – Fácil", "2 – Médio", "3 – Difícil"])
        self.s_mast   = QComboBox(); self.s_mast.addItems(["Todos os status", "Normal", "Dominada", "Revisar"])
        for w in [self.s_search, self.s_chap, self.s_gram, self.s_diff, self.s_mast]:
            filt.addWidget(w)
            if hasattr(w, "textChanged"):
                w.textChanged.connect(self._refresh)
            else:
                w.currentIndexChanged.connect(self._refresh)
        lay.addLayout(filt)

        # table
        cols = ["#", "Caractere", "Pinyin", "Tradução", "Tipo", "Capítulo", "Dificuldade", "Status", ""]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._edit_selected)
        lay.addWidget(self.table)

        self._word_ids = []

    def showEvent(self, e):
        super().showEvent(e)
        self._refresh_filters()
        self._refresh()

    def _refresh_filters(self):
        cur_chap = self.s_chap.currentText()
        cur_gram = self.s_gram.currentText()
        self.s_chap.blockSignals(True); self.s_gram.blockSignals(True)
        self.s_chap.clear(); self.s_chap.addItem("Todos os capítulos")
        self.s_gram.clear(); self.s_gram.addItem("Todos os tipos")
        for c in db.get_chapters(): self.s_chap.addItem(c)
        for g in db.get_gram_types(): self.s_gram.addItem(g)
        idx = self.s_chap.findText(cur_chap)
        if idx >= 0: self.s_chap.setCurrentIndex(idx)
        idx = self.s_gram.findText(cur_gram)
        if idx >= 0: self.s_gram.setCurrentIndex(idx)
        self.s_chap.blockSignals(False); self.s_gram.blockSignals(False)

    def _refresh(self):
        chap  = self.s_chap.currentText() if self.s_chap.currentIndex() > 0 else None
        gram  = self.s_gram.currentText() if self.s_gram.currentIndex() > 0 else None
        diff_i= self.s_diff.currentIndex()
        diff  = diff_i if diff_i > 0 else None
        mast_i= self.s_mast.currentIndex()
        mast  = (mast_i - 1) if mast_i > 0 else None
        search= self.s_search.text().strip() or None

        words = db.get_words(chapter=chap, gram_type=gram, difficulty=diff,
                             mastered=mast, search=search)
        self._word_ids = [w["id"] for w in words]
        self.table.setRowCount(0)
        status_map = {0: "Normal", 1: "✓ Dominada", 2: "⚠ Revisar"}
        diff_map   = {1: "Fácil", 2: "Médio", 3: "Difícil"}

        for row_i, w in enumerate(words):
            self.table.insertRow(row_i)
            cells = [
                str(row_i + 1),
                w["character"], w["pinyin"], w["translation"],
                w.get("gram_type", ""), w.get("chapter", ""),
                diff_map.get(w.get("difficulty", 1), ""),
                status_map.get(w.get("mastered", 0), ""),
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if col == 1:
                    item.setFont(QFont("Segoe UI", 15))
                if w.get("mastered") == 1:
                    item.setForeground(QColor(JADE))
                elif w.get("mastered") == 2:
                    item.setForeground(QColor(RED_SEAL))
                self.table.setItem(row_i, col, item)

            # action btn
            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setStyleSheet(f"background:{GOLD}; color:white; border-radius:4px; font-size:13px;")
            edit_btn.clicked.connect(lambda _, wid=w["id"]: self._edit_word(wid))
            self.table.setCellWidget(row_i, 8, edit_btn)

    def _add_word(self):
        dlg = WordDialog(self)
        if dlg.exec():
            d = dlg.get_data()
            db.add_word(**d)
            self._refresh_filters()
            self._refresh()

    def _edit_selected(self):
        rows = self.table.selectedItems()
        if not rows: return
        row = self.table.currentRow()
        if row < len(self._word_ids):
            self._edit_word(self._word_ids[row])

    def _edit_word(self, word_id):
        word = db.get_word(word_id)
        if not word: return
        dlg = WordDialog(self, word)
        if dlg.exec():
            d = dlg.get_data()
            db.update_word(word_id, d["character"], d["pinyin"], d["translation"],
                           d["gram_type"], d["example"], d["chapter"],
                           d["notes"], d["difficulty"], d["mastered"])
            self._refresh()

        # delete button in dialog
        del_btn = make_btn("🗑 Excluir", "danger")
        del_btn.clicked.connect(lambda: self._delete_word(word_id, dlg))

    def _delete_word(self, word_id, dlg):
        if QMessageBox.question(self, "Confirmar", "Excluir esta palavra?") \
                == QMessageBox.StandardButton.Yes:
            db.delete_word(word_id)
            dlg.reject()
            self._refresh()

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar CSV", "", "CSV Files (*.csv)"
        )
        if not path: return
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        if not rows:
            QMessageBox.warning(self, "Arquivo vazio", "O CSV não contém dados.")
            return
        added, skipped = db.import_words_csv(rows)
        QMessageBox.information(
            self, "Importação concluída",
            f"✓ {added} palavras adicionadas.\n✗ {skipped} ignoradas (sem caractere)."
        )
        self._refresh_filters()
        self._refresh()


# ─── NOTES PAGE ───────────────────────────────────────────────────────────────

class NoteDialog(QDialog):
    def __init__(self, parent=None, note=None):
        super().__init__(parent)
        self.note = note
        self.setWindowTitle("Editar anotação" if note else "Nova anotação")
        self.setMinimumSize(540, 460)
        self.setStyleSheet(STYLE)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        self.f_title = QLineEdit(); self.f_title.setPlaceholderText("Título…")
        self.f_cat   = QLineEdit(); self.f_cat.setPlaceholderText("Categoria")
        self.f_tags  = QLineEdit(); self.f_tags.setPlaceholderText("Tags separadas por vírgula")
        self.f_chap  = QLineEdit(); self.f_chap.setPlaceholderText("Capítulo relacionado")
        form.addRow("Título *",    self.f_title)
        form.addRow("Categoria",   self.f_cat)
        form.addRow("Tags",        self.f_tags)
        form.addRow("Capítulo",    self.f_chap)
        lay.addLayout(form)

        body_lbl = QLabel("Conteúdo")
        body_lbl.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        lay.addWidget(body_lbl)
        self.f_body = QTextEdit()
        self.f_body.setPlaceholderText("Escreva sua anotação aqui…")
        lay.addWidget(self.f_body)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        lay.addWidget(btns)

        if note:
            self.f_title.setText(note["title"])
            self.f_cat.setText(note.get("category", ""))
            tags = json.loads(note.get("tags", "[]") or "[]")
            self.f_tags.setText(", ".join(tags))
            self.f_chap.setText(note.get("chapter", ""))
            self.f_body.setPlainText(note.get("body", ""))

    def _save(self):
        if not self.f_title.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Digite um título.")
            return
        self.accept()

    def get_data(self):
        raw_tags = [t.strip() for t in self.f_tags.text().split(",") if t.strip()]
        return dict(
            title    = self.f_title.text().strip(),
            body     = self.f_body.toPlainText().strip(),
            category = self.f_cat.text().strip(),
            tags     = json.dumps(raw_tags, ensure_ascii=False),
            chapter  = self.f_chap.text().strip(),
            word_id  = None,
        )


class NotesPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        hdr = QHBoxLayout()
        title = QLabel("Anotações")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()
        btn_add = QPushButton("＋  Nova anotação")
        btn_add.clicked.connect(self._add_note)
        hdr.addWidget(btn_add)
        lay.addLayout(hdr)

        # filters
        filt = QHBoxLayout()
        self.s_search = QLineEdit(); self.s_search.setPlaceholderText("🔍  Buscar título, corpo, tags…")
        self.s_cat    = QComboBox(); self.s_cat.addItem("Todas as categorias")
        self.s_chap   = QComboBox(); self.s_chap.addItem("Todos os capítulos")
        for w in [self.s_search, self.s_cat, self.s_chap]:
            filt.addWidget(w)
            if hasattr(w, "textChanged"):
                w.textChanged.connect(self._refresh)
            else:
                w.currentIndexChanged.connect(self._refresh)
        lay.addLayout(filt)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # list
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ background:{WHITE}; border:1.5px solid {BORDER}; border-radius:8px; }}
            QListWidget::item {{ padding:12px; border-bottom:1px solid {BORDER}; }}
            QListWidget::item:selected {{ background:{RED_SEAL}; color:white; }}
        """)
        self.list_widget.currentItemChanged.connect(self._show_note)
        splitter.addWidget(self.list_widget)

        # preview
        preview = card_frame()
        prev_lay = QVBoxLayout(preview)
        prev_lay.setContentsMargins(16, 16, 16, 16)
        self.prev_title = QLabel("Selecione uma anotação")
        self.prev_title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.prev_title.setWordWrap(True)
        self.prev_meta = QLabel("")
        self.prev_meta.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        self.prev_body = QTextEdit()
        self.prev_body.setReadOnly(True)
        self.prev_body.setStyleSheet(f"border:none; background:transparent;")
        prev_btns = QHBoxLayout()
        self.btn_edit = QPushButton("✏ Editar")
        self.btn_del  = QPushButton("🗑 Excluir")
        self.btn_del.setStyleSheet(f"background:{RED_SEAL};")
        self.btn_edit.clicked.connect(self._edit_note)
        self.btn_del.clicked.connect(self._delete_note)
        prev_btns.addWidget(self.btn_edit)
        prev_btns.addWidget(self.btn_del)
        prev_btns.addStretch()
        prev_lay.addWidget(self.prev_title)
        prev_lay.addWidget(self.prev_meta)
        prev_lay.addWidget(h_sep())
        prev_lay.addWidget(self.prev_body)
        prev_lay.addLayout(prev_btns)
        splitter.addWidget(preview)
        splitter.setSizes([260, 500])

        lay.addWidget(splitter)
        self._notes = []
        self._current_note = None

    def showEvent(self, e):
        super().showEvent(e)
        self._refresh_filters()
        self._refresh()

    def _refresh_filters(self):
        self.s_cat.blockSignals(True); self.s_chap.blockSignals(True)
        cur_cat = self.s_cat.currentText(); cur_ch = self.s_chap.currentText()
        self.s_cat.clear(); self.s_cat.addItem("Todas as categorias")
        self.s_chap.clear(); self.s_chap.addItem("Todos os capítulos")
        for c in db.get_note_categories(): self.s_cat.addItem(c)
        for c in db.get_chapters(): self.s_chap.addItem(c)
        idx = self.s_cat.findText(cur_cat)
        if idx >= 0: self.s_cat.setCurrentIndex(idx)
        idx = self.s_chap.findText(cur_ch)
        if idx >= 0: self.s_chap.setCurrentIndex(idx)
        self.s_cat.blockSignals(False); self.s_chap.blockSignals(False)

    def _refresh(self):
        search = self.s_search.text().strip() or None
        cat    = self.s_cat.currentText() if self.s_cat.currentIndex() > 0 else None
        chap   = self.s_chap.currentText() if self.s_chap.currentIndex() > 0 else None
        self._notes = db.get_notes(search=search, category=cat, chapter=chap)
        self.list_widget.clear()
        for note in self._notes:
            tags = json.loads(note.get("tags", "[]") or "[]")
            tag_str = "  ".join(f"#{t}" for t in tags)
            item = QListWidgetItem(f"{note['title']}\n{note.get('category','')}"
                                   f"  {tag_str}")
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            self.list_widget.addItem(item)

    def _show_note(self, item):
        if not item: return
        note_id = item.data(Qt.ItemDataRole.UserRole)
        for n in self._notes:
            if n["id"] == note_id:
                self._current_note = n
                break
        if not self._current_note: return
        tags = json.loads(self._current_note.get("tags", "[]") or "[]")
        self.prev_title.setText(self._current_note["title"])
        meta = []
        if self._current_note.get("category"): meta.append(self._current_note["category"])
        if self._current_note.get("chapter"):  meta.append(f"Cap. {self._current_note['chapter']}")
        if tags: meta.append("  ".join(f"#{t}" for t in tags))
        self.prev_meta.setText("  •  ".join(meta))
        self.prev_body.setPlainText(self._current_note.get("body", ""))

    def _add_note(self):
        dlg = NoteDialog(self)
        if dlg.exec():
            d = dlg.get_data()
            db.add_note(**d)
            self._refresh_filters()
            self._refresh()

    def _edit_note(self):
        if not self._current_note: return
        dlg = NoteDialog(self, self._current_note)
        if dlg.exec():
            d = dlg.get_data()
            db.update_note(self._current_note["id"], d["title"], d["body"],
                           d["category"], d["tags"], d["chapter"], d["word_id"])
            self._refresh()

    def _delete_note(self):
        if not self._current_note: return
        if QMessageBox.question(self, "Confirmar", "Excluir esta anotação?") \
                == QMessageBox.StandardButton.Yes:
            db.delete_note(self._current_note["id"])
            self._current_note = None
            self.prev_title.setText("Selecione uma anotação")
            self.prev_body.clear()
            self._refresh()


# ─── STUDY (SRS + ANKI) ───────────────────────────────────────────────────────

class StudyPage(QWidget):
    def __init__(self):
        super().__init__()
        self.session_id = str(uuid.uuid4())
        self.cards = []
        self.current_idx = 0
        self.revealed = False
        self.session_correct = 0
        self.session_total = 0
        self.mode = "char2trans"
        self.start_time = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        # header + config
        hdr = QHBoxLayout()
        title = QLabel("Estudar")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        hdr.addWidget(title)
        hdr.addStretch()

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Caractere → Tradução",
            "Tradução → Caractere",
            "Pinyin → Caractere"
        ])
        self.chap_combo = QComboBox()
        self.chap_combo.addItem("Todos os capítulos")
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(5, 100); self.limit_spin.setValue(20)
        self.limit_spin.setPrefix("Limite: ")

        hdr.addWidget(QLabel("Modo:"))
        hdr.addWidget(self.mode_combo)
        hdr.addWidget(QLabel("Capítulo:"))
        hdr.addWidget(self.chap_combo)
        hdr.addWidget(self.limit_spin)

        btn_start = QPushButton("▶  Iniciar sessão")
        btn_start.clicked.connect(self._start_session)
        hdr.addWidget(btn_start)
        lay.addLayout(hdr)

        # progress bar
        self.prog_bar = QProgressBar()
        self.prog_bar.setStyleSheet(f"""
            QProgressBar {{
                background:{BORDER}; border-radius:4px; height:8px; text-align:center;
                color: transparent;
            }}
            QProgressBar::chunk {{ background:{RED_SEAL}; border-radius:4px; }}
        """)
        self.prog_bar.setFixedHeight(8)
        lay.addWidget(self.prog_bar)

        # card area
        self.stack = QStackedWidget()

        # — idle screen
        idle = QWidget()
        idle_lay = QVBoxLayout(idle)
        idle_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_icon = QLabel("🃏")
        idle_icon.setFont(QFont("Segoe UI", 48))
        idle_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_msg = QLabel("Configure o deck acima e clique em Iniciar sessão")
        idle_msg.setStyleSheet(f"color:{MUTED}; font-size:15px;")
        idle_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_lay.addWidget(idle_icon)
        idle_lay.addWidget(idle_msg)
        self.stack.addWidget(idle)   # index 0

        # — flashcard screen
        fc_widget = QWidget()
        fc_lay = QVBoxLayout(fc_widget)
        fc_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fc_lay.setSpacing(20)

        self.card_frame_widget = card_frame()
        self.card_frame_widget.setFixedSize(560, 280)
        cf_lay = QVBoxLayout(self.card_frame_widget)
        cf_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prompt_type = QLabel("")
        self.lbl_prompt_type.setStyleSheet(f"color:{MUTED}; font-size:11px; letter-spacing:2px;")
        self.lbl_prompt_type.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prompt = QLabel("")
        self.lbl_prompt.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        self.lbl_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prompt.setWordWrap(True)
        self.lbl_hint = QLabel("")
        self.lbl_hint.setStyleSheet(f"color:{MUTED}; font-size:13px;")
        self.lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_answer = QLabel("")
        self.lbl_answer.setFont(QFont("Segoe UI", 18))
        self.lbl_answer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_answer.setWordWrap(True)
        self.lbl_example = QLabel("")
        self.lbl_example.setStyleSheet(f"color:{MUTED}; font-size:12px; font-style:italic;")
        self.lbl_example.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_example.setWordWrap(True)
        cf_lay.addWidget(self.lbl_prompt_type)
        cf_lay.addWidget(self.lbl_prompt)
        cf_lay.addWidget(self.lbl_hint)
        cf_lay.addWidget(h_sep())
        cf_lay.addWidget(self.lbl_answer)
        cf_lay.addWidget(self.lbl_example)
        fc_lay.addWidget(self.card_frame_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # reveal / quality buttons
        self.btn_reveal = QPushButton("👁  Revelar resposta")
        self.btn_reveal.setFixedWidth(220)
        self.btn_reveal.clicked.connect(self._reveal)
        fc_lay.addWidget(self.btn_reveal, alignment=Qt.AlignmentFlag.AlignCenter)

        self.quality_frame = QFrame()
        q_lay = QHBoxLayout(self.quality_frame)
        q_lay.setSpacing(8)
        quality_config = [
            ("✗ Errei", 0, RED_SEAL),
            ("Difícil", 2, "#e67e22"),
            ("Bom", 3, GOLD),
            ("Fácil", 4, JADE),
            ("✓ Muito fácil", 5, "#1a7d4b"),
        ]
        for label, quality, color in quality_config:
            btn = QPushButton(label)
            btn.setStyleSheet(f"background:{color}; min-width:90px;")
            btn.clicked.connect(lambda _, q=quality: self._rate(q))
            q_lay.addWidget(btn)
        self.quality_frame.hide()
        fc_lay.addWidget(self.quality_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(fc_widget)  # index 1

        # — results screen
        results = QWidget()
        res_lay = QVBoxLayout(results)
        res_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        res_lay.setSpacing(16)
        self.res_title = QLabel("Sessão concluída! 🎉")
        self.res_title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.res_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.res_details = QLabel("")
        self.res_details.setStyleSheet(f"color:{MUTED}; font-size:14px;")
        self.res_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_restart = QPushButton("↺  Nova sessão")
        btn_restart.setFixedWidth(180)
        btn_restart.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        res_lay.addWidget(self.res_title)
        res_lay.addWidget(self.res_details)
        res_lay.addWidget(btn_restart, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(results)  # index 2

        lay.addWidget(self.stack)

    def showEvent(self, e):
        super().showEvent(e)
        cur = self.chap_combo.currentText()
        self.chap_combo.blockSignals(True)
        self.chap_combo.clear()
        self.chap_combo.addItem("Todos os capítulos")
        for c in db.get_chapters(): self.chap_combo.addItem(c)
        idx = self.chap_combo.findText(cur)
        if idx >= 0: self.chap_combo.setCurrentIndex(idx)
        self.chap_combo.blockSignals(False)

    def _start_session(self):
        chap = self.chap_combo.currentText() if self.chap_combo.currentIndex() > 0 else None
        limit = self.limit_spin.value()
        self.cards = db.get_due_cards(chapter=chap, limit=limit)
        if not self.cards:
            QMessageBox.information(self, "Sem cards", "Nenhum card para revisar agora. Parabéns!")
            return
        self.current_idx = 0
        self.session_id = str(uuid.uuid4())
        self.session_correct = 0
        self.session_total = 0
        self.start_time = time.time()
        mode_map = {0: "char2trans", 1: "trans2char", 2: "pinyin2char"}
        self.mode = mode_map[self.mode_combo.currentIndex()]
        self.prog_bar.setMaximum(len(self.cards))
        self._show_card()
        self.stack.setCurrentIndex(1)

    def _show_card(self):
        self.revealed = False
        self.lbl_answer.hide()
        self.lbl_example.hide()
        self.btn_reveal.show()
        self.quality_frame.hide()

        card = self.cards[self.current_idx]
        self.prog_bar.setValue(self.current_idx)

        if self.mode == "char2trans":
            self.lbl_prompt_type.setText("CARACTERE → TRADUÇÃO")
            self.lbl_prompt.setText(card["character"])
            self.lbl_hint.setText(card["pinyin"])
            self.lbl_answer.setText(card["translation"])
        elif self.mode == "trans2char":
            self.lbl_prompt_type.setText("TRADUÇÃO → CARACTERE")
            self.lbl_prompt.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            self.lbl_prompt.setText(card["translation"])
            self.lbl_hint.setText("")
            self.lbl_answer.setText(f"{card['character']}  ({card['pinyin']})")
        else:
            self.lbl_prompt_type.setText("PINYIN → CARACTERE")
            self.lbl_prompt.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
            self.lbl_prompt.setText(card["pinyin"])
            self.lbl_hint.setText(card["translation"])
            self.lbl_answer.setText(card["character"])

        example = card.get("example", "")
        self.lbl_example.setText(f'"{example}"' if example else "")

    def _reveal(self):
        self.revealed = True
        self.lbl_answer.show()
        self.lbl_example.show()
        self.btn_reveal.hide()
        self.quality_frame.show()

    def _rate(self, quality):
        card = self.cards[self.current_idx]
        db.update_srs(card["word_id"] if "word_id" in card else card["id"],
                      quality, self.session_id, self.mode)
        if quality >= 3:
            self.session_correct += 1
        self.session_total += 1
        self.current_idx += 1
        self.prog_bar.setValue(self.current_idx)

        if self.current_idx >= len(self.cards):
            self._end_session()
        else:
            self._show_card()

    def _end_session(self):
        elapsed = int(time.time() - (self.start_time or time.time()))
        mins, secs = divmod(elapsed, 60)
        accuracy = int(self.session_correct / max(self.session_total, 1) * 100)
        self.res_details.setText(
            f"✓ {self.session_correct}/{self.session_total} corretas  "
            f"({accuracy}% de acerto)\n"
            f"⏱ Tempo: {mins}m {secs}s"
        )
        self.stack.setCurrentIndex(2)


# ─── STATS PAGE ───────────────────────────────────────────────────────────────

class StatsPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(20)

        title = QLabel("Estatísticas")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        lay.addWidget(title)

        # chapter table
        chap_card = card_frame()
        chap_lay = QVBoxLayout(chap_card)
        chap_lay.setContentsMargins(16, 16, 16, 16)
        chap_lay.addWidget(section_label("PROGRESSO POR CAPÍTULO"))
        cols = ["Capítulo", "Total", "Dominadas", "Revisar", "Taxa de acerto"]
        self.chap_table = QTableWidget(0, len(cols))
        self.chap_table.setHorizontalHeaderLabels(cols)
        self.chap_table.setAlternatingRowColors(True)
        self.chap_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.chap_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.chap_table.setShowGrid(False)
        self.chap_table.verticalHeader().setVisible(False)
        self.chap_table.setMaximumHeight(220)
        chap_lay.addWidget(self.chap_table)
        lay.addWidget(chap_card)

        # accuracy chart
        acc_card = card_frame()
        acc_lay = QVBoxLayout(acc_card)
        acc_lay.setContentsMargins(16, 16, 16, 16)
        acc_lay.addWidget(section_label("TAXA DE ACERTO — ÚLTIMOS 30 DIAS"))
        self.acc_fig, self.acc_ax = plt.subplots(figsize=(8, 2.5))
        self.acc_fig.patch.set_facecolor("#faf7f2")
        self.acc_canvas = FigureCanvas(self.acc_fig)
        acc_lay.addWidget(self.acc_canvas)
        lay.addWidget(acc_card)
        lay.addStretch()

    def showEvent(self, e):
        super().showEvent(e)
        self.refresh()

    def refresh(self):
        # chapter table
        stats = db.get_chapter_stats()
        self.chap_table.setRowCount(0)
        for row_i, s in enumerate(stats):
            self.chap_table.insertRow(row_i)
            acc = s.get("avg_correct")
            acc_str = f"{int(acc*100)}%" if acc is not None else "—"
            cells = [s["chapter"], str(s["total"]),
                     str(int(s["mastered"] or 0)),
                     str(int(s["needs_review"] or 0)), acc_str]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.chap_table.setItem(row_i, col, item)

        # accuracy chart
        data = db.get_daily_stats(30)
        self.acc_ax.clear()
        if data:
            days = [d["day"] for d in data]
            rates = [(d["correct"] or 0) / max(d["total"], 1) * 100 for d in data]
            self.acc_ax.plot(days, rates, color=RED_SEAL, linewidth=2, marker="o",
                             markersize=4)
            self.acc_ax.fill_between(days, rates, alpha=0.1, color=RED_SEAL)
            self.acc_ax.set_ylim(0, 105)
            self.acc_ax.set_facecolor("#faf7f2")
            self.acc_ax.tick_params(labelsize=8, colors=MUTED)
            self.acc_ax.spines[:].set_visible(False)
            self.acc_ax.yaxis.set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda x, _: f"{int(x)}%")
            )
            plt.sca(self.acc_ax)
            plt.xticks(rotation=45, ha="right")
        else:
            self.acc_ax.text(0.5, 0.5, "Sem dados ainda",
                             ha="center", va="center", color=MUTED,
                             transform=self.acc_ax.transAxes)
            self.acc_ax.axis("off")
        self.acc_fig.tight_layout()
        self.acc_canvas.draw()


# ─── MAIN WINDOW ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("漢語 — Mandarin Study")
        self.setMinimumSize(1100, 680)
        self.setStyleSheet(STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._switch_page)
        root.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        self.dash   = DashboardPage()
        self.vocab  = VocabPage()
        self.notes  = NotesPage()
        self.study  = StudyPage()
        self.stats  = StatsPage()
        for p in [self.dash, self.vocab, self.notes, self.study, self.stats]:
            self.pages.addWidget(p)
        root.addWidget(self.pages)

    def _switch_page(self, idx):
        self.pages.setCurrentIndex(idx)
        if idx == 0:
            self.dash.refresh()
        elif idx == 4:
            self.stats.refresh()


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

def main():
    db.init_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
