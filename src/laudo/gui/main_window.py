import json
import os
import sys
import traceback
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QByteArray, QObject, QRectF, QRunnable, QSize, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QColor, QFont, QIcon, QPainter, QPaintEvent, QPalette, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..reduce import DEFAULT_RESOLUTION, RESOLUTION_CHOICES

ASSETS_DIR = Path(__file__).parent / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
APP_ICON = ASSETS_DIR / "icon.png"


def set_app_icon(app: QApplication) -> None:
    if APP_ICON.is_file():
        app.setWindowIcon(QIcon(str(APP_ICON)))


class Spinner(QWidget):
    """Animated circular spinner used to indicate background processing."""

    def __init__(self, parent: QWidget | None = None, size: int = 22):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self.setFixedSize(size, size)
        self.hide()

    def start(self) -> None:
        self._angle = 0
        self.show()
        self._timer.start(16)

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _rotate(self) -> None:
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = max(2, self.width() // 8)
        rect = QRectF(width, width, self.width() - 2 * width, self.height() - 2 * width)
        color = self.palette().highlight().color()
        track = QColor(color)
        track.setAlpha(50)
        painter.setPen(QPen(track, width))
        painter.drawEllipse(rect)
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, -self._angle * 16, 100 * 16)


class _WorkerSignals(QObject):
    finished = Signal(str)
    failed = Signal(str, str)


class _Worker(QRunnable):
    def __init__(self, fn: Callable[[], str]):
        super().__init__()
        self.fn = fn
        self.signals = _WorkerSignals()

    def run(self) -> None:
        try:
            result = self.fn()
        except Exception as e:  # noqa: BLE001 - report every error to the user
            self.signals.failed.emit(str(e) or type(e).__name__, traceback.format_exc())
        else:
            self.signals.finished.emit(result)


