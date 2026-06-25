import sys
import os
import csv
import json
import uuid
import time
import random
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
QMainWindow, QDialog {{ background: {PAPER}; }}
QWidget {{ background: {PAPER}; color: {INK}; font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; font-size: 13px; }}
QLabel {{ background: transparent; }}
QPushButton {{ background: {INK}; color: {PAPER}; border: none; border-radius: 6px; padding: 8px 18px; font-weight: 600; font-size: 13px; }}
QPushButton:hover {{ background: {RED_SEAL}; }}
QPushButton:pressed {{ background: #922b21; }}
QLineEdit, QTextEdit, QComboBox, QSpinBox {{ background: {WHITE}; border: 1.5px solid {BORDER}; border-radius: 6px; padding: 7px 10px; color: {INK}; selection-background-color: {RED_SEAL}; }}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {RED_SEAL}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ width: 10px; height: 10px; }}
QCheckBox {{ color: {INK}; spacing: 8px; background: transparent; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1.5px solid {BORDER}; border-radius: 4px; background: {WHITE}; }}
QCheckBox::indicator:checked {{ background: {RED_SEAL}; border-color: {RED_SEAL}; }}
QTableWidget {{ background: {WHITE}; alternate-background-color: {CARD_BG}; border: 1.5px solid {BORDER}; border-radius: 8px; gridline-color: {BORDER}; }}
QTableWidget::item {{ padding: 6px 8px; }}
QTableWidget::item:selected {{ background: {RED_SEAL}; color: {WHITE}; }}
QHeaderView::section {{ background: {INK}; color: {PAPER}; padding: 8px; border: none; font-weight: 600; }}
QScrollBar:vertical {{ background: {CARD_BG}; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: {MUTED}; border-radius: 4px; min-height: 30px; }}
QScrollBar:horizontal {{ background: {CARD_BG}; height: 8px; border-radius: 4px; }}
QScrollBar::handle:horizontal {{ background: {MUTED}; border-radius: 4px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QTabWidget::pane {{ border: 1.5px solid {BORDER}; border-radius: 8px; background: {WHITE}; }}
QTabBar::tab {{ background: {CARD_BG}; color: {MUTED}; padding: 8px 20px; border: 1.5px solid {BORDER}; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }}
QTabBar::tab:selected {{ background: {WHITE}; color: {INK}; font-weight: 600; border-color: {RED_SEAL}; }}
QFrame#card {{ background: {WHITE}; border: 1.5px solid {BORDER}; border-radius: 10px; }}
QFrame#link_card {{ background: {CARD_BG}; border: 1.5px solid {BORDER}; border-radius: 8px; }}
"""

def card_frame():
    f = QFrame(); f.setObjectName("card"); return f

def section_label(text):
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    lbl.setStyleSheet(f"color: {MUTED}; letter-spacing: 1px; background: transparent;")
    return lbl

def h_sep():
    line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {BORDER};"); return line

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

class SidebarBtn(QPushButton):
    def __init__(self, text, icon_char="", parent=None):
        super().__init__(parent)
        self.setText(f"  {icon_char}  {text}")
        self.setCheckable(True); self.setFixedHeight(46)
        self.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {RED_SEAL}; border: none; border-radius: 8px; text-align: left; padding-left: 12px; font-size: 13px; font-weight: 500; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.08); }}
            QPushButton:checked {{ background: {SB_ACTIVE}; color: white; font-weight: 700; }}
        """)

class Sidebar(QWidget):
    page_changed = pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar"); self.setFixedWidth(210)
        self.setStyleSheet(f"background: {SIDEBAR};")
        lay = QVBoxLayout(self); lay.setContentsMargins(12,20,12,20); lay.setSpacing(4)
        logo = QLabel("漢語"); logo.setFont(QFont("Segoe UI",28,QFont.Weight.Bold))
        logo.setStyleSheet(f"color:{RED_SEAL}; background:transparent; letter-spacing:4px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("Mandarin Study")
        sub.setStyleSheet(f"color:{MUTED}; background:transparent; font-size:10px; letter-spacing:2px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo); lay.addWidget(sub); lay.addSpacing(20)
        lay.addWidget(self._sep())
        self.btns = []
        for i,(name,icon) in enumerate([("Dashboard","⬛"),("Vocabulário","字"),("Anotações","📝"),("Estudar (SRS)","🃏"),("Estatísticas","📊")]):
            btn = SidebarBtn(name,icon)
            btn.clicked.connect(lambda _,idx=i: self._select(idx))
            lay.addWidget(btn); self.btns.append(btn)
        lay.addStretch(); lay.addWidget(self._sep())
        ver = QLabel("v1.1  •  SQLite")
        ver.setStyleSheet(f"color:{RED_SEAL}; font-size:10px; background:transparent;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(ver)
        self._select(0)

    def _sep(self):
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: rgba(255,255,255,0.08);"); return line

    def _select(self, idx):
        for i,btn in enumerate(self.btns): btn.setChecked(i==idx)
        self.page_changed.emit(idx)

    def select_external(self, idx):
        self._select(idx)

# ── DASHBOARD ─────────────────────────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, label, value, color=None):
        super().__init__(); self.setObjectName("card"); self.setFixedHeight(100)
        lay = QVBoxLayout(self); lay.setContentsMargins(16,12,16,12)
        self.val_lbl = QLabel(str(value)); self.val_lbl.setFont(QFont("Segoe UI",28,QFont.Weight.Bold))
        self.val_lbl.setStyleSheet(f"color:{color or RED_SEAL}; background:transparent;")
        txt = QLabel(label); txt.setStyleSheet(f"color:{MUTED}; font-size:11px; background:transparent;")
        lay.addWidget(self.val_lbl); lay.addWidget(txt)
    def set_value(self,v): self.val_lbl.setText(str(v))

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(20)
        title = QLabel("Dashboard"); title.setFont(QFont("Segoe UI",20,QFont.Weight.Bold))
        lay.addWidget(title)
        grid = QHBoxLayout()
        self.sc_total    = StatCard("Total de palavras", 0, INK)
        self.sc_mastered = StatCard("Dominadas",         0, JADE)
        self.sc_due      = StatCard("Para revisar hoje", 0, RED_SEAL)
        self.sc_today    = StatCard("Estudadas hoje",    0, GOLD)
        for sc in [self.sc_total,self.sc_mastered,self.sc_due,self.sc_today]: grid.addWidget(sc)
        lay.addLayout(grid)
        chart_card = card_frame(); chart_lay = QVBoxLayout(chart_card); chart_lay.setContentsMargins(16,16,16,16)
        chart_lay.addWidget(section_label("PALAVRAS ESTUDADAS — ÚLTIMOS 30 DIAS"))
        self.figure,self.ax = plt.subplots(figsize=(8,2.8)); self.figure.patch.set_facecolor("#faf7f2")
        self.canvas = FigureCanvas(self.figure); chart_lay.addWidget(self.canvas)
        lay.addWidget(chart_card); lay.addStretch()

    def refresh(self):
        s = db.get_overall_stats()
        self.sc_total.set_value(s["total_words"]); self.sc_mastered.set_value(s["mastered"])
        self.sc_due.set_value(s["due_today"]); self.sc_today.set_value(s["studied_today"])
        self._draw_chart()

    def _draw_chart(self):
        data = db.get_daily_stats(30); self.ax.clear()
        if data:
            days=[d["day"] for d in data]; totals=[d["total"] for d in data]; corrects=[d["correct"] or 0 for d in data]
            self.ax.bar(days,totals,color=f"{INK}33",label="Total"); self.ax.bar(days,corrects,color=RED_SEAL,alpha=0.8,label="Corretas")
            self.ax.set_facecolor("#faf7f2"); self.ax.tick_params(labelsize=8,colors=MUTED)
            self.ax.spines[:].set_visible(False); self.ax.legend(fontsize=8); plt.xticks(rotation=45,ha="right")
        else:
            self.ax.text(0.5,0.5,"Sem dados ainda — comece a estudar!",ha="center",va="center",color=MUTED,transform=self.ax.transAxes,fontsize=11)
            self.ax.set_facecolor("#faf7f2"); self.ax.axis("off")
        self.figure.tight_layout(); self.canvas.draw()

# ── LINK WIDGETS ──────────────────────────────────────────────────────────────

class LinkedNoteItem(QFrame):
    clicked = pyqtSignal(int)
    def __init__(self, note, parent=None):
        super().__init__(parent); self.note_id = note["id"]
        self.setObjectName("link_card"); self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(self); lay.setContentsMargins(10,8,10,8)
        icon = QLabel("📝"); icon.setFixedWidth(22)
        info = QVBoxLayout()
        title = QLabel(note["title"]); title.setFont(QFont("Segoe UI",12,QFont.Weight.Bold))
        title.setStyleSheet(f"color:{INK};")
        meta_parts = []
        if note.get("category"): meta_parts.append(note["category"])
        if note.get("chapter"):  meta_parts.append(f"Cap. {note['chapter']}")
        meta = QLabel("  •  ".join(meta_parts) if meta_parts else "Sem categoria")
        meta.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        info.addWidget(title); info.addWidget(meta)
        arrow = QLabel("→"); arrow.setStyleSheet(f"color:{RED_SEAL}; font-size:16px; font-weight:bold;")
        lay.addWidget(icon); lay.addLayout(info); lay.addStretch(); lay.addWidget(arrow)
    def mousePressEvent(self, e): self.clicked.emit(self.note_id)

# ── WORD DIALOG ───────────────────────────────────────────────────────────────

class WordDialog(QDialog):
    navigate_to_note = pyqtSignal(int)
    def __init__(self, parent=None, word=None):
        super().__init__(parent); self.word = word
        self.setWindowTitle("Editar palavra" if word else "Nova palavra")
        self.setMinimumWidth(520); self.setStyleSheet(STYLE)
        main_lay = QVBoxLayout(self); main_lay.setContentsMargins(24,24,24,24); main_lay.setSpacing(16)
        form = QFormLayout(); form.setSpacing(12)
        def field(ph=""): e=QLineEdit(); e.setPlaceholderText(ph); return e
        self.f_char=field("e.g. 你好"); self.f_pinyin=field("e.g. nǐ hǎo"); self.f_trans=field("e.g. Olá")
        self.f_gram=QComboBox(); self.f_gram.setEditable(True)
        self.f_gram.addItems(["","n.","v.","adj.","adv.","p.l.","p.c.","pron.","conj.","part.","expr."])
        self.f_exam=QTextEdit(); self.f_exam.setPlaceholderText("Exemplo de uso…"); self.f_exam.setFixedHeight(70)
        self.f_chap=field("e.g. 14")
        self.f_notes=QTextEdit(); self.f_notes.setPlaceholderText("Observações…"); self.f_notes.setFixedHeight(70)
        self.f_diff=QComboBox(); self.f_diff.addItems(["1 – Fácil","2 – Médio","3 – Difícil"])
        self.f_mast=QComboBox(); self.f_mast.addItems(["Normal","Dominada ✓","Precisa revisar ⚠"])
        form.addRow("Caractere *",self.f_char); form.addRow("Pinyin *",self.f_pinyin)
        form.addRow("Tradução *",self.f_trans); form.addRow("Tipo gram.",self.f_gram)
        form.addRow("Exemplo",self.f_exam); form.addRow("Capítulo",self.f_chap)
        form.addRow("Observações",self.f_notes); form.addRow("Dificuldade",self.f_diff)
        form.addRow("Status",self.f_mast)
        main_lay.addLayout(form)
        if word:
            main_lay.addWidget(h_sep())
            main_lay.addWidget(section_label("ANOTAÇÕES VINCULADAS"))
            self.notes_container = QVBoxLayout(); self.notes_container.setSpacing(6)
            self._load_linked_notes()
            main_lay.addLayout(self.notes_container)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save); btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        main_lay.addWidget(btns)
        if word:
            self.f_char.setText(word["character"]); self.f_pinyin.setText(word["pinyin"])
            self.f_trans.setText(word["translation"]); self.f_gram.setCurrentText(word.get("gram_type",""))
            self.f_exam.setPlainText(word.get("example","")); self.f_chap.setText(word.get("chapter",""))
            self.f_notes.setPlainText(word.get("notes","")); self.f_diff.setCurrentIndex(int(word.get("difficulty",1))-1)
            self.f_mast.setCurrentIndex(int(word.get("mastered",0)))

    def _load_linked_notes(self):
        while self.notes_container.count():
            item = self.notes_container.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        notes = db.get_notes_by_word(self.word["id"])
        if not notes:
            empty = QLabel("Nenhuma anotação vinculada a esta palavra.")
            empty.setStyleSheet(f"color:{MUTED}; font-size:12px; font-style:italic;")
            self.notes_container.addWidget(empty)
        else:
            for note in notes:
                item = LinkedNoteItem(note)
                item.clicked.connect(self._on_note_clicked)
                self.notes_container.addWidget(item)

    def _on_note_clicked(self, note_id):
        self.navigate_to_note.emit(note_id); self.accept()

    def _save(self):
        if not self.f_char.text().strip() or not self.f_pinyin.text().strip() or not self.f_trans.text().strip():
            QMessageBox.warning(self,"Campos obrigatórios","Preencha Caractere, Pinyin e Tradução."); return
        self.accept()

    def get_data(self):
        return dict(character=self.f_char.text().strip(), pinyin=self.f_pinyin.text().strip(),
                    translation=self.f_trans.text().strip(), gram_type=self.f_gram.currentText().strip(),
                    example=self.f_exam.toPlainText().strip(), chapter=self.f_chap.text().strip(),
                    notes=self.f_notes.toPlainText().strip(), difficulty=self.f_diff.currentIndex()+1,
                    mastered=self.f_mast.currentIndex())

# ── VOCAB PAGE ────────────────────────────────────────────────────────────────

class VocabPage(QWidget):
    navigate_to_note = pyqtSignal(int)
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(14)
        hdr = QHBoxLayout()
        title = QLabel("Vocabulário"); title.setFont(QFont("Segoe UI",20,QFont.Weight.Bold))
        hdr.addWidget(title); hdr.addStretch()
        btn_import = QPushButton("⬆  Importar CSV"); btn_import.setStyleSheet(f"background:{JADE};")
        btn_add = QPushButton("＋  Nova palavra")
        btn_import.clicked.connect(self._import_csv); btn_add.clicked.connect(self._add_word)
        hdr.addWidget(btn_import); hdr.addWidget(btn_add); lay.addLayout(hdr)
        filt = QHBoxLayout()
        self.s_search=QLineEdit(); self.s_search.setPlaceholderText("🔍  Buscar…")
        self.s_chap=QComboBox(); self.s_chap.addItem("Todos os capítulos")
        self.s_gram=QComboBox(); self.s_gram.addItem("Todos os tipos")
        self.s_diff=QComboBox(); self.s_diff.addItems(["Dificuldade","1 – Fácil","2 – Médio","3 – Difícil"])
        self.s_mast=QComboBox(); self.s_mast.addItems(["Todos os status","Normal","Dominada","Revisar"])
        for w in [self.s_search,self.s_chap,self.s_gram,self.s_diff,self.s_mast]:
            filt.addWidget(w)
            if hasattr(w,"textChanged"): w.textChanged.connect(self._refresh)
            else: w.currentIndexChanged.connect(self._refresh)
        lay.addLayout(filt)
        cols=["#","Caractere","Pinyin","Tradução","Tipo","Exemplo","Capítulo","Dificuldade","Status",""]
        self.table=QTableWidget(0,len(cols)); self.table.setHorizontalHeaderLabels(cols)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        hdr.setMinimumSectionSize(46)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(6, 80)
        self.table.setColumnWidth(7, 90)
        self.table.setColumnWidth(8, 100)
        self.table.setColumnWidth(9, 46)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._edit_selected)
        lay.addWidget(self.table); self._word_ids=[]

    def showEvent(self,e): super().showEvent(e); self._refresh_filters(); self._refresh()

    def _refresh_filters(self):
        cur_chap=self.s_chap.currentText(); cur_gram=self.s_gram.currentText()
        self.s_chap.blockSignals(True); self.s_gram.blockSignals(True)
        self.s_chap.clear(); self.s_chap.addItem("Todos os capítulos")
        self.s_gram.clear(); self.s_gram.addItem("Todos os tipos")
        for c in db.get_chapters(): self.s_chap.addItem(c)
        for g in db.get_gram_types(): self.s_gram.addItem(g)
        idx=self.s_chap.findText(cur_chap)
        if idx>=0: self.s_chap.setCurrentIndex(idx)
        idx=self.s_gram.findText(cur_gram)
        if idx>=0: self.s_gram.setCurrentIndex(idx)
        self.s_chap.blockSignals(False); self.s_gram.blockSignals(False)

    def _refresh(self):
        chap=self.s_chap.currentText() if self.s_chap.currentIndex()>0 else None
        gram=self.s_gram.currentText() if self.s_gram.currentIndex()>0 else None
        diff_i=self.s_diff.currentIndex(); diff=diff_i if diff_i>0 else None
        mast_i=self.s_mast.currentIndex(); mast=(mast_i-1) if mast_i>0 else None
        search=self.s_search.text().strip() or None
        words=db.get_words(chapter=chap,gram_type=gram,difficulty=diff,mastered=mast,search=search)
        self._word_ids=[w["id"] for w in words]; self.table.setRowCount(0)
        status_map={0:"Normal",1:"✓ Dominada",2:"⚠ Revisar"}; diff_map={1:"Fácil",2:"Médio",3:"Difícil"}
        for row_i,w in enumerate(words):
            self.table.insertRow(row_i)
            cells=[str(row_i+1),w["character"],w["pinyin"],w["translation"],w.get("gram_type",""),w.get("example",""),w.get("chapter",""),diff_map.get(w.get("difficulty",1),""),status_map.get(w.get("mastered",0),"")]
            for col,val in enumerate(cells):
                item=QTableWidgetItem(val); item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft)
                if col==1: item.setFont(QFont("Segoe UI",15))
                if w.get("mastered")==1: item.setForeground(QColor(JADE))
                elif w.get("mastered")==2: item.setForeground(QColor(RED_SEAL))
                self.table.setItem(row_i,col,item)
            edit_btn=QPushButton("✏"); edit_btn.setFixedSize(36,30)
            edit_btn.setStyleSheet(f"background:{GOLD}; color:white; border-radius:4px; font-size:13px;")
            edit_btn.clicked.connect(lambda _,wid=w["id"]: self._edit_word(wid))
            self.table.setCellWidget(row_i,9,edit_btn)

    def _add_word(self):
        dlg=WordDialog(self)
        if dlg.exec():
            db.add_word(**dlg.get_data()); self._refresh_filters(); self._refresh()

    def _edit_selected(self):
        row=self.table.currentRow()
        if row<len(self._word_ids): self._edit_word(self._word_ids[row])

    def _edit_word(self, word_id):
        word=db.get_word(word_id)
        if not word: return
        dlg=WordDialog(self,word)
        dlg.navigate_to_note.connect(self.navigate_to_note.emit)
        if dlg.exec():
            d=dlg.get_data()
            db.update_word(word_id,d["character"],d["pinyin"],d["translation"],d["gram_type"],d["example"],d["chapter"],d["notes"],d["difficulty"],d["mastered"])
            self._refresh()

    def _import_csv(self):
        path,_=QFileDialog.getOpenFileName(self,"Selecionar CSV","","CSV Files (*.csv)")
        if not path: return
        rows=[]
        with open(path,newline="",encoding="utf-8") as f:
            for row in csv.DictReader(f): rows.append(row)
        if not rows: QMessageBox.warning(self,"Arquivo vazio","O CSV não contém dados."); return
        added,skipped=db.import_words_csv(rows)
        QMessageBox.information(self,"Importação concluída",f"✓ {added} palavras adicionadas.\n✗ {skipped} ignoradas (sem caractere).")
        self._refresh_filters(); self._refresh()

    def highlight_word(self, word_id):
        self._refresh()
        for row,wid in enumerate(self._word_ids):
            if wid==word_id:
                self.table.selectRow(row); self.table.scrollToItem(self.table.item(row,0)); break

# ── NOTE DIALOG ───────────────────────────────────────────────────────────────

class NoteDialog(QDialog):
    navigate_to_word = pyqtSignal(int)
    def __init__(self, parent=None, note=None):
        super().__init__(parent); self.note=note
        self._selected_word_id = note["word_id"] if note and note.get("word_id") else None
        self.setWindowTitle("Editar anotação" if note else "Nova anotação")
        self.setMinimumSize(560,540); self.setStyleSheet(STYLE)
        lay=QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(12)
        form=QFormLayout(); form.setSpacing(10)
        self.f_title=QLineEdit(); self.f_title.setPlaceholderText("Título…")
        self.f_cat=QLineEdit(); self.f_cat.setPlaceholderText("Categoria")
        self.f_tags=QLineEdit(); self.f_tags.setPlaceholderText("Tags separadas por vírgula")
        self.f_chap=QLineEdit(); self.f_chap.setPlaceholderText("Capítulo relacionado")
        form.addRow("Título *",self.f_title); form.addRow("Categoria",self.f_cat)
        form.addRow("Tags",self.f_tags); form.addRow("Capítulo",self.f_chap)
        lay.addLayout(form)
        lay.addWidget(h_sep()); lay.addWidget(section_label("PALAVRA VINCULADA"))
        word_row=QHBoxLayout()
        self.word_combo=QComboBox(); self.word_combo.setEditable(True)
        self.word_combo.lineEdit().setPlaceholderText("Buscar e selecionar palavra…")
        self.word_combo.setMinimumWidth(300)
        self._word_map={}; self._populate_word_combo()
        self.word_combo.currentIndexChanged.connect(self._on_word_combo_changed)
        btn_clear=QPushButton("✕ Remover vínculo")
        btn_clear.setStyleSheet(f"background:transparent; color:{MUTED}; border:1px solid {BORDER}; padding:6px 12px;")
        btn_clear.clicked.connect(self._clear_word)
        word_row.addWidget(self.word_combo); word_row.addWidget(btn_clear); lay.addLayout(word_row)
        # Preview da palavra vinculada
        self.word_preview=QFrame(); self.word_preview.setObjectName("link_card"); self.word_preview.hide()
        self.word_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        wp_lay=QHBoxLayout(self.word_preview); wp_lay.setContentsMargins(10,8,10,8)
        self.wp_char=QLabel(""); self.wp_char.setFont(QFont("Segoe UI",20,QFont.Weight.Bold)); self.wp_char.setFixedWidth(44)
        wp_info=QVBoxLayout()
        self.wp_pinyin=QLabel(""); self.wp_pinyin.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        self.wp_trans=QLabel(""); self.wp_trans.setStyleSheet(f"color:{INK}; font-size:12px;")
        wp_info.addWidget(self.wp_pinyin); wp_info.addWidget(self.wp_trans)
        wp_arr=QLabel("→ Ver palavra"); wp_arr.setStyleSheet(f"color:{RED_SEAL}; font-size:12px; font-weight:bold;")
        wp_lay.addWidget(self.wp_char); wp_lay.addLayout(wp_info); wp_lay.addStretch(); wp_lay.addWidget(wp_arr)
        self.word_preview.mousePressEvent=lambda e: self._go_to_word()
        lay.addWidget(self.word_preview)
        lay.addWidget(h_sep())
        body_lbl=QLabel("Conteúdo"); body_lbl.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        lay.addWidget(body_lbl)
        self.f_body=QTextEdit(); self.f_body.setPlaceholderText("Escreva sua anotação aqui…"); lay.addWidget(self.f_body)
        btns=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save); btns.rejected.connect(self.reject)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        lay.addWidget(btns)
        if note:
            self.f_title.setText(note["title"]); self.f_cat.setText(note.get("category",""))
            self.f_tags.setText(", ".join(json.loads(note.get("tags","[]") or "[]")))
            self.f_chap.setText(note.get("chapter","")); self.f_body.setPlainText(note.get("body",""))
            if note.get("word_id"):
                self._set_word_preview(note["word_id"])
                for text,wid in self._word_map.items():
                    if wid==note["word_id"]:
                        idx=self.word_combo.findText(text)
                        if idx>=0:
                            self.word_combo.blockSignals(True); self.word_combo.setCurrentIndex(idx); self.word_combo.blockSignals(False)
                        break

    def _populate_word_combo(self):
        self.word_combo.blockSignals(True); self.word_combo.clear(); self.word_combo.addItem("— Nenhuma —"); self._word_map={}
        for w in db.get_words_for_combo():
            label=f"{w['character']}  {w['pinyin']}  —  {w['translation']}"; self.word_combo.addItem(label); self._word_map[label]=w["id"]
        self.word_combo.blockSignals(False)

    def _on_word_combo_changed(self,idx):
        text=self.word_combo.currentText(); word_id=self._word_map.get(text)
        if word_id: self._selected_word_id=word_id; self._set_word_preview(word_id)
        else: self._selected_word_id=None; self.word_preview.hide()

    def _set_word_preview(self,word_id):
        word=db.get_word(word_id)
        if not word: return
        self.wp_char.setText(word["character"]); self.wp_pinyin.setText(word["pinyin"]); self.wp_trans.setText(word["translation"]); self.word_preview.show()

    def _clear_word(self):
        self._selected_word_id=None; self.word_combo.blockSignals(True); self.word_combo.setCurrentIndex(0); self.word_combo.blockSignals(False); self.word_preview.hide()

    def _go_to_word(self):
        if self._selected_word_id: self.navigate_to_word.emit(self._selected_word_id); self.accept()

    def _save(self):
        if not self.f_title.text().strip(): QMessageBox.warning(self,"Campo obrigatório","Digite um título."); return
        self.accept()

    def get_data(self):
        raw_tags=[t.strip() for t in self.f_tags.text().split(",") if t.strip()]
        return dict(title=self.f_title.text().strip(), body=self.f_body.toPlainText().strip(),
                    category=self.f_cat.text().strip(), tags=json.dumps(raw_tags,ensure_ascii=False),
                    chapter=self.f_chap.text().strip(), word_id=self._selected_word_id)

