import os
import sys
from pathlib import Path
from typing import cast

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .. import images


class _ImageCard(QWidget):
    clicked = Signal()

    def __init__(self, name: str, thumb_path: Path, caption: str):
        super().__init__()
        self.name = name
        self._original = caption
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        pixmap = QPixmap(str(thumb_path))
        self._thumb_label = QLabel()
        self._thumb_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self._thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._thumb_label)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 11px; color: #555;")
        layout.addWidget(name_label)

        self.caption_edit = QLineEdit(caption)
        self.caption_edit.setPlaceholderText("Legenda...")
        layout.addWidget(self.caption_edit)

        self.setLayout(layout)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def is_changed(self) -> bool:
        return self.caption_edit.text() != self._original


class _ImageDialog(QDialog):
    def __init__(self, cards: list[_ImageCard], index: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.cards = cards
        self.index = index
        self._init_ui()
        self._load_image()

    def _init_ui(self) -> None:
        self.setWindowTitle("Visualizar imagem")
        self.setMinimumSize(700, 600)
        self.setStyleSheet("font-family: system-ui, sans-serif;")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)

        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._image_label, 1)

        self._name_label = QLabel()
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setStyleSheet("font-size: 13px; color: #555; margin-top: 6px;")
        layout.addWidget(self._name_label)

        caption_layout = QHBoxLayout()
        caption_label = QLabel("Legenda:")
        self._caption_edit = QLineEdit()
        self._caption_edit.setPlaceholderText("Legenda...")
        self._caption_edit.setStyleSheet("padding: 6px 10px; font-size: 14px;")
        self._caption_edit.returnPressed.connect(self._go_next_or_close)
        caption_layout.addWidget(caption_label)
        caption_layout.addWidget(self._caption_edit, 1)
        layout.addLayout(caption_layout)

        nav_layout = QHBoxLayout()
        self._prev_btn = QPushButton("\u25C0 Anterior")
        self._prev_btn.setStyleSheet("padding: 8px 20px; font-size: 14px;")
        self._prev_btn.setAutoDefault(False)
        self._prev_btn.clicked.connect(self._go_prev)

        self._counter_label = QLabel()
        self._counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._counter_label.setStyleSheet("font-size: 13px; color: #555;")

        self._next_btn = QPushButton("Pr\u00F3xima \u25B6")
        self._next_btn.setStyleSheet("padding: 8px 20px; font-size: 14px;")
        self._next_btn.setAutoDefault(False)
        self._next_btn.clicked.connect(self._go_next)

        nav_layout.addWidget(self._prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self._counter_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self._next_btn)
        layout.addLayout(nav_layout)

        self.setLayout(layout)

    def _load_image(self) -> None:
        card = self.cards[self.index]
        img_path = images.get_image_path(card.name)
        if img_path is not None:
            pixmap = QPixmap(str(img_path))
            screen = self.screen().availableGeometry()
            max_w = min(screen.width() - 40, 1200)
            max_h = min(screen.height() - 200, 800)
            self._image_label.setPixmap(pixmap.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self._image_label.setText("Imagem n\u00E3o encontrada")
        self._name_label.setText(card.name)
        self._caption_edit.setText(card.caption_edit.text())
        self._counter_label.setText(f"{self.index + 1} / {len(self.cards)}")
        self._prev_btn.setEnabled(self.index > 0)
        self._next_btn.setEnabled(self.index < len(self.cards) - 1)
        self._caption_edit.setFocus()

    def _apply_caption(self) -> None:
        card = self.cards[self.index]
        card.caption_edit.setText(self._caption_edit.text())

    def _go_prev(self) -> None:
        if self.index > 0:
            self._apply_caption()
            self.index -= 1
            self._load_image()

    def _go_next(self) -> None:
        if self.index < len(self.cards) - 1:
            self._apply_caption()
            self.index += 1
            self._load_image()

    def _go_next_or_close(self) -> None:
        if self.index < len(self.cards) - 1:
            self._go_next()
        else:
            self._apply_caption()
            self.accept()

    def done(self, result: int) -> None:
        self._apply_caption()
        super().done(result)


class CaptionEditor(QWidget):
    def __init__(self, dir_path: Path | None = None):
        super().__init__()
        self.dir_path = dir_path
        self.cards: list[_ImageCard] = []
        self._init_ui()
        self._load_images()

    def _init_ui(self) -> None:
        self.setWindowTitle("Editor de legendas")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("font-family: system-ui, sans-serif;")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)

        header = QLabel("Editor de legendas")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(header)

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filtrar imagens...")
        self.filter_edit.setStyleSheet("padding: 6px 10px; font-size: 14px; margin-bottom: 8px;")
        self.filter_edit.textChanged.connect(self._filter_cards)
        layout.addWidget(self.filter_edit)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(8)
        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll, 1)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Salvar")
        save_btn.setStyleSheet(
            "padding: 8px 24px; font-size: 14px; font-weight: bold;"
        )
        save_btn.clicked.connect(self._save)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _load_images(self) -> None:
        if self.dir_path is not None:
            os.chdir(str(self.dir_path))

        image_list = images.list_images()
        if not image_list:
            msg = QLabel("No images found in fotos/")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setStyleSheet("font-size: 16px; color: #888; padding: 40px;")
            self.grid_layout.addWidget(msg, 0, 0)
            return

        cols = 4
        for i, img_path in enumerate(image_list):
            name = img_path.stem
            thumb = images.get_thumbnail(name)
            if thumb is None:
                continue
            caption = images.get_caption(name)
            card = _ImageCard(name, thumb, caption)
            card.clicked.connect(lambda idx=len(self.cards): self._open_card(idx))
            self.cards.append(card)
            self.grid_layout.addWidget(card, i // cols, i % cols)

    def _open_card(self, index: int) -> None:
        visible = [c for c in self.cards if c.isVisible()]
        if not visible:
            return
        try:
            vis_index = visible.index(self.cards[index])
        except ValueError:
            vis_index = 0
        dlg = _ImageDialog(visible, vis_index, self)
        dlg.exec()

    def _filter_cards(self, text: str) -> None:
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    self.grid_layout.removeWidget(widget)
                    widget.hide()

        if not self.cards:
            return

        matching = [
            card for card in self.cards
            if not text or text.lower() in card.name.lower() or text.lower() in card.caption_edit.text().lower()
        ]

        cols = 4
        for i, card in enumerate(matching):
            card.setVisible(True)
            self.grid_layout.addWidget(card, i // cols, i % cols)

        for card in self.cards:
            if card not in matching:
                card.setVisible(False)

    def _save(self) -> None:
        saved = 0
        for card in self.cards:
            if card.is_changed():
                images.set_caption(card.name, card.caption_edit.text())
                saved += 1
        self.statusBar().showMessage(f"Saved {saved} caption(s).", 3000)

    def statusBar(self) -> QStatusBar:
        parent = self.window()
        sb = cast(QStatusBar | None, parent.findChild(QStatusBar))
        if sb is None:
            sb = QStatusBar(parent)
            layout = parent.layout()
            if layout is not None:
                layout.addWidget(sb)
        return sb


def run(dir_path: Path | None = None) -> None:
    app = QApplication(sys.argv)
    icon_path = Path(__file__).parent / "assets" / "laudo.png"
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = CaptionEditor(dir_path)
    window.show()
    sys.exit(app.exec())