class ReduceImagesDialog(QDialog):
    def __init__(self, folder: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Reduzir imagens")
        self.setMinimumWidth(560)
        self._folder = folder

        form = QFormLayout()
        self.source_edit = QLineEdit(str(folder / "fotos"))
        form.addRow("Origem:", self._path_row(self.source_edit, self._pick_source))
        self.dest_edit = QLineEdit(str(folder / "fotos"))
        form.addRow("Destino:", self._path_row(self.dest_edit, self._pick_dest))
        self.max_combo = QComboBox()
        for r in RESOLUTION_CHOICES:
            self.max_combo.addItem(f"{r}px", r)
        self.max_combo.setCurrentIndex(RESOLUTION_CHOICES.index(DEFAULT_RESOLUTION))
        form.addRow("Tamanho máximo:", self.max_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _path_row(self, edit: QLineEdit, pick: Callable[[], None]) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(edit, 1)
        folder_btn = QPushButton("Pasta…")
        folder_btn.clicked.connect(lambda: self._pick_dir(edit))
        h.addWidget(folder_btn)
        file_btn = QPushButton("Arquivo…")
        file_btn.clicked.connect(pick)
        h.addWidget(file_btn)
        return row

    def _pick_dir(self, edit: QLineEdit) -> None:
        path = QFileDialog.getExistingDirectory(self, "Selecionar pasta", edit.text() or str(self._folder))
        if path:
            edit.setText(path)

    def _pick_source(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar documento", str(self._folder), "Documentos (*.docx *.odt)"
        )
        if path:
            self.source_edit.setText(path)
            self.dest_edit.setText(path)

    def _pick_dest(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar documento como", self.dest_edit.text(), "Documentos (*.docx *.odt)"
        )
        if path:
            self.dest_edit.setText(path)

    def _accept(self) -> None:
        if not self.source_edit.text().strip() or not self.dest_edit.text().strip():
            QMessageBox.warning(self, "Reduzir imagens", "Informe origem e destino.")
            return
        self.accept()

    @property
    def source(self) -> Path:
        return Path(self.source_edit.text().strip())

    @property
    def dest(self) -> Path:
        return Path(self.dest_edit.text().strip())

    @property
    def max_resolution(self) -> int:
        return int(self.max_combo.currentData())


class MainWindow(QWidget):
    def __init__(self, dir_path: Path | None = None):
        super().__init__()
        self._pool = QThreadPool.globalInstance()
        self._busy = False
        self._workers: set[_Worker] = set()
        self._caption_editor: QWidget | None = None
        self._action_buttons: list[QPushButton] = []
        self._init_ui(dir_path or Path.cwd())

    # ----------------------------------------------------------------- UI
    def _init_ui(self, folder: Path) -> None:
        self.setWindowTitle("Laudo")
        self.setMinimumSize(760, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QLabel("Laudo")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Pasta:"))
        self.folder_edit = QLineEdit(str(folder.resolve()))
        folder_row.addWidget(self.folder_edit, 1)
        browse_btn = QPushButton("Selecionar…")
        browse_btn.setIcon(self._icon("folder"))
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(browse_btn)
        layout.addLayout(folder_row)

        grid = QGridLayout()
        grid.setSpacing(8)
        self.gen_btn = self._make_button("Gerar laudo", "gen — gera o docx/pdf", self._on_gen, "gen")
        self.pdf_check = QCheckBox("PDF")
        self.pdf_check.setToolTip("Gerar PDF em vez de DOCX")
        gen_box = QHBoxLayout()
        gen_box.addWidget(self.gen_btn, 1)
        gen_box.addWidget(self.pdf_check)
        grid.addLayout(gen_box, 0, 0)
        grid.addWidget(self._make_button("Legendas", "captions — editor de legendas", self._on_captions, "captions"), 0, 1)
        grid.addWidget(self._make_button("Variáveis", "vars — variáveis do context.txt", self._on_vars, "vars"), 0, 2)
        grid.addWidget(self._make_button("Contexto", "context — contexto completo do template", self._on_context, "context"), 1, 0)
        grid.addWidget(self._make_button("Reduzir imagens", "reduce-images", self._on_reduce, "reduce"), 1, 1)
        layout.addLayout(grid)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        mono = QFont("monospace")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.output.setFont(mono)
        layout.addWidget(self.output, 1)

        status_row = QHBoxLayout()
        self.spinner = Spinner(self)
        status_row.addWidget(self.spinner)
        self.status_label = QLabel("Pronto.")
        status_row.addWidget(self.status_label, 1)
        layout.addLayout(status_row)

    def _make_button(self, text: str, tooltip: str, slot: Callable[[], None], icon: str | None = None) -> QPushButton:
        btn = QPushButton(text)
        if icon:
            btn.setIcon(self._icon(icon))
            btn.setIconSize(QSize(18, 18))
        btn.setToolTip(tooltip)
        btn.setMinimumHeight(36)
        btn.clicked.connect(slot)
        self._action_buttons.append(btn)
        return btn

    def _icon(self, name: str) -> QIcon:
        """Load a stroke SVG from assets/icons, tinted with the palette's text color."""
        path = ICONS_DIR / f"{name}.svg"
        if not path.is_file():
            return QIcon()
        color = self.palette().color(QPalette.ColorRole.ButtonText).name()
        data = path.read_text(encoding="utf-8").replace("currentColor", color).encode("utf-8")
        renderer = QSvgRenderer(QByteArray(data))
        icon = QIcon()
        for size in (16, 18, 24, 32, 48):
            pixmap = QPixmap(QSize(size, size) * self.devicePixelRatioF())
            pixmap.setDevicePixelRatio(self.devicePixelRatioF())
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter, QRectF(0, 0, size, size))
            painter.end()
            icon.addPixmap(pixmap)
        return icon

    def _browse_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Selecionar pasta", self.folder_edit.text())
        if path:
            self.folder_edit.setText(path)

    # ------------------------------------------------------------ helpers
    def _folder(self) -> Path | None:
        folder = Path(self.folder_edit.text().strip()).expanduser()
        if not folder.is_dir():
            QMessageBox.critical(self, "Erro", f"Pasta não encontrada:\n{folder}")
            return None
        os.chdir(folder)
        return folder.resolve()

    def _set_busy(self, busy: bool, message: str) -> None:
        self._busy = busy
        for btn in self._action_buttons:
            btn.setEnabled(not busy)
        self.folder_edit.setEnabled(not busy)
        self.status_label.setText(message)
        if busy:
            self.spinner.start()
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        else:
            self.spinner.stop()
            QApplication.restoreOverrideCursor()

    def _run_task(self, label: str, fn: Callable[[], str]) -> None:
        if self._busy:
            return
        self._set_busy(True, f"{label}…")
        worker = _Worker(fn)
        worker.setAutoDelete(False)
        self._workers.add(worker)
        worker.signals.finished.connect(lambda result: self._on_done(label, result))
        worker.signals.failed.connect(lambda msg, tb: self._on_error(label, msg, tb))
        worker.signals.finished.connect(lambda _r: self._workers.discard(worker))
        worker.signals.failed.connect(lambda _m, _t: self._workers.discard(worker))
        self._pool.start(worker)

    def _on_done(self, label: str, result: str) -> None:
        self._set_busy(False, f"{label}: concluído.")
        self.output.setPlainText(result)

    def _on_error(self, label: str, message: str, tb: str) -> None:
        self._set_busy(False, f"{label}: erro.")
        self.output.setPlainText(tb)
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("Erro")
        box.setText(f"{label} falhou:")
        box.setInformativeText(message)
        box.setDetailedText(tb)
        box.exec()

    # ------------------------------------------------------------ actions
    def _on_gen(self) -> None:
        folder = self._folder()
        if folder is None:
            return
        pdf = self.pdf_check.isChecked()
        output = folder / ("laudo.pdf" if pdf else "laudo.docx")

        def task() -> str:
            from .. import convert

            result = convert(folder, output)
            return f"Gerado: {result}"

        self._run_task("Gerar laudo", task)

    def _on_captions(self) -> None:
        folder = self._folder()
        if folder is None:
            return
        try:
            from .caption_editor import CaptionEditor

            if self._caption_editor is not None:
                self._caption_editor.close()
            self._caption_editor = CaptionEditor(folder)
            self._caption_editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            self._caption_editor.destroyed.connect(self._clear_caption_editor)
            self._caption_editor.show()
        except Exception as e:  # noqa: BLE001
            self._on_error("Legendas", str(e) or type(e).__name__, traceback.format_exc())

    def _clear_caption_editor(self) -> None:
        self._caption_editor = None

    def _on_vars(self) -> None:
        folder = self._folder()
        if folder is None:
            return

        def task() -> str:
            from ..core import _parse_context_txt

            return json.dumps(_parse_context_txt(folder), indent=2, ensure_ascii=False)

        self._run_task("Variáveis", task)

    def _on_context(self) -> None:
        folder = self._folder()
        if folder is None:
            return

        def task() -> str:
            from ..core import _build_context, context_to_json

            return context_to_json(_build_context(folder).ctx)

        self._run_task("Contexto", task)

    def _on_reduce(self) -> None:
        folder = self._folder()
        if folder is None:
            return
        dlg = ReduceImagesDialog(folder, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        source = dlg.source if dlg.source.is_absolute() else folder / dlg.source
        dest = dlg.dest if dlg.dest.is_absolute() else folder / dlg.dest
        max_resolution = dlg.max_resolution

        def task() -> str:
            from ..reduce import reduce_images

            reduce_images(source, dest, max_resolution=max_resolution)
            return f"Imagens reduzidas ({max_resolution}px) salvas em {dest}"

        self._run_task("Reduzir imagens", task)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._caption_editor is not None:
            self._caption_editor.close()
        super().closeEvent(event)


def run_main(dir_path: Path | None = None) -> None:
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication(sys.argv)
    set_app_icon(app)
    window = MainWindow(dir_path)
    window.show()
    sys.exit(app.exec())