# ── NOTES PAGE ────────────────────────────────────────────────────────────────

class NotesPage(QWidget):
    navigate_to_word=pyqtSignal(int)
    def __init__(self):
        super().__init__()
        lay=QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(14)
        hdr=QHBoxLayout(); title=QLabel("Anotações"); title.setFont(QFont("Segoe UI",20,QFont.Weight.Bold))
        hdr.addWidget(title); hdr.addStretch()
        btn_add=QPushButton("＋  Nova anotação"); btn_add.clicked.connect(self._add_note); hdr.addWidget(btn_add); lay.addLayout(hdr)
        filt=QHBoxLayout()
        self.s_search=QLineEdit(); self.s_search.setPlaceholderText("🔍  Buscar título, corpo, tags…")
        self.s_cat=QComboBox(); self.s_cat.addItem("Todas as categorias")
        self.s_chap=QComboBox(); self.s_chap.addItem("Todos os capítulos")
        for w in [self.s_search,self.s_cat,self.s_chap]:
            filt.addWidget(w)
            if hasattr(w,"textChanged"): w.textChanged.connect(self._refresh)
            else: w.currentIndexChanged.connect(self._refresh)
        lay.addLayout(filt)
        splitter=QSplitter(Qt.Orientation.Horizontal)
        self.list_widget=QListWidget()
        self.list_widget.setStyleSheet(f"QListWidget {{background:{WHITE};border:1.5px solid {BORDER};border-radius:8px;}} QListWidget::item {{padding:12px;border-bottom:1px solid {BORDER};}} QListWidget::item:selected {{background:{RED_SEAL};color:white;}}")
        self.list_widget.currentItemChanged.connect(self._show_note); splitter.addWidget(self.list_widget)
        preview=card_frame(); prev_lay=QVBoxLayout(preview); prev_lay.setContentsMargins(16,16,16,16); prev_lay.setSpacing(10)
        self.prev_title=QLabel("Selecione uma anotação"); self.prev_title.setFont(QFont("Segoe UI",15,QFont.Weight.Bold)); self.prev_title.setWordWrap(True)
        self.prev_meta=QLabel(""); self.prev_meta.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        # Card da palavra vinculada
        self.prev_word_frame=QFrame(); self.prev_word_frame.setObjectName("link_card")
        self.prev_word_frame.setCursor(Qt.CursorShape.PointingHandCursor); self.prev_word_frame.hide()
        pw_lay=QHBoxLayout(self.prev_word_frame); pw_lay.setContentsMargins(10,8,10,8)
        pw_icon=QLabel("字"); pw_icon.setStyleSheet(f"color:{RED_SEAL}; font-size:16px; font-weight:bold;"); pw_icon.setFixedWidth(24)
        self.pw_text=QLabel(""); self.pw_text.setStyleSheet(f"color:{INK}; font-size:13px;")
        pw_arr=QLabel("→ Ver palavra"); pw_arr.setStyleSheet(f"color:{RED_SEAL}; font-size:12px; font-weight:bold;")
        pw_lay.addWidget(pw_icon); pw_lay.addWidget(self.pw_text); pw_lay.addStretch(); pw_lay.addWidget(pw_arr)
        self.prev_word_frame.mousePressEvent=lambda e: self._go_to_linked_word()
        self.prev_body=QTextEdit(); self.prev_body.setReadOnly(True); self.prev_body.setStyleSheet("border:none; background:transparent;")
        prev_btns=QHBoxLayout()
        self.btn_edit=QPushButton("✏ Editar"); self.btn_del=QPushButton("🗑 Excluir"); self.btn_del.setStyleSheet(f"background:{RED_SEAL};")
        self.btn_edit.clicked.connect(self._edit_note); self.btn_del.clicked.connect(self._delete_note)
        prev_btns.addWidget(self.btn_edit); prev_btns.addWidget(self.btn_del); prev_btns.addStretch()
        prev_lay.addWidget(self.prev_title); prev_lay.addWidget(self.prev_meta)
        prev_lay.addWidget(self.prev_word_frame); prev_lay.addWidget(h_sep())
        prev_lay.addWidget(self.prev_body); prev_lay.addLayout(prev_btns)
        splitter.addWidget(preview); splitter.setSizes([260,500]); lay.addWidget(splitter)
        self._notes=[]; self._current_note=None

    def showEvent(self,e): super().showEvent(e); self._refresh_filters(); self._refresh()

    def _refresh_filters(self):
        self.s_cat.blockSignals(True); self.s_chap.blockSignals(True)
        cur_cat=self.s_cat.currentText(); cur_ch=self.s_chap.currentText()
        self.s_cat.clear(); self.s_cat.addItem("Todas as categorias")
        self.s_chap.clear(); self.s_chap.addItem("Todos os capítulos")
        for c in db.get_note_categories(): self.s_cat.addItem(c)
        for c in db.get_chapters(): self.s_chap.addItem(c)
        idx=self.s_cat.findText(cur_cat)
        if idx>=0: self.s_cat.setCurrentIndex(idx)
        idx=self.s_chap.findText(cur_ch)
        if idx>=0: self.s_chap.setCurrentIndex(idx)
        self.s_cat.blockSignals(False); self.s_chap.blockSignals(False)

    def _refresh(self):
        search=self.s_search.text().strip() or None
        cat=self.s_cat.currentText() if self.s_cat.currentIndex()>0 else None
        chap=self.s_chap.currentText() if self.s_chap.currentIndex()>0 else None
        self._notes=db.get_notes(search=search,category=cat,chapter=chap)
        self.list_widget.clear()
        for note in self._notes:
            tags=json.loads(note.get("tags","[]") or "[]"); tag_str="  ".join(f"#{t}" for t in tags)
            linked="  🔗" if note.get("word_id") else ""
            item=QListWidgetItem(f"{note['title']}{linked}\n{note.get('category','')}  {tag_str}")
            item.setData(Qt.ItemDataRole.UserRole,note["id"]); self.list_widget.addItem(item)

    def _show_note(self,item):
        if not item: return
        note_id=item.data(Qt.ItemDataRole.UserRole)
        self._current_note=next((n for n in self._notes if n["id"]==note_id),None)
        if not self._current_note: return
        tags=json.loads(self._current_note.get("tags","[]") or "[]")
        self.prev_title.setText(self._current_note["title"])
        meta=[]
        if self._current_note.get("category"): meta.append(self._current_note["category"])
        if self._current_note.get("chapter"):  meta.append(f"Cap. {self._current_note['chapter']}")
        if tags: meta.append("  ".join(f"#{t}" for t in tags))
        self.prev_meta.setText("  •  ".join(meta)); self.prev_body.setPlainText(self._current_note.get("body",""))
        word_id=self._current_note.get("word_id")
        if word_id:
            word=db.get_word(word_id)
            if word:
                self.pw_text.setText(f"{word['character']}  {word['pinyin']}  —  {word['translation']}"); self.prev_word_frame.show()
            else: self.prev_word_frame.hide()
        else: self.prev_word_frame.hide()

    def _go_to_linked_word(self):
        if self._current_note and self._current_note.get("word_id"):
            self.navigate_to_word.emit(self._current_note["word_id"])

    def _add_note(self):
        dlg=NoteDialog(self); dlg.navigate_to_word.connect(self.navigate_to_word.emit)
        if dlg.exec():
            d=dlg.get_data(); db.add_note(**d); self._refresh_filters(); self._refresh()

    def _edit_note(self):
        if not self._current_note: return
        dlg=NoteDialog(self,self._current_note); dlg.navigate_to_word.connect(self.navigate_to_word.emit)
        if dlg.exec():
            d=dlg.get_data()
            db.update_note(self._current_note["id"],d["title"],d["body"],d["category"],d["tags"],d["chapter"],d["word_id"])
            self._refresh()
            updated=next((n for n in db.get_notes() if n["id"]==self._current_note["id"]),None)
            if updated:
                self._current_note=updated
                class FI:
                    def data(self,_): return updated["id"]
                self._show_note(FI())

    def select_note(self,note_id):
        self._refresh()
        for i in range(self.list_widget.count()):
            item=self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole)==note_id:
                self.list_widget.setCurrentItem(item); self.list_widget.scrollToItem(item); break

    def _delete_note(self):
        if not self._current_note: return
        if QMessageBox.question(self,"Confirmar","Excluir esta anotação?")==QMessageBox.StandardButton.Yes:
            db.delete_note(self._current_note["id"]); self._current_note=None
            self.prev_title.setText("Selecione uma anotação"); self.prev_body.clear()
            self.prev_word_frame.hide(); self._refresh()

