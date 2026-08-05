from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
)

from our_day.models.guest_table import GuestTable


class TableDialog(QDialog):
    def __init__(self, parent=None, table: GuestTable | None = None) -> None:
        super().__init__(parent)
        self.table = table
        self.setWindowTitle("Asztal szerkesztése" if table else "Új asztal")
        self.resize(480, 330)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Például: 1. asztal vagy Család")
        self.capacity_input = QSpinBox()
        self.capacity_input.setRange(1, 100)
        self.capacity_input.setValue(8)
        self.notes_input = QTextEdit()

        form.addRow("Név *", self.name_input)
        form.addRow("Férőhely", self.capacity_input)
        form.addRow("Megjegyzés", self.notes_input)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        cancel = QPushButton("Mégse")
        cancel.setObjectName("secondaryButton")
        save = QPushButton("Mentés")
        save.setObjectName("primaryButton")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save)
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

        if table:
            self.name_input.setText(table.name)
            self.capacity_input.setValue(table.capacity)
            self.notes_input.setPlainText(table.notes)

    def _save(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Hiányzó név", "Az asztal neve kötelező.")
            return
        self.accept()

    def get_table(self) -> GuestTable:
        return GuestTable(
            id=self.table.id if self.table else None,
            name=self.name_input.text().strip(),
            capacity=self.capacity_input.value(),
            notes=self.notes_input.toPlainText().strip(),
        )


class SettingsPage(QWidget):
    data_changed = Signal()

    def __init__(self, table_repository) -> None:
        super().__init__()
        self.repository = table_repository

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(18)

        header = QHBoxLayout()
        text = QVBoxLayout()
        title = QLabel("Beállítások")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Esküvői asztalok és általános törzsadatok kezelése.")
        subtitle.setObjectName("pageSubtitle")
        text.addWidget(title)
        text.addWidget(subtitle)

        add = QPushButton("+ Új asztal")
        add.setObjectName("primaryButton")
        add.clicked.connect(self._create)

        header.addLayout(text)
        header.addStretch()
        header.addWidget(add)
        layout.addLayout(header)

        actions = QHBoxLayout()
        edit = QPushButton("Szerkesztés")
        edit.setObjectName("secondaryButton")
        edit.clicked.connect(self._edit)
        delete = QPushButton("Törlés")
        delete.setObjectName("dangerButton")
        delete.clicked.connect(self._delete)
        actions.addWidget(edit)
        actions.addWidget(delete)
        actions.addStretch()
        layout.addLayout(actions)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Asztal neve", "Férőhely", "Megjegyzés", "Azonosító"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setColumnHidden(3, True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._edit)
        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        tables = self.repository.list_all()
        self.table.setRowCount(len(tables))
        for row, table in enumerate(tables):
            for col, value in enumerate(
                (table.name, str(table.capacity), table.notes or "—", str(table.id))
            ):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def _selected_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Nincs kiválasztás", "Válassz ki egy asztalt.")
            return None
        return int(self.table.item(rows[0].row(), 3).text())

    def _create(self) -> None:
        dialog = TableDialog(self)
        if dialog.exec():
            try:
                self.repository.create(dialog.get_table())
                self.data_changed.emit()
            except Exception:
                QMessageBox.warning(self, "Hiba", "Már létezik ilyen nevű asztal.")

    def _edit(self) -> None:
        table_id = self._selected_id()
        if table_id is None:
            return
        table = self.repository.get_by_id(table_id)
        dialog = TableDialog(self, table)
        if dialog.exec():
            try:
                self.repository.update(dialog.get_table())
                self.data_changed.emit()
            except Exception:
                QMessageBox.warning(self, "Hiba", "Már létezik ilyen nevű asztal.")

    def _delete(self) -> None:
        table_id = self._selected_id()
        if table_id is None:
            return
        answer = QMessageBox.question(
            self,
            "Asztal törlése",
            "A hozzárendelt vendégekről is lekerül az asztal. Folytatod?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.repository.delete(table_id)
            self.data_changed.emit()
