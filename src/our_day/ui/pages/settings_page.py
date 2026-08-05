from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from our_day.models.guest_table import GuestTable
from our_day.services.database_service import DatabaseService


class TableDialog(QDialog):
    def __init__(self, parent=None, table: GuestTable | None = None) -> None:
        super().__init__(parent)
        self.table = table
        self.setWindowTitle("Asztal szerkesztése" if table else "Új asztal")
        self.resize(480, 330)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
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
            QMessageBox.warning(
                self,
                "Hiányzó név",
                "Az asztal neve kötelező.",
            )
            return
        self.accept()

    def get_table(self) -> GuestTable:
        return GuestTable(
            id=self.table.id if self.table else None,
            name=self.name_input.text().strip(),
            capacity=self.capacity_input.value(),
            notes=self.notes_input.toPlainText().strip(),
        )


class PreferenceDialog(QDialog):
    def __init__(self, parent=None, preference: dict | None = None) -> None:
        super().__init__(parent)
        self.preference = preference
        self.setWindowTitle(
            "Étrendi adat szerkesztése"
            if preference
            else "Új étrendi adat"
        )
        self.resize(420, 220)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.category_input = QComboBox()
        self.category_input.addItems(
            ("Étrend", "Érzékenység", "Allergia")
        )

        self.name_input = QLineEdit()

        form.addRow("Kategória", self.category_input)
        form.addRow("Megnevezés *", self.name_input)
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

        if preference:
            self.category_input.setCurrentText(
                preference["category"]
            )
            self.name_input.setText(preference["name"])

    def _save(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                "Hiányzó megnevezés",
                "A megnevezés kötelező.",
            )
            return
        self.accept()


