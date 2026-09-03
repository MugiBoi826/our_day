from datetime import date

from PySide6.QtCore import QDate, QObject, QSettings, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QCheckBox,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
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
from our_day.models.wedding import Wedding
from our_day.services.database_service import DatabaseService
from our_day.services.supabase_sync_service import (
    SupabaseSyncError,
    SupabaseSyncService,
)


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
        self.shape_input = QComboBox()
        self.shape_input.addItems(
            (
                "Kerek",
                "Ovális",
                "Téglalap",
                "Hosszú asztal",
                "U alakú",
                "Főasztal",
            )
        )
        self.notes_input = QTextEdit()

        form.addRow("Név *", self.name_input)
        form.addRow("Férőhely", self.capacity_input)
        form.addRow("Forma", self.shape_input)
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
            self.shape_input.setCurrentText(table.shape)

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
            position_x=(self.table.position_x if self.table else 40),
            position_y=(self.table.position_y if self.table else 40),
            shape=self.shape_input.currentText(),
        )


class CloudSyncWorker(QObject):
    finished = Signal(str, dict)
    failed = Signal(str, str)

    def __init__(self, service: SupabaseSyncService, operation: str) -> None:
        super().__init__()
        self.service = service
        self.operation = operation

    @Slot()
    def run(self) -> None:
        try:
            if self.operation == "upload":
                result = self.service.upload_cache()
            else:
                result = self.service.download_to_cache()
        except Exception as error:
            self.failed.emit(self.operation, str(error))
            return
        self.finished.emit(self.operation, result)


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
        wedding_repository,
    ) -> None:
        super().__init__()
        self.table_repository = table_repository
        self.preference_repository = preference_repository
        self.wedding_repository = wedding_repository
        self.cloud_sync = SupabaseSyncService()
        self._cloud_busy = False
        self._pending_upload = False
        self._sync_thread: QThread | None = None
        self._sync_worker: CloudSyncWorker | None = None
        self._upload_timer = QTimer(self)
        self._upload_timer.setSingleShot(True)
        self._upload_timer.setInterval(1500)
        self._upload_timer.timeout.connect(lambda: self._start_cloud_sync("upload"))
        self._download_timer = QTimer(self)
        self._download_timer.setInterval(60_000)
        self._download_timer.timeout.connect(lambda: self._start_cloud_sync("download"))

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
        tabs.addTab(self._create_wedding_tab(), "Esküvő")
        tabs.addTab(self._create_tables_tab(), "Asztalok")
        tabs.addTab(
            self._create_preferences_tab(),
            "Étrend és allergiák",
        )
        tabs.addTab(
            self._create_database_tab(),
            "Adatbázis",
        )
        tabs.addTab(self._create_cloud_tab(), "Felhőszinkron")

        layout.addWidget(tabs, 1)

    def _create_cloud_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        title = QLabel("Supabase felhőszinkron")
        title.setObjectName("sectionTitle")
        description = QLabel(
            "A Supabase a központi adatforrás, az ezen a gépen lévő SQLite "
            "adatbázis pedig offline gyorsítótár. Bejelentkezés után a változások "
            "automatikusan szinkronizálódnak; a jelszót az alkalmazás nem menti el."
        )
        description.setWordWrap(True)
        description.setObjectName("pageSubtitle")

        settings = QSettings("Our Day", "Our Day")
        self.cloud_email_input = QLineEdit()
        self.cloud_email_input.setText(settings.value("cloud/email", ""))
        self.cloud_email_input.setPlaceholderText("Supabase-fiók e-mail-címe")
        self.cloud_password_input = QLineEdit()
        self.cloud_password_input.setEchoMode(QLineEdit.Password)
        self.cloud_password_input.setPlaceholderText("Jelszó")

        form = QFormLayout()
        form.addRow("E-mail", self.cloud_email_input)
        form.addRow("Jelszó", self.cloud_password_input)

        self.cloud_login_button = QPushButton("Bejelentkezés")
        self.cloud_login_button.setObjectName("primaryButton")
        self.cloud_login_button.clicked.connect(self._cloud_login)

        self.cloud_download_button = QPushButton("Felhőadatok letöltése")
        self.cloud_download_button.setObjectName("primaryButton")
        self.cloud_download_button.setEnabled(False)
        self.cloud_download_button.clicked.connect(self._cloud_download)

        self.cloud_upload_button = QPushButton("Offline módosítások feltöltése")
        self.cloud_upload_button.setObjectName("secondaryButton")
        self.cloud_upload_button.setEnabled(False)
        self.cloud_upload_button.clicked.connect(self._cloud_upload)

        buttons = QHBoxLayout()
        buttons.addWidget(self.cloud_login_button)
        buttons.addWidget(self.cloud_download_button)
        buttons.addWidget(self.cloud_upload_button)
        buttons.addStretch()

        self.cloud_status = QLabel("Nincs bejelentkezve.")
        self.cloud_status.setWordWrap(True)

        warning = QLabel(
            "A letöltés a helyi gyorsítótárat a felhő aktuális állapotára cseréli. "
            "Ha offline dolgoztál, előbb töltsd fel a módosításokat."
        )
        warning.setWordWrap(True)
        warning.setObjectName("pageSubtitle")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.cloud_status)
        layout.addWidget(warning)
        layout.addStretch()
        return page

    def _cloud_login(self) -> None:
        email = self.cloud_email_input.text().strip()
        password = self.cloud_password_input.text()
        if not email or not password:
            QMessageBox.warning(self, "Hiányzó adatok", "Add meg az e-mail-címet és a jelszót.")
            return
        try:
            self.cloud_sync.sign_in(email, password)
        except SupabaseSyncError as error:
            QMessageBox.critical(self, "Bejelentkezési hiba", str(error))
            return
        QSettings("Our Day", "Our Day").setValue("cloud/email", email)
        self.cloud_password_input.clear()
        self.cloud_download_button.setEnabled(True)
        self.cloud_upload_button.setEnabled(True)
        self.cloud_status.setText("Bejelentkezve. Az automatikus szinkron elindult…")
        self._download_timer.start()
        self._start_cloud_sync("download")

    def schedule_auto_upload(self) -> None:
        if not self.cloud_sync.is_signed_in:
            return
        self._pending_upload = True
        self._upload_timer.start()

    def _start_cloud_sync(self, operation: str) -> None:
        if not self.cloud_sync.is_signed_in:
            return
        if operation == "download" and (
            self._pending_upload or self._upload_timer.isActive()
        ):
            return
        if self._cloud_busy:
            if operation == "upload":
                self._pending_upload = True
            return
        self._cloud_busy = True
        if operation == "upload":
            self._pending_upload = False
        self.cloud_status.setText(
            "Helyi változások feltöltése…" if operation == "upload"
            else "Felhőadatok frissítése…"
        )
        thread = QThread(self)
        worker = CloudSyncWorker(self.cloud_sync, operation)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._cloud_sync_finished)
        worker.failed.connect(self._cloud_sync_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._cloud_thread_finished)
        self._sync_thread = thread
        self._sync_worker = worker
        thread.start()

    @Slot()
    def _cloud_thread_finished(self) -> None:
        self._cloud_busy = False
        self._sync_thread = None
        self._sync_worker = None
        if self._pending_upload:
            self._upload_timer.start(250)

    @Slot(str, dict)
    def _cloud_sync_finished(self, operation: str, counts: dict) -> None:
        if operation == "upload":
            self.cloud_status.setText("Minden helyi változás a felhőben van.")
        else:
            self.cloud_status.setText(
                f"Naprakész: {counts['guests']} vendég, {counts['tasks']} teendő, "
                f"{counts['entries']} szolgáltatás."
            )
            self.data_changed.emit()

    @Slot(str, str)
    def _cloud_sync_failed(self, operation: str, error: str) -> None:
        self.cloud_status.setText(
            "A háttérszinkron most nem sikerült; az offline adatok megmaradtak. "
            f"Részletek: {error}"
        )

    def _cloud_download(self) -> None:
        if QMessageBox.question(
            self, "Helyi gyorsítótár frissítése",
            "A helyi adatokat lecseréljük a Supabase aktuális adataira. Folytatod?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self._start_cloud_sync("download")

    def _cloud_upload(self) -> None:
        self._start_cloud_sync("upload")

    def _create_wedding_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        title = QLabel("Esküvő alapadatai")
        title.setObjectName("sectionTitle")

        description = QLabel(
            "Ezek az adatok jelennek meg az Áttekintés oldalon, és "
            "a költségkerethez viszonyítva számoljuk a szolgáltatásokat."
        )
        description.setWordWrap(True)
        description.setObjectName("pageSubtitle")

        form = QFormLayout()
        form.setSpacing(14)

        self.bride_name_input = QLineEdit()
        self.bride_name_input.setPlaceholderText("Például: Anna")

        self.groom_name_input = QLineEdit()
        self.groom_name_input.setPlaceholderText("Például: Péter")

        self.wedding_date_enabled = QCheckBox("Esküvő dátuma megadva")
        self.wedding_date_input = QDateEdit(QDate.currentDate().addYears(1))
        self.wedding_date_input.setCalendarPopup(True)
        self.wedding_date_input.setDisplayFormat("yyyy.MM.dd.")
        self.wedding_date_input.setEnabled(False)
        self.wedding_date_enabled.toggled.connect(
            self.wedding_date_input.setEnabled
        )

        date_container = QWidget()
        date_layout = QHBoxLayout(date_container)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.addWidget(self.wedding_date_enabled)
        date_layout.addWidget(self.wedding_date_input, 1)

        self.venue_name_input = QLineEdit()
        self.venue_name_input.setPlaceholderText("Helyszín neve")

        self.venue_address_input = QLineEdit()
        self.venue_address_input.setPlaceholderText("Helyszín címe")

        self.budget_input = QDoubleSpinBox()
        self.budget_input.setRange(0, 999_999_999)
        self.budget_input.setDecimals(0)
        self.budget_input.setSingleStep(100_000)
        self.budget_input.setSuffix(" Ft")
        self.budget_input.setGroupSeparatorShown(True)

        self.wedding_notes_input = QTextEdit()
        self.wedding_notes_input.setPlaceholderText(
            "Fontos közös megjegyzések az esküvőről"
        )
        self.wedding_notes_input.setMinimumHeight(110)

        form.addRow("Menyasszony neve", self.bride_name_input)
        form.addRow("Vőlegény neve", self.groom_name_input)
        form.addRow("Esküvő dátuma", date_container)
        form.addRow("Helyszín neve", self.venue_name_input)
        form.addRow("Helyszín címe", self.venue_address_input)
        form.addRow("Teljes költségkeret", self.budget_input)
        form.addRow("Megjegyzés", self.wedding_notes_input)

        save_button = QPushButton("Esküvő adatainak mentése")
        save_button.setObjectName("primaryButton")
        save_button.setMinimumHeight(44)
        save_button.clicked.connect(self._save_wedding)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(form)
        layout.addWidget(save_button)
        layout.addStretch()
        return page

    def _save_wedding(self) -> None:
        selected_date = None
        if self.wedding_date_enabled.isChecked():
            value = self.wedding_date_input.date()
            selected_date = date(value.year(), value.month(), value.day())

        wedding = Wedding(
            bride_name=self.bride_name_input.text().strip(),
            groom_name=self.groom_name_input.text().strip(),
            wedding_date=selected_date,
            venue_name=self.venue_name_input.text().strip(),
            venue_address=self.venue_address_input.text().strip(),
            budget_amount=self.budget_input.value(),
            notes=self.wedding_notes_input.toPlainText().strip(),
        )

        try:
            self.wedding_repository.save_active(wedding)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Mentési hiba",
                f"Az esküvő adatainak mentése nem sikerült.\n\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Adatok mentve",
            "Az esküvő alapadatai sikeresen elmentésre kerültek.",
        )
        self.data_changed.emit()

    def _load_wedding(self) -> None:
        wedding = self.wedding_repository.get_active()
        if wedding is None:
            self.bride_name_input.clear()
            self.groom_name_input.clear()
            self.wedding_date_enabled.setChecked(False)
            self.venue_name_input.clear()
            self.venue_address_input.clear()
            self.budget_input.setValue(0)
            self.wedding_notes_input.clear()
            return

        self.bride_name_input.setText(wedding.bride_name)
        self.groom_name_input.setText(wedding.groom_name)
        self.venue_name_input.setText(wedding.venue_name)
        self.venue_address_input.setText(wedding.venue_address)
        self.budget_input.setValue(wedding.budget_amount)
        self.wedding_notes_input.setPlainText(wedding.notes)

        if wedding.wedding_date:
            self.wedding_date_enabled.setChecked(True)
            self.wedding_date_input.setDate(
                QDate(
                    wedding.wedding_date.year,
                    wedding.wedding_date.month,
                    wedding.wedding_date.day,
                )
            )
        else:
            self.wedding_date_enabled.setChecked(False)

    def _create_database_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        title = QLabel("Adatbázis-kezelés")
        title.setObjectName("sectionTitle")

        description = QLabel(
            "Itt exportálhatod vagy importálhatod a teljes adatbázist, "
            "kiürítheted az alkalmazást, illetve visszatöltheted a "
            "beépített demóadatokat."
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

        export_button = QPushButton("Adatbázis exportálása")
        export_button.setObjectName("primaryButton")
        export_button.setMinimumHeight(44)
        export_button.clicked.connect(self._export_database)

        import_button = QPushButton("Adatbázis importálása")
        import_button.setObjectName("secondaryButton")
        import_button.setMinimumHeight(44)
        import_button.clicked.connect(self._import_database)

        clear_button = QPushButton("Adatbázis teljes ürítése")
        clear_button.setObjectName("dangerButton")
        clear_button.setMinimumHeight(44)
        clear_button.clicked.connect(self._clear_database)

        demo_button = QPushButton("Demóadatok betöltése")
        demo_button.setObjectName("secondaryButton")
        demo_button.setMinimumHeight(44)
        demo_button.clicked.connect(self._load_demo_database)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(export_button)
        layout.addWidget(import_button)
        layout.addSpacing(8)
        layout.addWidget(warning)
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
        self._load_wedding()
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

    def _export_database(self) -> None:
        default_name = (
            f"our_day_backup_{date.today().isoformat()}.db"
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Our Day adatbázis exportálása",
            default_name,
            "SQLite adatbázis (*.db *.sqlite *.sqlite3)",
        )

        if not file_path:
            return

        try:
            exported_path = DatabaseService.export_database(file_path)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Exportálási hiba",
                f"Az adatbázis exportálása nem sikerült.\n\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Export elkészült",
            f"A teljes adatbázis sikeresen exportálva lett.\n\n{exported_path}",
        )

    def _import_database(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Our Day adatbázis importálása",
            "",
            "SQLite adatbázis (*.db *.sqlite *.sqlite3);;Minden fájl (*)",
        )

        if not file_path:
            return

        answer = QMessageBox.warning(
            self,
            "Adatbázis importálása",
            (
                "Az import felülírja az alkalmazás jelenlegi teljes "
                "adatbázisát.\n\n"
                "A művelet előtt automatikus biztonsági mentés készül.\n\n"
                "Biztosan folytatod?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            database_path, backup_path = DatabaseService.import_database(
                file_path
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Importálási hiba",
                f"Az adatbázis importálása nem sikerült.\n\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Import sikeres",
            (
                "Az adatbázis sikeresen importálva lett.\n\n"
                f"Aktív adatbázis: {database_path}\n\n"
                f"Automatikus mentés: {backup_path}"
            ),
        )
        self.data_changed.emit()

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
