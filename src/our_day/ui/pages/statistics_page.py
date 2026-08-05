from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from our_day.services.guest_export_service import GuestExportService
from our_day.ui.widgets.statistic_card import StatisticCard


class StatisticsPage(QWidget):
    def __init__(
        self,
        guest_repository,
        group_repository,
    ) -> None:
        super().__init__()

        self.guest_repository = guest_repository
        self.group_repository = group_repository

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(34, 28, 34, 30)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()

        header_text = QVBoxLayout()
        header_text.setSpacing(4)

        title = QLabel("Vendégstatisztikák")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "RSVP, létszám, étkezési igények és ültetés egy helyen."
        )
        subtitle.setObjectName("pageSubtitle")

        export_button = QPushButton("Excel export")
        export_button.setObjectName("primaryButton")
        export_button.clicked.connect(self._export_excel)

        header_text.addWidget(title)
        header_text.addWidget(subtitle)

        header_layout.addLayout(header_text)
        header_layout.addStretch()
        header_layout.addWidget(export_button)

        layout.addLayout(header_layout)

        self._build_headcount_section(layout)
        self._build_dining_section(layout)
        self._build_seating_section(layout)
        self._build_preference_section(layout)
        self._build_rsvp_section(layout)

        scroll.setWidget(content)
        root_layout.addWidget(scroll)

    def _build_headcount_section(self, layout: QVBoxLayout) -> None:
        section = self._section_frame(
            "Létszám és válaszadási állapot"
        )
        section_layout = section.layout()

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        self.total_card = StatisticCard(
            "Tervezett létszám",
            "0",
            "accent",
        )
        self.confirmed_card = StatisticCard(
            "Részt vesz",
            "0",
            "success",
        )
        self.waiting_card = StatisticCard(
            "Válaszra vár",
            "0",
            "warning",
        )
        self.declined_card = StatisticCard(
            "Nem vesz részt",
            "0",
            "danger",
        )
        self.adults_card = StatisticCard(
            "Felnőttek",
            "0 / 0",
        )
        self.children_card = StatisticCard(
            "Gyermekek",
            "0 / 0",
        )

        cards = (
            self.total_card,
            self.confirmed_card,
            self.waiting_card,
            self.declined_card,
            self.adults_card,
            self.children_card,
        )

        for index, card in enumerate(cards):
            grid.addWidget(
                card,
                index // 3,
                index % 3,
            )

        self.response_progress = QProgressBar()
        self.response_progress.setRange(0, 100)
        self.response_progress.setTextVisible(True)
        self.response_progress.setMinimumHeight(24)

        self.response_progress_label = QLabel()
        self.response_progress_label.setObjectName("pageSubtitle")

        section_layout.addLayout(grid)
        section_layout.addWidget(self.response_progress_label)
        section_layout.addWidget(self.response_progress)

        layout.addWidget(section)

    def _build_dining_section(self, layout: QVBoxLayout) -> None:
        section = self._section_frame("Étkezés")
        section_layout = section.layout()

        cards_layout = QHBoxLayout()

        self.dinner_card = StatisticCard(
            "Vacsorázik",
            "0",
            "success",
        )
        self.no_dinner_card = StatisticCard(
            "Nem vacsorázik",
            "0",
            "danger",
        )
        self.special_diet_card = StatisticCard(
            "Speciális igény",
            "0",
            "warning",
        )
        self.contactable_card = StatisticCard(
            "Van elérhetősége",
            "0",
            "accent",
        )

        for card in (
            self.dinner_card,
            self.no_dinner_card,
            self.special_diet_card,
            self.contactable_card,
        ):
            cards_layout.addWidget(card)

        section_layout.addLayout(cards_layout)
        layout.addWidget(section)

    def _build_seating_section(self, layout: QVBoxLayout) -> None:
        section = self._section_frame("Ültetés és asztalok")
        section_layout = section.layout()

        top_layout = QHBoxLayout()

        self.unassigned_card = StatisticCard(
            "Nincs asztalhoz rendelve",
            "0",
            "danger",
        )
        self.capacity_card = StatisticCard(
            "Összes férőhely",
            "0",
            "accent",
        )
        self.assigned_card = StatisticCard(
            "Asztalhoz rendelve",
            "0",
            "success",
        )
        self.overbooked_card = StatisticCard(
            "Túlfoglalt asztal",
            "0",
            "danger",
        )

        for card in (
            self.unassigned_card,
            self.capacity_card,
            self.assigned_card,
            self.overbooked_card,
        ):
            top_layout.addWidget(card)

        self.tables_table = QTableWidget(0, 5)
        self.tables_table.setMinimumHeight(260)
        self.tables_table.setHorizontalHeaderLabels(
            (
                "Asztal",
                "Férőhely",
                "Hozzárendelve",
                "Szabad hely",
                "Állapot",
            )
        )
        self.tables_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.tables_table.setSelectionMode(
            QTableWidget.NoSelection
        )
        self.tables_table.verticalHeader().setVisible(False)

        header = self.tables_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.tables_table.setColumnWidth(1, 110)
        self.tables_table.setColumnWidth(2, 135)
        self.tables_table.setColumnWidth(3, 110)
        self.tables_table.setColumnWidth(4, 150)
        self.tables_table.setHorizontalScrollMode(
            QTableWidget.ScrollPerPixel
        )

        section_layout.addLayout(top_layout)
        section_layout.addWidget(self.tables_table)

        layout.addWidget(section)

    def _build_preference_section(self, layout: QVBoxLayout) -> None:
        section = self._section_frame(
            "Étrend, érzékenység és allergia"
        )
        section_layout = section.layout()

        self.preferences_table = QTableWidget(0, 3)
        self.preferences_table.setMinimumHeight(300)
        self.preferences_table.setHorizontalHeaderLabels(
            (
                "Kategória",
                "Megnevezés",
                "Érintett vendégek",
            )
        )
        self.preferences_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.preferences_table.setSelectionMode(
            QTableWidget.NoSelection
        )
        self.preferences_table.verticalHeader().setVisible(False)
        self.preferences_table.verticalHeader().setDefaultSectionSize(36)

        header = self.preferences_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.preferences_table.setColumnWidth(0, 165)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.preferences_table.setColumnWidth(2, 165)
        self.preferences_table.setHorizontalScrollMode(
            QTableWidget.ScrollPerPixel
        )

        section_layout.addWidget(self.preferences_table)
        layout.addWidget(section)

    def _build_rsvp_section(self, layout: QVBoxLayout) -> None:
        section = self._section_frame(
            "Meghívási csoportok és RSVP"
        )
        section_layout = section.layout()

        self.rsvp_table = QTableWidget(0, 8)
        self.rsvp_table.setMinimumHeight(380)
        self.rsvp_table.setHorizontalHeaderLabels(
            (
                "Csoport",
                "Típus",
                "Határidő",
                "Összesen",
                "Részt vesz",
                "Várakozik",
                "Nem jön",
                "Állapot",
            )
        )
        self.rsvp_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.rsvp_table.setSelectionMode(
            QTableWidget.NoSelection
        )
        self.rsvp_table.verticalHeader().setVisible(False)
        self.rsvp_table.verticalHeader().setDefaultSectionSize(38)

        header = self.rsvp_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.rsvp_table.setColumnWidth(1, 150)
        self.rsvp_table.setColumnWidth(2, 125)
        self.rsvp_table.setColumnWidth(3, 95)
        self.rsvp_table.setColumnWidth(4, 105)
        self.rsvp_table.setColumnWidth(5, 105)
        self.rsvp_table.setColumnWidth(6, 95)
        self.rsvp_table.setColumnWidth(7, 150)
        self.rsvp_table.setMinimumWidth(900)
        self.rsvp_table.setHorizontalScrollMode(
            QTableWidget.ScrollPerPixel
        )

        section_layout.addWidget(self.rsvp_table)
        layout.addWidget(section)

    @staticmethod
    def _section_frame(title_text: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("contentCard")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel(title_text)
        title.setObjectName("sectionTitle")

        layout.addWidget(title)
        return frame

    def _export_excel(self) -> None:
        default_name = (
            f"our_day_statisztika_"
            f"{date.today().isoformat()}.xlsx"
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Vendégstatisztika Excel export",
            default_name,
            "Excel munkafüzet (*.xlsx)",
        )

        if not file_path:
            return

        try:
            GuestExportService.export(file_path)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Exportálási hiba",
                (
                    "Az Excel export nem sikerült.\n\n"
                    f"{error}"
                ),
            )
            return

        QMessageBox.information(
            self,
            "Export elkészült",
            f"Az Excel export sikeresen elkészült:\n{file_path}",
        )

    def refresh(self) -> None:
        summary = self.guest_repository.get_summary()

        self.total_card.set_value(str(summary["planned"]))
        self.confirmed_card.set_value(
            str(summary["confirmed"])
        )
        self.waiting_card.set_value(
            str(summary["waiting"])
        )
        self.declined_card.set_value(
            str(summary["declined"])
        )
        self.adults_card.set_value(
            f"{summary['confirmed_adults']} / "
            f"{summary['planned_adults']}"
        )
        self.children_card.set_value(
            f"{summary['confirmed_children']} / "
            f"{summary['planned_children']}"
        )

        answered = (
            summary["confirmed"]
            + summary["declined"]
        )
        response_rate = (
            round(answered / summary["planned"] * 100)
            if summary["planned"]
            else 0
        )

        self.response_progress.setValue(response_rate)
        self.response_progress.setFormat(
            f"{response_rate}% válaszolt"
        )
        self.response_progress_label.setText(
            f"{answered} vendég válaszolt, "
            f"{summary['waiting']} válaszára még várunk."
        )

        self.dinner_card.set_value(
            str(summary["dinner"])
        )
        self.no_dinner_card.set_value(
            str(summary["not_dinner"])
        )

        preference_summary = (
            self.guest_repository
            .get_preference_summary()
        )
        special_guest_count = sum(
            item["count"]
            for item in preference_summary
        )
        self.special_diet_card.set_value(
            str(special_guest_count)
        )
        self.contactable_card.set_value(
            str(
                self.guest_repository
                .get_contactable_count()
            )
        )

        self._refresh_tables()
        self._refresh_preferences(preference_summary)
        self._refresh_rsvp()

    def _refresh_tables(self) -> None:
        table_summary = (
            self.guest_repository
            .get_table_summary()
        )

        capacity = sum(
            table["capacity"]
            for table in table_summary
        )
        assigned = sum(
            table["assigned"]
            for table in table_summary
        )
        overbooked = sum(
            1
            for table in table_summary
            if table["remaining"] < 0
        )

        self.unassigned_card.set_value(
            str(
                self.guest_repository
                .get_unassigned_confirmed_count()
            )
        )
        self.capacity_card.set_value(str(capacity))
        self.assigned_card.set_value(str(assigned))
        self.overbooked_card.set_value(str(overbooked))

        self.tables_table.setRowCount(
            len(table_summary)
        )

        for row, table in enumerate(table_summary):
            if table["remaining"] < 0:
                status = "Túlfoglalt"
            elif table["remaining"] == 0:
                status = "Megtelt"
            else:
                status = "Van szabad hely"

            values = (
                table["name"],
                str(table["capacity"]),
                str(table["assigned"]),
                str(table["remaining"]),
                status,
            )

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)

                if status == "Túlfoglalt":
                    item.setForeground(Qt.darkRed)
                elif status == "Megtelt":
                    item.setForeground(Qt.darkYellow)

                self.tables_table.setItem(
                    row,
                    column,
                    item,
                )

        self.tables_table.resizeRowsToContents()

    def _refresh_preferences(
        self,
        preference_summary,
    ) -> None:
        self.preferences_table.setRowCount(
            len(preference_summary)
        )

        for row, preference in enumerate(
            preference_summary
        ):
            values = (
                preference["category"],
                preference["name"],
                str(preference["count"]),
            )

            for column, value in enumerate(values):
                self.preferences_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

        self.preferences_table.resizeRowsToContents()

    def _refresh_rsvp(self) -> None:
        overview = (
            self.group_repository
            .get_rsvp_overview()
        )

        self.rsvp_table.setRowCount(len(overview))

        for row, group in enumerate(overview):
            due_date = group["rsvp_due_date"]

            if group["waiting"] == 0:
                status = "Lezárt"
            elif due_date is None:
                status = "Nincs határidő"
            else:
                days_left = (due_date - date.today()).days

                if days_left < 0:
                    status = (
                        f"{abs(days_left)} napja lejárt"
                    )
                elif days_left == 0:
                    status = "Ma esedékes"
                elif days_left <= 10:
                    status = (
                        f"{days_left} nap múlva"
                    )
                else:
                    status = "Folyamatban"

            values = (
                group["name"],
                group["group_type"],
                (
                    due_date.strftime("%Y.%m.%d.")
                    if due_date
                    else "—"
                ),
                str(group["total"]),
                str(group["confirmed"]),
                str(group["waiting"]),
                str(group["declined"]),
                status,
            )

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)

                if "lejárt" in status:
                    item.setForeground(Qt.darkRed)
                elif (
                    status == "Ma esedékes"
                    or "nap múlva" in status
                ):
                    item.setForeground(Qt.darkYellow)

                self.rsvp_table.setItem(
                    row,
                    column,
                    item,
                )

        self.rsvp_table.resizeRowsToContents()