class SettingsPage(QWidget):
    data_changed = Signal()

    def __init__(
        self,
        table_repository,
        preference_repository,
    ) -> None:
        super().__init__()
        self.table_repository = table_repository
        self.preference_repository = preference_repository

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(18)

        title = QLabel("Beállítások")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Asztalok, étrendek, érzékenységek és allergiák kezelése."
        )
        subtitle.setObjectName("pageSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        tabs = QTabWidget()
        tabs.addTab(self._create_tables_tab(), "Asztalok")
        tabs.addTab(
            self._create_preferences_tab(),
            "Étrend és allergiák",
        )
        tabs.addTab(
            self._create_database_tab(),
            "Adatbázis",
        )

        layout.addWidget(tabs, 1)

    def _create_database_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        title = QLabel("Adatbázis-kezelés")
        title.setObjectName("sectionTitle")

        description = QLabel(
            "Itt teljesen kiürítheted az alkalmazás adatbázisát, "
            "vagy visszatöltheted a beépített demóadatokat."
        )
        description.setWordWrap(True)
        description.setObjectName("pageSubtitle")

        warning = QLabel(
            "Figyelem: az adatbázis ürítése minden szolgáltatást, "
            "feladatot, vendéget, csoportot, asztalt és beállítást töröl."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet(
            """
            QLabel {
                background: #FFF0F0;
                color: #9B2525;
                border: 1px solid #E8B6B6;
                border-radius: 10px;
                padding: 14px;
                font-weight: 600;
            }
            """
        )

        clear_button = QPushButton("Adatbázis teljes ürítése")
        clear_button.setObjectName("dangerButton")
        clear_button.setMinimumHeight(44)
        clear_button.clicked.connect(self._clear_database)

        demo_button = QPushButton("Demóadatok betöltése")
        demo_button.setObjectName("primaryButton")
        demo_button.setMinimumHeight(44)
        demo_button.clicked.connect(self._load_demo_database)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(warning)
        layout.addSpacing(8)
        layout.addWidget(clear_button)
        layout.addWidget(demo_button)
        layout.addStretch()

        return page

    def _create_tables_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        actions = QHBoxLayout()

        add = QPushButton("+ Új asztal")
        add.setObjectName("primaryButton")
        add.clicked.connect(self._create_table)

        edit = QPushButton("Szerkesztés")
        edit.setObjectName("secondaryButton")
        edit.clicked.connect(self._edit_table)

        delete = QPushButton("Törlés")
        delete.setObjectName("dangerButton")
        delete.clicked.connect(self._delete_table)

        actions.addWidget(add)
        actions.addWidget(edit)
        actions.addWidget(delete)
        actions.addStretch()
        layout.addLayout(actions)

        self.tables_table = QTableWidget(0, 4)
        self.tables_table.setHorizontalHeaderLabels(
            ["Asztal neve", "Férőhely", "Megjegyzés", "Azonosító"]
        )
        self.tables_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.tables_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.tables_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.tables_table.setColumnHidden(3, True)
        self.tables_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.Stretch,
        )
        self.tables_table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.Stretch,
        )
        self.tables_table.doubleClicked.connect(self._edit_table)

        layout.addWidget(self.tables_table, 1)
        return page

    def _create_preferences_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        actions = QHBoxLayout()

        add = QPushButton("+ Új elem")
        add.setObjectName("primaryButton")
        add.clicked.connect(self._create_preference)

        edit = QPushButton("Szerkesztés")
        edit.setObjectName("secondaryButton")
        edit.clicked.connect(self._edit_preference)

        delete = QPushButton("Törlés")
        delete.setObjectName("dangerButton")
        delete.clicked.connect(self._delete_preference)

        actions.addWidget(add)
        actions.addWidget(edit)
        actions.addWidget(delete)
        actions.addStretch()
        layout.addLayout(actions)

        self.preferences_table = QTableWidget(0, 3)
        self.preferences_table.setHorizontalHeaderLabels(
            ["Kategória", "Megnevezés", "Azonosító"]
        )
        self.preferences_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.preferences_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.preferences_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.preferences_table.setColumnHidden(2, True)
        self.preferences_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )
        self.preferences_table.doubleClicked.connect(
            self._edit_preference
        )

        layout.addWidget(self.preferences_table, 1)
        return page

    def refresh(self) -> None:
        tables = self.table_repository.list_all()
        self.tables_table.setRowCount(len(tables))

        for row, table in enumerate(tables):
            values = (
                table.name,
                str(table.capacity),
                table.notes or "—",
                str(table.id),
            )
            for column, value in enumerate(values):
                self.tables_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

        preferences = self.preference_repository.list_all()
        self.preferences_table.setRowCount(len(preferences))

        for row, preference in enumerate(preferences):
            values = (
                preference["category"],
                preference["name"],
                str(preference["id"]),
            )
            for column, value in enumerate(values):
                self.preferences_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

    def _selected_table_id(self) -> int | None:
        rows = self.tables_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(
                self,
                "Nincs kiválasztás",
                "Válassz ki egy asztalt.",
            )
            return None
        return int(self.tables_table.item(rows[0].row(), 3).text())

    def _selected_preference(self) -> dict | None:
        rows = self.preferences_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(
                self,
                "Nincs kiválasztás",
                "Válassz ki egy elemet.",
            )
            return None

        row = rows[0].row()
        return {
            "id": int(self.preferences_table.item(row, 2).text()),
            "category": self.preferences_table.item(row, 0).text(),
            "name": self.preferences_table.item(row, 1).text(),
        }

    def _clear_database(self) -> None:
        first_answer = QMessageBox.warning(
            self,
            "Adatbázis teljes ürítése",
            (
                "Ez a művelet minden jelenlegi adatot véglegesen töröl.\n\n"
                "Biztosan folytatod?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if first_answer != QMessageBox.Yes:
            return

        second_answer = QMessageBox.question(
            self,
            "Végső megerősítés",
            (
                "Az adatbázis kiürítése nem vonható vissza.\n"
                "Szeretnéd végrehajtani?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if second_answer != QMessageBox.Yes:
            return

        try:
            database_path = DatabaseService.clear_database()
        except Exception as error:
            QMessageBox.critical(
                self,
                "Adatbázishiba",
                f"Az adatbázis ürítése nem sikerült.\n\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Adatbázis kiürítve",
            (
                "Az adatbázis sikeresen kiürült.\n\n"
                f"Fájl: {database_path}"
            ),
        )
        self.data_changed.emit()

    def _load_demo_database(self) -> None:
        answer = QMessageBox.question(
            self,
            "Demóadatok betöltése",
            (
                "A demóadatok betöltése felülírja a jelenlegi adatbázist.\n\n"
                "Biztosan folytatod?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            database_path = DatabaseService.load_demo_database()
        except Exception as error:
            QMessageBox.critical(
                self,
                "Adatbázishiba",
                f"A demóadatok betöltése nem sikerült.\n\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Demóadatok betöltve",
            (
                "A demóadatok sikeresen betöltődtek.\n\n"
                f"Fájl: {database_path}"
            ),
        )
        self.data_changed.emit()

    def _create_table(self) -> None:
        dialog = TableDialog(self)
        if dialog.exec():
            try:
                self.table_repository.create(dialog.get_table())
                self.data_changed.emit()
            except Exception:
                QMessageBox.warning(
                    self,
                    "Hiba",
                    "Már létezik ilyen nevű asztal.",
                )

    def _edit_table(self) -> None:
        table_id = self._selected_table_id()
        if table_id is None:
            return

        table = self.table_repository.get_by_id(table_id)
        dialog = TableDialog(self, table)

        if dialog.exec():
            try:
                self.table_repository.update(dialog.get_table())
                self.data_changed.emit()
            except Exception:
                QMessageBox.warning(
                    self,
                    "Hiba",
                    "Már létezik ilyen nevű asztal.",
                )

    def _delete_table(self) -> None:
        table_id = self._selected_table_id()
        if table_id is None:
            return

        if QMessageBox.question(
            self,
            "Asztal törlése",
            "A hozzárendelt vendégekről lekerül az asztal. Folytatod?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) == QMessageBox.Yes:
            self.table_repository.delete(table_id)
            self.data_changed.emit()

    def _create_preference(self) -> None:
        dialog = PreferenceDialog(self)
        if dialog.exec():
            try:
                self.preference_repository.create(
                    dialog.category_input.currentText(),
                    dialog.name_input.text().strip(),
                )
                self.data_changed.emit()
            except Exception:
                QMessageBox.warning(
                    self,
                    "Hiba",
                    "Ez az elem már létezik ebben a kategóriában.",
                )

    def _edit_preference(self) -> None:
        preference = self._selected_preference()
        if preference is None:
            return

        dialog = PreferenceDialog(self, preference)
        if dialog.exec():
            try:
                self.preference_repository.update(
                    preference["id"],
                    dialog.category_input.currentText(),
                    dialog.name_input.text().strip(),
                )
                self.data_changed.emit()
            except Exception:
                QMessageBox.warning(
                    self,
                    "Hiba",
                    "Ez az elem már létezik ebben a kategóriában.",
                )

    def _delete_preference(self) -> None:
        preference = self._selected_preference()
        if preference is None:
            return

        if QMessageBox.question(
            self,
            "Elem törlése",
            "A vendégekről is lekerül ez a beállítás. Folytatod?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) == QMessageBox.Yes:
            self.preference_repository.delete(preference["id"])
            self.data_changed.emit()