# ── STUDY PAGE ────────────────────────────────────────────────────────────────

class StudyPage(QWidget):
    def __init__(self):
        super().__init__(); self.session_id=str(uuid.uuid4()); self.cards=[]; self.current_idx=0
        self.revealed=False; self.session_correct=0; self.session_total=0; self.mode="char2trans"; self.start_time=None
        lay=QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(14)
        hdr=QHBoxLayout(); title=QLabel("Estudar"); title.setFont(QFont("Segoe UI",20,QFont.Weight.Bold))
        hdr.addWidget(title); hdr.addStretch()
        self.mode_combo=QComboBox(); self.mode_combo.addItems(["Caractere → Tradução","Tradução → Caractere","Pinyin → Caractere"])
        self.chap_combo=QComboBox(); self.chap_combo.addItem("Todos os capítulos")
        self.gram_combo=QComboBox(); self.gram_combo.addItem("Todos os tipos")
        self.diff_combo=QComboBox(); self.diff_combo.addItems(["Dificuldade","1 – Fácil","2 – Médio","3 – Difícil"])
        self.limit_spin=QSpinBox(); self.limit_spin.setRange(5,100); self.limit_spin.setValue(20); self.limit_spin.setPrefix("Limite: ")
        self.chk_hide_pinyin=QCheckBox("Ocultar pinyin até revelar")
        self.chk_shuffle=QCheckBox("Embaralhar")
        self.chk_force=QCheckBox("Estudar tudo")
        hdr.addWidget(QLabel("Modo:")); hdr.addWidget(self.mode_combo)
        hdr.addWidget(QLabel("Capítulo:")); hdr.addWidget(self.chap_combo)
        hdr.addWidget(QLabel("Tipo gramatical:")); hdr.addWidget(self.gram_combo)
        hdr.addWidget(self.diff_combo); hdr.addWidget(self.limit_spin)
        hdr.addWidget(self.chk_hide_pinyin); hdr.addWidget(self.chk_shuffle); hdr.addWidget(self.chk_force)
        btn_start=QPushButton("▶  Iniciar sessão"); btn_start.clicked.connect(self._start_session); hdr.addWidget(btn_start); lay.addLayout(hdr)
        self.prog_bar=QProgressBar()
        self.prog_bar.setStyleSheet(f"QProgressBar {{background:{BORDER};border-radius:4px;height:8px;text-align:center;color:transparent;}} QProgressBar::chunk {{background:{RED_SEAL};border-radius:4px;}}")
        self.prog_bar.setFixedHeight(8); lay.addWidget(self.prog_bar)
        self.stack=QStackedWidget()
        idle=QWidget(); idle_lay=QVBoxLayout(idle); idle_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_icon=QLabel("🃏"); idle_icon.setFont(QFont("Segoe UI",48)); idle_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_msg=QLabel("Configure o deck acima e clique em Iniciar sessão"); idle_msg.setStyleSheet(f"color:{MUTED}; font-size:15px;"); idle_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_lay.addWidget(idle_icon); idle_lay.addWidget(idle_msg); self.stack.addWidget(idle)
        fc=QWidget(); fc_lay=QVBoxLayout(fc); fc_lay.setAlignment(Qt.AlignmentFlag.AlignCenter); fc_lay.setSpacing(20)
        self.card_frame_widget=card_frame(); self.card_frame_widget.setMinimumSize(900, 480)
        self.card_frame_widget.setMaximumSize(16777215, 16777215)
        cf_lay=QVBoxLayout(self.card_frame_widget); cf_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prompt_type=QLabel(""); self.lbl_prompt_type.setStyleSheet(f"color:{MUTED}; font-size:16px; letter-spacing:2px;"); self.lbl_prompt_type.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prompt=QLabel(""); self.lbl_prompt.setFont(QFont("Segoe UI",96,QFont.Weight.Bold)); self.lbl_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter); self.lbl_prompt.setWordWrap(True)
        self.lbl_hint=QLabel(""); self.lbl_hint.setStyleSheet(f"color:{MUTED}; font-size:28px;"); self.lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_answer=QLabel(""); self.lbl_answer.setFont(QFont("Segoe UI",44)); self.lbl_answer.setAlignment(Qt.AlignmentFlag.AlignCenter); self.lbl_answer.setWordWrap(True)
        self.lbl_example=QLabel(""); self.lbl_example.setStyleSheet(f"color:{MUTED}; font-size:19px; font-style:italic;"); self.lbl_example.setAlignment(Qt.AlignmentFlag.AlignCenter); self.lbl_example.setWordWrap(True)
        for w in [self.lbl_prompt_type,self.lbl_prompt,self.lbl_hint,h_sep(),self.lbl_answer,self.lbl_example]: cf_lay.addWidget(w)
        fc_lay.addWidget(self.card_frame_widget,alignment=Qt.AlignmentFlag.AlignCenter)
        self.btn_reveal=QPushButton("👁  Revelar resposta"); self.btn_reveal.setFixedWidth(220); self.btn_reveal.clicked.connect(self._reveal)
        fc_lay.addWidget(self.btn_reveal,alignment=Qt.AlignmentFlag.AlignCenter)
        self.quality_frame=QFrame(); q_lay=QHBoxLayout(self.quality_frame); q_lay.setSpacing(8)
        for label,quality,color in [("✗ Errei",0,RED_SEAL),("Difícil",2,"#e67e22"),("Bom",3,GOLD),("Fácil",4,JADE),("✓ Muito fácil",5,"#1a7d4b")]:
            btn=QPushButton(label); btn.setStyleSheet(f"background:{color}; min-width:90px;"); btn.clicked.connect(lambda _,q=quality: self._rate(q)); q_lay.addWidget(btn)
        self.quality_frame.hide(); fc_lay.addWidget(self.quality_frame,alignment=Qt.AlignmentFlag.AlignCenter); self.stack.addWidget(fc)
        results=QWidget(); res_lay=QVBoxLayout(results); res_lay.setAlignment(Qt.AlignmentFlag.AlignCenter); res_lay.setSpacing(16)
        self.res_title=QLabel("Sessão concluída! 🎉"); self.res_title.setFont(QFont("Segoe UI",22,QFont.Weight.Bold)); self.res_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.res_details=QLabel(""); self.res_details.setStyleSheet(f"color:{MUTED}; font-size:14px;"); self.res_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_restart=QPushButton("↺  Nova sessão"); btn_restart.setFixedWidth(180); btn_restart.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        res_lay.addWidget(self.res_title); res_lay.addWidget(self.res_details); res_lay.addWidget(btn_restart,alignment=Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(results); lay.addWidget(self.stack)

    def showEvent(self,e):
        super().showEvent(e); cur=self.chap_combo.currentText(); self.chap_combo.blockSignals(True)
        self.chap_combo.clear(); self.chap_combo.addItem("Todos os capítulos")
        for c in db.get_chapters(): self.chap_combo.addItem(c)
        idx=self.chap_combo.findText(cur)
        if idx>=0: self.chap_combo.setCurrentIndex(idx)
        self.chap_combo.blockSignals(False)
        cur_g=self.gram_combo.currentText(); self.gram_combo.blockSignals(True)
        self.gram_combo.clear(); self.gram_combo.addItem("Todos os tipos")
        for g in db.get_gram_types(): self.gram_combo.addItem(g)
        idx=self.gram_combo.findText(cur_g)
        if idx>=0: self.gram_combo.setCurrentIndex(idx)
        self.gram_combo.blockSignals(False)

    def _start_session(self):
        chap=self.chap_combo.currentText() if self.chap_combo.currentIndex()>0 else None
        gram=self.gram_combo.currentText() if self.gram_combo.currentIndex()>0 else None
        diff_i=self.diff_combo.currentIndex(); diff=diff_i if diff_i>0 else None
        self.cards=db.get_due_cards(chapter=chap,limit=self.limit_spin.value(),gram_type=gram,difficulty=diff,force=self.chk_force.isChecked())
        if self.chk_shuffle.isChecked(): random.shuffle(self.cards)
        if not self.cards: QMessageBox.information(self,"Sem cards","Nenhum card para revisar agora. Parabéns!"); return
        self.current_idx=0; self.session_id=str(uuid.uuid4()); self.session_correct=self.session_total=0
        self.start_time=time.time(); self.mode={0:"char2trans",1:"trans2char",2:"pinyin2char"}[self.mode_combo.currentIndex()]
        self.prog_bar.setMaximum(len(self.cards)); self._show_card(); self.stack.setCurrentIndex(1)

    def _show_card(self):
        self.revealed=False; self.lbl_answer.hide(); self.lbl_example.hide(); self.btn_reveal.show(); self.quality_frame.hide()
        card=self.cards[self.current_idx]; self.prog_bar.setValue(self.current_idx)
        if self.mode=="char2trans":
            self.lbl_prompt_type.setText("CARACTERE → TRADUÇÃO"); self.lbl_prompt.setText(card["character"])
            self.lbl_hint.setText("" if self.chk_hide_pinyin.isChecked() else card["pinyin"]); self.lbl_answer.setText(card["translation"])
        elif self.mode=="trans2char":
            self.lbl_prompt_type.setText("TRADUÇÃO → CARACTERE"); self.lbl_prompt.setFont(QFont("Segoe UI",60,QFont.Weight.Bold)); self.lbl_prompt.setText(card["translation"]); self.lbl_hint.setText(""); self.lbl_answer.setText(f"{card['character']}  ({card['pinyin']})")
        else:
            self.lbl_prompt_type.setText("PINYIN → CARACTERE"); self.lbl_prompt.setFont(QFont("Segoe UI",72,QFont.Weight.Bold)); self.lbl_prompt.setText(card["pinyin"]); self.lbl_hint.setText(card["translation"]); self.lbl_answer.setText(card["character"])
        self.lbl_example.setText(f'"{card["example"]}"' if card.get("example") else "")

    def _reveal(self):
        self.revealed=True
        if self.mode=="char2trans" and self.chk_hide_pinyin.isChecked():
            self.lbl_hint.setText(self.cards[self.current_idx]["pinyin"])
        self.lbl_answer.show(); self.lbl_example.show(); self.btn_reveal.hide(); self.quality_frame.show()

    def _rate(self,quality):
        card=self.cards[self.current_idx]; db.update_srs(card.get("word_id",card["id"]),quality,self.session_id,self.mode)
        if quality>=3: self.session_correct+=1
        self.session_total+=1; self.current_idx+=1; self.prog_bar.setValue(self.current_idx)
        if self.current_idx>=len(self.cards): self._end_session()
        else: self._show_card()

    def _end_session(self):
        elapsed=int(time.time()-(self.start_time or time.time())); mins,secs=divmod(elapsed,60)
        accuracy=int(self.session_correct/max(self.session_total,1)*100)
        self.res_details.setText(f"✓ {self.session_correct}/{self.session_total} corretas  ({accuracy}% de acerto)\n⏱ Tempo: {mins}m {secs}s")
        self.stack.setCurrentIndex(2)

# ── STATS PAGE ────────────────────────────────────────────────────────────────

class StatsPage(QWidget):
    def __init__(self):
        super().__init__()
        lay=QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(20)
        title=QLabel("Estatísticas"); title.setFont(QFont("Segoe UI",20,QFont.Weight.Bold)); lay.addWidget(title)
        chap_card=card_frame(); chap_lay=QVBoxLayout(chap_card); chap_lay.setContentsMargins(16,16,16,16)
        chap_lay.addWidget(section_label("PROGRESSO POR CAPÍTULO"))
        cols=["Capítulo","Total","Dominadas","Revisar","Taxa de acerto"]
        self.chap_table=QTableWidget(0,len(cols)); self.chap_table.setHorizontalHeaderLabels(cols)
        self.chap_table.setAlternatingRowColors(True); self.chap_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.chap_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.chap_table.setShowGrid(False); self.chap_table.verticalHeader().setVisible(False); self.chap_table.setMaximumHeight(220)
        chap_lay.addWidget(self.chap_table); lay.addWidget(chap_card)
        acc_card=card_frame(); acc_lay=QVBoxLayout(acc_card); acc_lay.setContentsMargins(16,16,16,16)
        acc_lay.addWidget(section_label("TAXA DE ACERTO — ÚLTIMOS 30 DIAS"))
        self.acc_fig,self.acc_ax=plt.subplots(figsize=(8,2.5)); self.acc_fig.patch.set_facecolor("#faf7f2")
        self.acc_canvas=FigureCanvas(self.acc_fig); acc_lay.addWidget(self.acc_canvas)
        lay.addWidget(acc_card); lay.addStretch()

    def showEvent(self,e): super().showEvent(e); self.refresh()

    def refresh(self):
        stats=db.get_chapter_stats(); self.chap_table.setRowCount(0)
        for row_i,s in enumerate(stats):
            self.chap_table.insertRow(row_i); acc=s.get("avg_correct"); acc_str=f"{int(acc*100)}%" if acc is not None else "—"
            for col,val in enumerate([s["chapter"],str(s["total"]),str(int(s["mastered"] or 0)),str(int(s["needs_review"] or 0)),acc_str]):
                item=QTableWidgetItem(val); item.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.chap_table.setItem(row_i,col,item)
        data=db.get_daily_stats(30); self.acc_ax.clear()
        if data:
            days=[d["day"] for d in data]; rates=[(d["correct"] or 0)/max(d["total"],1)*100 for d in data]
            self.acc_ax.plot(days,rates,color=RED_SEAL,linewidth=2,marker="o",markersize=4)
            self.acc_ax.fill_between(days,rates,alpha=0.1,color=RED_SEAL); self.acc_ax.set_ylim(0,105)
            self.acc_ax.set_facecolor("#faf7f2"); self.acc_ax.tick_params(labelsize=8,colors=MUTED)
            self.acc_ax.spines[:].set_visible(False)
            self.acc_ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x,_: f"{int(x)}%"))
            plt.sca(self.acc_ax); plt.xticks(rotation=45,ha="right")
        else:
            self.acc_ax.text(0.5,0.5,"Sem dados ainda",ha="center",va="center",color=MUTED,transform=self.acc_ax.transAxes); self.acc_ax.axis("off")
        self.acc_fig.tight_layout(); self.acc_canvas.draw()

