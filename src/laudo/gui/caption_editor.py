import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .. import images


class _ImageCard(QWidget):
    def __init__(self, name: str, thumb_path: Path, caption: str):
        super().__init__()
        self.name = name
        self._original = caption
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        pixmap = QPixmap(str(thumb_path))
        thumb_label = QLabel()
        thumb_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(thumb_label)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 11px; color: #555;")
        layout.addWidget(name_label)

        self.caption_edit = QLineEdit(caption)
        self.caption_edit.setPlaceholderText("Legenda...")
        layout.addWidget(self.caption_edit)

        self.setLayout(layout)

    def is_changed(self) -> bool:
        return self.caption_edit.text() != self._original


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
            self.cards.append(card)
            self.grid_layout.addWidget(card, i // cols, i % cols)

    def _save(self) -> None:
        saved = 0
        for card in self.cards:
            if card.is_changed():
                images.set_caption(card.name, card.caption_edit.text())
                saved += 1
        self.statusBar().showMessage(f"Saved {saved} caption(s).", 3000)

    def statusBar(self) -> QStatusBar:
        parent = self.window()
        sb = parent.findChild(QStatusBar)
        if sb is None:
            sb = QStatusBar(parent)
            layout = parent.layout()
            if layout is not None:
                layout.addWidget(sb)
        return sb


def run(dir_path: Path | None = None) -> None:
    app = QApplication(sys.argv)
    window = CaptionEditor(dir_path)
    window.show()
    sys.exit(app.exec())
