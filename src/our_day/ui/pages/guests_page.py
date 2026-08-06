from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from our_day.services.guest_export_service import GuestExportService
from our_day.ui.dialogs.assign_guests_dialog import AssignGuestsDialog
from our_day.ui.dialogs.guest_dialog import GuestDialog
from our_day.ui.dialogs.invitation_group_dialog import (
    InvitationGroupDialog,
)
from our_day.ui.widgets.statistic_card import StatisticCard


class GuestsPage(QWidget):
    data_changed = Signal()

    GROUP_ID_ROLE = Qt.UserRole

    def __init__(
        self,
        guest_repository,
        table_repository,
        preference_repository,
        group_repository,
    ) -> None:
        super().__init__()

        self.guest_repository = guest_repository
        self.table_repository = table_repository
        self.preference_repository = preference_repository
        self.group_repository = group_repository
        self.current_group_id: int | None = None

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(30, 26, 30, 26)
        root_layout.setSpacing(18)

        header_layout = QHBoxLayout()

        header_text = QVBoxLayout()
        header_text.setSpacing(4)

        title = QLabel("Meghívottkezelő")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Meghívási csoportok, RSVP, étkezési igények és ültetés."
        )
        subtitle.setObjectName("pageSubtitle")

        header_text.addWidget(title)
        header_text.addWidget(subtitle)

        export_button = QPushButton("Excel export")
        export_button.setObjectName("secondaryButton")
        export_button.clicked.connect(self._export_excel)

        new_group_button = QPushButton("+ Új csoport")
        new_group_button.setObjectName("secondaryButton")
        new_group_button.clicked.connect(self._create_group)

        new_guest_button = QPushButton("+ Új vendég")
        new_guest_button.setObjectName("primaryButton")
        new_guest_button.clicked.connect(self._create_guest)

        header_layout.addLayout(header_text)
        header_layout.addStretch()
        header_layout.addWidget(export_button)
        header_layout.addWidget(new_group_button)
        header_layout.addWidget(new_guest_button)

        root_layout.addLayout(header_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        splitter.addWidget(self._create_group_panel())
        splitter.addWidget(self._create_workspace_panel())
        splitter.setSizes([330, 970])

        root_layout.addWidget(splitter, 1)

    def _create_group_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("contentCard")
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(390)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Meghívási csoportok")
        title.setObjectName("sectionTitle")

        helper = QLabel(
            "Egy csoport lehet személy, pár, család vagy társaság."
        )
        helper.setWordWrap(True)
        helper.setObjectName("pageSubtitle")

        self.group_search = QLineEdit()
        self.group_search.setPlaceholderText("Csoport keresése...")
        self.group_search.textChanged.connect(self._refresh_group_list)

        self.group_list = QListWidget()
        self.group_list.setSpacing(4)
        self.group_list.currentItemChanged.connect(
            self._group_changed
        )

        actions = QHBoxLayout()

        edit_button = QPushButton("Szerkesztés")
        edit_button.setObjectName("secondaryButton")
        edit_button.clicked.connect(self._edit_group)

        delete_button = QPushButton("Törlés")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self._delete_group)

        actions.addWidget(edit_button)
        actions.addWidget(delete_button)

        layout.addWidget(title)
        layout.addWidget(helper)
        layout.addWidget(self.group_search)
        layout.addWidget(self.group_list, 1)
        layout.addLayout(actions)

        return panel

    def _create_workspace_panel(self) -> QWidget:
        panel = QWidget()

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 0, 0, 0)
        layout.setSpacing(14)

        self.group_detail_card = QFrame()
        self.group_detail_card.setObjectName("contentCard")

        detail_layout = QVBoxLayout(self.group_detail_card)
        detail_layout.setContentsMargins(22, 20, 22, 20)
        detail_layout.setSpacing(12)

        detail_header = QHBoxLayout()

        detail_text = QVBoxLayout()
        detail_text.setSpacing(3)

        self.group_title = QLabel("Összes meghívott")
        self.group_title.setStyleSheet(
            "font-size: 22px; font-weight: 700; background: transparent;"
        )

        self.group_meta = QLabel(
            "Az összes meghívott egy közös nézetben."
        )
        self.group_meta.setObjectName("pageSubtitle")
        self.group_meta.setWordWrap(True)

        detail_text.addWidget(self.group_title)
        detail_text.addWidget(self.group_meta)

        self.assign_existing_button = QPushButton("Meglévő személyek")
        self.assign_existing_button.setObjectName("secondaryButton")
        self.assign_existing_button.clicked.connect(self._assign_existing_guests)

        self.add_member_button = QPushButton("+ Tag hozzáadása")
        self.add_member_button.setObjectName("primaryButton")
        self.add_member_button.clicked.connect(self._create_guest)

        detail_header.addLayout(detail_text)
        detail_header.addStretch()
        detail_header.addWidget(self.assign_existing_button)
        detail_header.addWidget(self.add_member_button)

        detail_layout.addLayout(detail_header)

        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(12)
        stats_grid.setVerticalSpacing(12)

        self.total_card = StatisticCard("Összesen", "0", "accent")
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
        self.dinner_card = StatisticCard(
            "Vacsorázik",
            "0",
            "success",
        )

        for index, card in enumerate(
            (
                self.total_card,
                self.confirmed_card,
                self.waiting_card,
                self.declined_card,
                self.dinner_card,
            )
        ):
            stats_grid.addWidget(card, 0, index)

        detail_layout.addLayout(stats_grid)

        filter_card = QFrame()
        filter_card.setObjectName("contentCard")

        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(14, 12, 14, 12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Vendég keresése...")
        self.search_input.textChanged.connect(self._refresh_table)

        self.status_filter = QComboBox()
        self.status_filter.addItems(
            (
                "Minden státusz",
                "Válaszra vár",
                "Részt vesz",
                "Nem vesz részt",
            )
        )
        self.status_filter.currentTextChanged.connect(
            self._refresh_table
        )

        self.type_filter = QComboBox()
        self.type_filter.addItems(
            ("Minden típus", "Felnőtt", "Gyermek")
        )
        self.type_filter.currentTextChanged.connect(
            self._refresh_table
        )

        filter_layout.addWidget(self.search_input, 1)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(self.type_filter)

        action_layout = QHBoxLayout()

        edit_guest_button = QPushButton("Szerkesztés")
        edit_guest_button.setObjectName("secondaryButton")
        edit_guest_button.clicked.connect(self._edit_guest)

        confirm_button = QPushButton("Részt vesz")
        confirm_button.setObjectName("secondaryButton")
        confirm_button.clicked.connect(
            lambda: self._set_status("Részt vesz")
        )

        waiting_button = QPushButton("Válaszra vár")
        waiting_button.setObjectName("secondaryButton")
        waiting_button.clicked.connect(
            lambda: self._set_status("Válaszra vár")
        )

        decline_button = QPushButton("Nem vesz részt")
        decline_button.setObjectName("secondaryButton")
        decline_button.clicked.connect(
            lambda: self._set_status("Nem vesz részt")
        )

        delete_guest_button = QPushButton("Törlés")
        delete_guest_button.setObjectName("dangerButton")
        delete_guest_button.clicked.connect(self._delete_guest)

        for button in (
            edit_guest_button,
            confirm_button,
            waiting_button,
            decline_button,
            delete_guest_button,
        ):
            action_layout.addWidget(button)

        action_layout.addStretch()

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            (
                "Név",
                "Típus",
                "RSVP",
                "Vacsora",
                "Asztal",
                "Étrend / allergia",
                "Szerep",
                "Megjegyzés",
                "ID",
            )
        )
        self.table.setColumnHidden(8, True)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit_guest)

        table_header = self.table.horizontalHeader()
        table_header.setSectionResizeMode(
            0,
            QHeaderView.Stretch,
        )
        table_header.setSectionResizeMode(
            5,
            QHeaderView.Stretch,
        )

        layout.addWidget(self.group_detail_card)
        layout.addWidget(filter_card)
        layout.addLayout(action_layout)
        layout.addWidget(self.table, 1)

        return panel

    def refresh(self) -> None:
        self._refresh_group_list()
        self._refresh_group_workspace()

    def _refresh_group_list(self) -> None:
        selected_id = self.current_group_id
        search = self.group_search.text().strip().lower()

        self.group_list.blockSignals(True)
        self.group_list.clear()

        total_count = len(self.guest_repository.list_all())

        all_item = QListWidgetItem(
            f"Összes meghívott\n{total_count} fő"
        )
        all_item.setData(self.GROUP_ID_ROLE, None)
        self.group_list.addItem(all_item)

        for group in self.group_repository.list_all():
            if search and search not in group.name.lower():
                continue

            summary = self.group_repository.get_summary(group.id)

            item = QListWidgetItem(
                f"{group.name}\n"
                f"{summary['confirmed']} / {summary['total']} visszaigazolt"
            )
            item.setData(self.GROUP_ID_ROLE, group.id)
            item.setToolTip(
                f"{group.group_type} • "
                f"{summary['waiting']} válaszra vár"
            )
            self.group_list.addItem(item)

        selected_row = 0

        for index in range(self.group_list.count()):
            item = self.group_list.item(index)

            if item.data(self.GROUP_ID_ROLE) == selected_id:
                selected_row = index
                break

        self.group_list.setCurrentRow(selected_row)
        self.group_list.blockSignals(False)

    def _refresh_group_workspace(self) -> None:
        if self.current_group_id is None:
            guest_summary = self.guest_repository.get_summary()
            summary = {
                "total": guest_summary["planned"],
                "confirmed": guest_summary["confirmed"],
                "waiting": guest_summary["waiting"],
                "declined": guest_summary["declined"],
                "dinner": guest_summary["dinner"],
            }

            self.group_title.setText("Összes meghívott")
            self.group_meta.setText(
                "Az összes meghívott egy közös, szűrhető nézetben."
            )
            self.add_member_button.setText("+ Új vendég")
            self.assign_existing_button.setVisible(False)
        else:
            group = self.group_repository.get_by_id(
                self.current_group_id
            )
            summary = self.group_repository.get_summary(
                self.current_group_id
            )

            if group:
                metadata = [group.group_type]

                if group.group_type == "Család":
                    contact_name = (
                        self.group_repository
                        .get_contact_guest_name(group.id)
                    )

                    if contact_name:
                        metadata.append(
                            f"Kapcsolattartó: {contact_name}"
                        )

                if group.rsvp_due_date:
                    days = (
                        group.rsvp_due_date - date.today()
                    ).days

                    if days < 0:
                        deadline = (
                            f"RSVP: {abs(days)} napja lejárt"
                        )
                    elif days == 0:
                        deadline = "RSVP: ma esedékes"
                    else:
                        deadline = (
                            f"RSVP: {days} nap múlva"
                        )

                    metadata.append(deadline)

                if group.phone:
                    metadata.append(group.phone)

                if group.email:
                    metadata.append(group.email)

                self.group_title.setText(group.name)
                self.group_meta.setText(" • ".join(metadata))
                self.add_member_button.setText("+ Tag hozzáadása")
                self.assign_existing_button.setVisible(True)

        self.total_card.set_value(str(summary["total"]))
        self.confirmed_card.set_value(
            str(summary["confirmed"])
        )
        self.waiting_card.set_value(str(summary["waiting"]))
        self.declined_card.set_value(
            str(summary["declined"])
        )
        self.dinner_card.set_value(str(summary["dinner"]))

        self._refresh_table()

    def _refresh_table(self) -> None:
        guests = (
            self.guest_repository.list_all()
            if self.current_group_id is None
            else self.guest_repository.list_by_group(
                self.current_group_id
            )
        )

        search = self.search_input.text().strip().lower()
        status = self.status_filter.currentText()
        guest_type = self.type_filter.currentText()

        if search:
            guests = [
                guest
                for guest in guests
                if search in guest.name.lower()
            ]

        if status != "Minden státusz":
            guests = [
                guest
                for guest in guests
                if guest.attendance_status == status
            ]

        if guest_type != "Minden típus":
            guests = [
                guest
                for guest in guests
                if guest.guest_type == guest_type
            ]

        preference_map = {
            item["id"]: (
                f"{item['category']}: {item['name']}"
            )
            for item in self.preference_repository.list_all()
        }

        self.table.setRowCount(len(guests))

        for row, guest in enumerate(guests):
            preferences = ", ".join(
                preference_map.get(preference_id, "")
                for preference_id in guest.preference_ids
                if preference_map.get(preference_id)
            ) or "—"

            values = (
                guest.name,
                guest.guest_type,
                guest.attendance_status,
                "Igen" if guest.attends_dinner else "Nem",
                guest.table_name or "—",
                preferences,
                (
                    "Kapcsolattartó"
                    if guest.is_contact_person
                    else "—"
                ),
                guest.notes or "—",
                str(guest.id),
            )

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)

                if (
                    column == 2
                    and guest.attendance_status
                    == "Nem vesz részt"
                ):
                    item.setForeground(Qt.darkRed)

                self.table.setItem(row, column, item)

    def _export_excel(self) -> None:
        default_name = (
            f"our_day_vendeglista_"
            f"{date.today().isoformat()}.xlsx"
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Vendéglista Excel export",
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
            f"A vendéglista sikeresen elkészült:\n{file_path}",
        )

    def _group_changed(self, current, previous) -> None:
        self.current_group_id = (
            current.data(self.GROUP_ID_ROLE)
            if current
            else None
        )
        self._refresh_group_workspace()

    def _selected_guest_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()

        if not rows:
            QMessageBox.information(
                self,
                "Nincs kiválasztás",
                "Válassz ki egy vendéget.",
            )
            return None

        return int(
            self.table.item(rows[0].row(), 8).text()
        )

    def _selected_group_id(self) -> int | None:
        item = self.group_list.currentItem()

        if not item:
            return None

        return item.data(self.GROUP_ID_ROLE)

    def _create_group(self) -> None:
        dialog = InvitationGroupDialog(self)

        if dialog.exec():
            self.current_group_id = (
                self.group_repository.create(
                    dialog.get_group()
                )
            )
            self.data_changed.emit()

    def _edit_group(self) -> None:
        group_id = self._selected_group_id()

        if group_id is None:
            QMessageBox.information(
                self,
                "Nincs kiválasztott csoport",
                "Az Összes meghívott nézet nem szerkeszthető.",
            )
            return

        group = self.group_repository.get_by_id(group_id)
        dialog = InvitationGroupDialog(
            self,
            group,
            self.group_repository.list_group_members(
                group_id
            ),
        )

        if dialog.exec():
            updated_group = dialog.get_group()
            self.group_repository.update(
                updated_group
            )
            self.group_repository.set_contact_guest(
                group_id,
                (
                    updated_group.contact_guest_id
                    if updated_group.group_type == "Család"
                    else None
                ),
            )
            self.data_changed.emit()

    def _delete_group(self) -> None:
        group_id = self._selected_group_id()

        if group_id is None:
            return

        answer = QMessageBox.question(
            self,
            "Csoport törlése",
            (
                "A vendégek megmaradnak, de csoport nélkül. "
                "Biztosan folytatod?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer == QMessageBox.Yes:
            self.group_repository.delete(group_id)
            self.current_group_id = None
            self.data_changed.emit()

    def _assign_existing_guests(self) -> None:
        group_id = self._selected_group_id()
        if group_id is None:
            QMessageBox.information(self, "Nincs kiválasztott csoport", "Először válassz ki egy meghívási csoportot.")
            return

        available_guests = self.guest_repository.list_unassigned_guests()
        if not available_guests:
            QMessageBox.information(self, "Nincs hozzáadható személy", "Nincs olyan személy, aki még nem tartozik meghívási csoporthoz.")
            return

        group = self.group_repository.get_by_id(group_id)
        dialog = AssignGuestsDialog(
            self,
            guests=available_guests,
            group_name=group.name if group else "",
        )
        if not dialog.exec():
            return

        selected_guest_ids = dialog.get_selected_guest_ids()
        self.guest_repository.assign_guests_to_group(selected_guest_ids, group_id)
        QMessageBox.information(
            self,
            "Személyek hozzáadva",
            f"{len(selected_guest_ids)} személy sikeresen bekerült a csoportba.",
        )
        self.data_changed.emit()

    def _create_guest(self) -> None:
        dialog = GuestDialog(
            self,
            tables=self.table_repository.list_all(),
            preferences=self.preference_repository.list_all(),
        )

        if dialog.exec():
            guest = dialog.get_guest()
            guest.invitation_group_id = self.current_group_id

            self.guest_repository.create_group(
                guest,
                dialog.get_members(),
            )
            self.data_changed.emit()

    def _edit_guest(self) -> None:
        guest_id = self._selected_guest_id()

        if guest_id is None:
            return

        guest = self.guest_repository.get_by_id(guest_id)
        members = self.guest_repository.get_linked_members(
            guest_id
        )

        dialog = GuestDialog(
            self,
            guest,
            members,
            self.table_repository.list_all(),
            self.preference_repository.list_all(),
        )

        if dialog.exec():
            updated_guest = dialog.get_guest()
            updated_guest.invitation_group_id = (
                guest.invitation_group_id
            )

            self.guest_repository.update_group(
                updated_guest,
                dialog.get_members(),
            )
            self.data_changed.emit()

    def _set_status(self, status: str) -> None:
        guest_id = self._selected_guest_id()

        if guest_id is None:
            return

        guest = self.guest_repository.get_by_id(guest_id)
        guest.attendance_status = status

        if status != "Válaszra vár":
            guest.invitation_status = "Visszajelzett"

        self.guest_repository.update(guest)
        self.data_changed.emit()

    def _delete_guest(self) -> None:
        guest_id = self._selected_guest_id()

        if guest_id is None:
            return

        answer = QMessageBox.question(
            self,
            "Vendég törlése",
            "Biztosan törölni szeretnéd a vendéget?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer == QMessageBox.Yes:
            self.guest_repository.delete(guest_id)
            self.data_changed.emit()
