from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from our_day.services.seating_export_service import (
    SeatingExportService,
)
from our_day.ui.dialogs.seating_preference_dialog import (
    SeatingPreferenceDialog,
)
from our_day.ui.seating.auto_seating import (
    AutoSeatingService,
)
from our_day.ui.seating.drag_list import (
    GuestDropList,
)
from our_day.ui.seating.room_export import (
    RoomExportService,
)
from our_day.ui.seating.table_item import (
    MovableTableItem,
)
from our_day.ui.widgets.statistic_card import (
    StatisticCard,
)


class SeatingPage(QWidget):
    data_changed = Signal()

    def __init__(
        self,
        guest_repository,
        table_repository,
        preference_repository,
    ) -> None:
        super().__init__()

        self.guest_repository = (
            guest_repository
        )
        self.table_repository = (
            table_repository
        )
        self.preference_repository = (
            preference_repository
        )

        self.guests = []
        self.tables = []
        self.preference_map = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            30,
            26,
            30,
            26,
        )
        layout.setSpacing(16)

        layout.addLayout(
            self._create_header()
        )
        layout.addLayout(
            self._create_statistics()
        )

        self.warning_box = QLabel()
        self.warning_box.setObjectName(
            "seatingWarnings"
        )
        self.warning_box.setWordWrap(True)
        layout.addWidget(self.warning_box)

        self.tabs = QTabWidget()
        self.tabs.addTab(
            self._create_list_view(),
            "Gyors kiosztás",
        )
        self.tabs.addTab(
            self._create_room_view(),
            "Teremnézet",
        )

        layout.addWidget(
            self.tabs,
            1,
        )

    def _create_header(self):
        header = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel(
            "Ültetési rend 2.0"
        )
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Drag & drop, teremnézet, "
            "automatikus javaslatok és "
            "catering összesítés."
        )
        subtitle.setObjectName(
            "pageSubtitle"
        )

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        cleanup_button = QPushButton(
            "RSVP tisztítás"
        )
        cleanup_button.setObjectName(
            "secondaryButton"
        )
        cleanup_button.clicked.connect(
            self._cleanup
        )

        export_button = QPushButton(
            "Excel export"
        )
        export_button.setObjectName(
            "secondaryButton"
        )
        export_button.clicked.connect(
            self._export
        )

        auto_button = QPushButton(
            "Automatikus ültetés"
        )
        auto_button.setObjectName(
            "primaryButton"
        )
        auto_button.clicked.connect(
            self._auto_seat
        )

        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(cleanup_button)
        header.addWidget(export_button)
        header.addWidget(auto_button)

        return header

    def _create_statistics(self):
        statistics = QHBoxLayout()

        self.confirmed_card = StatisticCard(
            "Visszaigazolt",
            "0",
            "accent",
        )
        self.assigned_card = StatisticCard(
            "Elhelyezve",
            "0",
            "success",
        )
        self.unassigned_card = StatisticCard(
            "Asztal nélkül",
            "0",
            "warning",
        )
        self.warning_card = StatisticCard(
            "Figyelmeztetés",
            "0",
            "danger",
        )

        for card in (
            self.confirmed_card,
            self.assigned_card,
            self.unassigned_card,
            self.warning_card,
        ):
            statistics.addWidget(card)

        return statistics

    def _create_list_view(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(
            QFrame.NoFrame
        )

        self.list_content = QWidget()
        self.list_layout = QHBoxLayout(
            self.list_content
        )
        self.list_layout.setAlignment(
            Qt.AlignTop
        )

        scroll.setWidget(
            self.list_content
        )

        return scroll

    def _create_room_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        layout.setSpacing(10)

        toolbar = QHBoxLayout()

        helper = QLabel(
            "Az asztalok egérrel mozgathatók. "
            "A teljes összesítés az asztal "
            "fölé húzva látható."
        )
        helper.setObjectName(
            "pageSubtitle"
        )
        helper.setWordWrap(True)

        image_button = QPushButton(
            "Teremkép mentése"
        )
        image_button.setObjectName(
            "secondaryButton"
        )
        image_button.clicked.connect(
            self._save_room_image
        )

        print_button = QPushButton(
            "Nyomtatás / PDF"
        )
        print_button.setObjectName(
            "primaryButton"
        )
        print_button.clicked.connect(
            self._print_room
        )

        toolbar.addWidget(helper, 1)
        toolbar.addWidget(image_button)
        toolbar.addWidget(print_button)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(
            0,
            0,
            1600,
            1000,
        )

        self.room_view = QGraphicsView(
            self.scene
        )
        self.room_view.setRenderHint(
            QPainter.Antialiasing
        )
        self.room_view.setDragMode(
            QGraphicsView.RubberBandDrag
        )
        self.room_view.setBackgroundBrush(
            QBrush(
                QColor("#FFFFFF")
            )
        )

        layout.addLayout(toolbar)
        layout.addWidget(
            self.room_view,
            1,
        )

        return page

    def refresh(self) -> None:
        self.guests = (
            self.guest_repository
            .list_confirmed_for_seating()
        )
        self.tables = (
            self.table_repository.list_all()
        )
        self.preference_map = {
            item["id"]: (
                f"{item['category']}: "
                f"{item['name']}"
            )
            for item in (
                self.preference_repository
                .list_all()
            )
        }

        assigned = [
            guest
            for guest in self.guests
            if guest.table_id is not None
        ]
        unassigned = [
            guest
            for guest in self.guests
            if guest.table_id is None
        ]

        warnings = (
            self.guest_repository
            .get_seating_warnings()
        )

        self.confirmed_card.set_value(
            str(len(self.guests))
        )
        self.assigned_card.set_value(
            str(len(assigned))
        )
        self.unassigned_card.set_value(
            str(len(unassigned))
        )
        self.warning_card.set_value(
            str(len(warnings))
        )

        self.warning_box.setText(
            " • ".join(
                warning["title"]
                for warning in warnings[:5]
            )
            if warnings
            else (
                "Nincs észlelt csoport- "
                "vagy ültetési konfliktus."
            )
        )

        self._render_lists(
            unassigned
        )
        self._render_room()

    def _render_lists(
        self,
        unassigned,
    ) -> None:
        self._clear_layout(
            self.list_layout
        )

        self.list_layout.addWidget(
            self._make_column(
                "Asztal nélkül",
                None,
                unassigned,
            )
        )

        for table in self.tables:
            guests = [
                guest
                for guest in self.guests
                if guest.table_id == table.id
            ]

            self.list_layout.addWidget(
                self._make_column(
                    (
                        f"{table.name}\n"
                        f"{len(guests)} / "
                        f"{table.capacity} fő"
                    ),
                    table.id,
                    guests,
                )
            )

        self.list_layout.addStretch()

    def _make_column(
        self,
        title,
        table_id,
        guests,
    ):
        frame = QFrame()
        frame.setObjectName(
            "seatingTableCard"
        )
        frame.setMinimumWidth(290)
        frame.setMaximumWidth(360)

        layout = QVBoxLayout(frame)

        title_label = QLabel(title)
        title_label.setObjectName(
            "seatingTableTitle"
        )
        title_label.setWordWrap(True)

        drop_list = GuestDropList(
            table_id
        )
        drop_list.setSelectionMode(
            QAbstractItemView
            .ExtendedSelection
        )

        drop_list.guests_dropped.connect(
            self._drop_guests
        )
        drop_list.itemDoubleClicked.connect(
            lambda item: (
                self._edit_preference(
                    int(
                        item.data(
                            Qt.UserRole
                        )
                    )
                )
            )
        )

        for guest in guests:
            item = QListWidgetItem(
                self._guest_text(guest)
            )
            item.setData(
                Qt.UserRole,
                guest.id,
            )
            item.setToolTip(
                "Dupla kattintás: "
                "ültetési preferenciák"
            )
            drop_list.addItem(item)

        summary = QLabel(
            self._diet_summary(guests)
        )
        summary.setObjectName(
            "pageSubtitle"
        )
        summary.setWordWrap(True)

        preference_button = QPushButton(
            "Kijelölt preferenciái"
        )
        preference_button.setObjectName(
            "secondaryButton"
        )
        preference_button.clicked.connect(
            lambda: (
                self._edit_selected(
                    drop_list
                )
            )
        )

        layout.addWidget(title_label)
        layout.addWidget(
            drop_list,
            1,
        )
        layout.addWidget(summary)
        layout.addWidget(
            preference_button
        )

        return frame

    def _render_room(self) -> None:
        self.scene.clear()

        guests_by_table = defaultdict(list)

        for guest in self.guests:
            guests_by_table[
                guest.table_id
            ].append(guest)

        for table in self.tables:
            guests = guests_by_table[
                table.id
            ]

            item = MovableTableItem(
                table,
                len(guests),
                self._diet_summary(
                    guests
                ),
            )

            item.position_saved.connect(
                self.table_repository
                .update_position
            )

            self.scene.addItem(item)

    def _drop_guests(
        self,
        guest_ids,
        table_id,
    ) -> None:
        if table_id is not None:
            table = (
                self.table_repository
                .get_by_id(
                    int(table_id)
                )
            )

            if table is None:
                return

            current = len(
                [
                    guest
                    for guest in self.guests
                    if (
                        guest.table_id
                        == table_id
                        and guest.id
                        not in guest_ids
                    )
                ]
            )
            future = (
                current
                + len(guest_ids)
            )

            if future > table.capacity:
                answer = QMessageBox.warning(
                    self,
                    "Túlfoglalás",
                    (
                        f"A(z) {table.name} "
                        f"asztal {future}/"
                        f"{table.capacity} fő "
                        "lenne. Folytatod?"
                    ),
                    (
                        QMessageBox.Yes
                        | QMessageBox.No
                    ),
                    QMessageBox.No,
                )

                if (
                    answer
                    != QMessageBox.Yes
                ):
                    return

        self.guest_repository.assign_guests_to_table(
            guest_ids,
            table_id,
        )
        self.data_changed.emit()

    def _edit_selected(
        self,
        widget,
    ) -> None:
        items = widget.selectedItems()

        if len(items) != 1:
            QMessageBox.information(
                self,
                "Vendég kiválasztása",
                (
                    "Pontosan egy vendéget "
                    "válassz ki."
                ),
            )
            return

        self._edit_preference(
            int(
                items[0].data(
                    Qt.UserRole
                )
            )
        )

    def _edit_preference(
        self,
        guest_id,
    ) -> None:
        guest = (
            self.guest_repository
            .get_by_id(guest_id)
        )

        if not guest:
            return

        dialog = SeatingPreferenceDialog(
            self,
            guest,
            self.guests,
            (
                self.guest_repository
                .get_seating_preferences(
                    guest_id
                )
            ),
        )

        if not dialog.exec():
            return

        values = dialog.values()

        self.guest_repository.save_seating_preferences(
            guest_id,
            values["with"],
            values["avoid"],
            values["notes"],
            values["accessibility"],
        )

        self.data_changed.emit()

    def _auto_seat(self) -> None:
        if not self.tables:
            self.refresh()

        if not self.tables:
            QMessageBox.information(
                self,
                "Nincs asztal",
                (
                    "Először hozz létre "
                    "asztalokat."
                ),
            )
            return

        if not self.guests:
            QMessageBox.information(
                self,
                "Nincs vendég",
                (
                    "Nincs „Részt vesz” "
                    "állapotú vendég."
                ),
            )
            return

        proposal, unplaced = (
            AutoSeatingService
            .create_proposal(
                self.guests,
                self.tables,
            )
        )

        summary = "\n".join(
            (
                f"{table.name}: "
                f"{sum(1 for value in proposal.values() if value == table.id)} fő"
            )
            for table in self.tables
        )

        if unplaced:
            summary += (
                "\n\nNem elhelyezhető: "
                f"{len(unplaced)} fő"
            )

        answer = QMessageBox.question(
            self,
            "Automatikus ültetés",
            (
                "A program kapacitás és "
                "csoportok alapján készített "
                "javaslatot:\n\n"
                f"{summary}\n\n"
                "Alkalmazod?"
            ),
            (
                QMessageBox.Yes
                | QMessageBox.No
            ),
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        self.guest_repository.assign_guests_to_table(
            [
                guest.id
                for guest in self.guests
            ],
            None,
        )

        for table_id in set(
            proposal.values()
        ):
            guest_ids = [
                guest_id
                for guest_id, value
                in proposal.items()
                if value == table_id
            ]

            self.guest_repository.assign_guests_to_table(
                guest_ids,
                table_id,
            )

        self.data_changed.emit()

    def _export(self) -> None:
        if not self.tables and not self.guests:
            self.refresh()

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Ültetési rend export",
            "our_day_ultetesi_rend.xlsx",
            "Excel munkafüzet (*.xlsx)",
        )

        if not file_path:
            return

        try:
            exported = (
                SeatingExportService.export(
                    file_path,
                    self.tables,
                    self.guests,
                    self.preference_map,
                )
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Export hiba",
                (
                    "Az export nem sikerült."
                    f"\n\n{error}"
                ),
            )
            return

        QMessageBox.information(
            self,
            "Export elkészült",
            f"Elkészült:\n{exported}",
        )

    def _save_room_image(self) -> None:
        if not self.tables:
            self.refresh()

        if not self.tables:
            QMessageBox.information(
                self,
                "Nincs teremnézet",
                "Nincs exportálható asztal.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Teremkép mentése",
            "our_day_teremnezeti_terv.png",
            (
                "PNG kép (*.png);;"
                "JPEG kép (*.jpg *.jpeg)"
            ),
        )

        if not file_path:
            return

        try:
            destination = (
                RoomExportService.save_image(
                    self.scene,
                    file_path,
                )
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Mentési hiba",
                str(error),
            )
            return

        QMessageBox.information(
            self,
            "Teremkép elkészült",
            (
                "A kép sikeresen "
                f"elkészült:\n{destination}"
            ),
        )

    def _print_room(self) -> None:
        if not self.tables:
            self.refresh()

        if not self.tables:
            QMessageBox.information(
                self,
                "Nincs teremnézet",
                "Nincs nyomtatható asztal.",
            )
            return

        RoomExportService.print_scene(
            self,
            self.scene,
        )

    def _cleanup(self) -> None:
        count = (
            self.guest_repository
            .cleanup_invalid_seating()
        )

        QMessageBox.information(
            self,
            "RSVP tisztítás",
            (
                f"{count} már nem részt "
                "vevő vendég ültetése "
                "törölve."
            ),
        )

        self.data_changed.emit()

    def _guest_text(
        self,
        guest,
    ) -> str:
        flags = [guest.guest_type]

        if guest.attends_dinner:
            flags.append("Vacsora")

        if guest.preference_ids:
            flags.append(
                "Speciális igény"
            )

        if (
            guest
            .accessibility_required
        ):
            flags.append(
                "Könnyű megközelítés"
            )

        return (
            f"{guest.name}\n"
            f"{' • '.join(flags)}"
        )

    def _diet_summary(
        self,
        guests,
    ) -> str:
        adults = sum(
            guest.guest_type == "Felnőtt"
            for guest in guests
        )
        children = sum(
            guest.guest_type == "Gyermek"
            for guest in guests
        )

        preferences = defaultdict(int)

        for guest in guests:
            for preference_id in (
                guest.preference_ids
            ):
                if (
                    preference_id
                    in self.preference_map
                ):
                    preferences[
                        self.preference_map[
                            preference_id
                        ]
                    ] += 1

        preference_text = ", ".join(
            f"{name}: {count}"
            for name, count in sorted(
                preferences.items()
            )
        )

        result = (
            f"{adults} felnőtt • "
            f"{children} gyermek"
        )

        if preference_text:
            result += (
                f"\n{preference_text}"
            )

        return result

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.deleteLater()