# ── MAIN WINDOW ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("漢語 — Mandarin Study"); self.setMinimumSize(1100,680); self.setStyleSheet(STYLE)
        central=QWidget(); self.setCentralWidget(central)
        root=QHBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.sidebar=Sidebar(); self.sidebar.page_changed.connect(self._switch_page); root.addWidget(self.sidebar)
        self.pages=QStackedWidget()
        self.dash=DashboardPage(); self.vocab=VocabPage(); self.notes=NotesPage(); self.study=StudyPage(); self.stats=StatsPage()
        for p in [self.dash,self.vocab,self.notes,self.study,self.stats]: self.pages.addWidget(p)
        root.addWidget(self.pages)
        # Navegação cruzada
        self.vocab.navigate_to_note.connect(self._go_to_note)
        self.notes.navigate_to_word.connect(self._go_to_word)

    def _switch_page(self,idx):
        self.pages.setCurrentIndex(idx)
        if idx==0: self.dash.refresh()
        elif idx==4: self.stats.refresh()

    def _go_to_note(self,note_id):
        self.sidebar.select_external(2); self.pages.setCurrentIndex(2); self.notes.select_note(note_id)

    def _go_to_word(self,word_id):
        self.sidebar.select_external(1); self.pages.setCurrentIndex(1); self.vocab.highlight_word(word_id)

def main():
    db.init_db(); app=QApplication(sys.argv); app.setStyle("Fusion"); win=MainWindow(); win.show(); sys.exit(app.exec())

if __name__=="__main__":
    main()