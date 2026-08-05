from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from our_day.repositories.guest_repository import GuestRepository
from our_day.ui.dialogs.guest_dialog import GuestDialog
from our_day.ui.widgets.statistic_card import StatisticCard


class GuestsPage(QWidget):
    data_changed = Signal()

    def __init__(self, repository: GuestRepository, table_repository) -> None:
        super().__init__()
        self.repository = repository
        self.table_repository = table_repository

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(18)

        header = QHBoxLayout()
        header_text = QVBoxLayout()

        title = QLabel("Meghívottak")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Meghívások, visszajelzések, kísérők és vendéglátási információk."
        )
        subtitle.setObjectName("pageSubtitle")

        header_text.addWidget(title)
        header_text.addWidget(subtitle)

        add_button = QPushButton("+ Új meghívott")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.open_create_dialog)

        header.addLayout(header_text)
        header.addStretch()
        header.addWidget(add_button)
        layout.addLayout(header)

        summary_layout = QHBoxLayout()
        self.planned_card = StatisticCard("Tervezett létszám", "0")
        self.confirmed_card = StatisticCard("Részt vesz", "0")
        self.waiting_card = StatisticCard("Válaszra vár", "0")
        self.declined_card = StatisticCard("Nem vesz részt", "0")

        for card in (
            self.planned_card,
            self.confirmed_card,
            self.waiting_card,
            self.declined_card,
        ):
            summary_layout.addWidget(card)

        layout.addLayout(summary_layout)

        actions = QHBoxLayout()

        edit_button = QPushButton("Szerkesztés")
        edit_button.setObjectName("secondaryButton")
        edit_button.clicked.connect(self._edit_selected)

        confirm_button = QPushButton("Részt vesz")
        confirm_button.setObjectName("secondaryButton")
        confirm_button.clicked.connect(
            lambda: self._set_attendance_status("Részt vesz")
        )

        decline_button = QPushButton("Nem vesz részt")
        decline_button.setObjectName("secondaryButton")
        decline_button.clicked.connect(
            lambda: self._set_attendance_status("Nem vesz részt")
        )

        delete_button = QPushButton("Törlés")
        delete_button.setObjectName("dangerButton")
        delete_button.clicked.connect(self._delete_selected)

        actions.addWidget(edit_button)
        actions.addWidget(confirm_button)
        actions.addWidget(decline_button)
        actions.addWidget(delete_button)
        actions.addStretch()
        layout.addLayout(actions)

        self.table = QTableWidget(0, 11)
        self.table.setHorizontalHeaderLabels(
            [
                "Név",
                "Típus",
                "Meghívás",
                "Részvétel",
                "Kísérő",
                "Vacsora",
                "Ételérzékenység / igény",
                "Asztal",
                "Elérhetőség",
                "Kapcsolódó meghívott",
                "Azonosító",
            ]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._edit_selected)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(0, QHeaderView.Stretch)
        header_view.setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.setColumnHidden(10, True)

        layout.addWidget(self.table, 1)

    def refresh(self) -> None:
        guests = self.repository.list_all()
        summary = self.repository.get_summary()

        self.planned_card.set_value(str(summary["planned"]))
        self.confirmed_card.set_value(str(summary["confirmed"]))
        self.waiting_card.set_value(str(summary["waiting"]))
        self.declined_card.set_value(str(summary["declined"]))

        self.table.setRowCount(len(guests))

        for row, guest in enumerate(guests):
            contact = " • ".join(
                value for value in (guest.phone, guest.email) if value
            ) or "—"

            plus_one = (
                guest.plus_one_name
                if guest.has_plus_one and guest.plus_one_name
                else ("Igen" if guest.has_plus_one else "Nem")
            )

            linked_name = self.repository.get_parent_name(guest.parent_guest_id) or "—"

            values = (
                guest.name,
                guest.guest_type,
                guest.invitation_status,
                guest.attendance_status,
                plus_one,
                "Igen" if guest.attends_dinner else "Nem",
                guest.dietary_notes or "—",
                guest.table_name or "—",
                contact,
                linked_name,
                str(guest.id),
            )

            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

    def open_create_dialog(self) -> None:
        dialog = GuestDialog(self, tables=self.table_repository.list_all())
        if dialog.exec():
            self.repository.create_with_companion(dialog.get_guest(), dialog.get_companion())
            self.data_changed.emit()

    def _selected_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(
                self,
                "Nincs kiválasztott meghívott",
                "Először válassz ki egy sort.",
            )
            return None
        return int(self.table.item(rows[0].row(), 10).text())

    def _edit_selected(self) -> None:
        guest_id = self._selected_id()
        if guest_id is None:
            return

        guest = self.repository.get_by_id(guest_id)
        if guest is None:
            QMessageBox.warning(self, "Hiba", "A meghívott nem található.")
            return

        companion = self.repository.get_companion(guest_id)
        dialog = GuestDialog(
            self,
            guest,
            companion,
            self.table_repository.list_all(),
        )
        if dialog.exec():
            self.repository.update_with_companion(dialog.get_guest(), dialog.get_companion())
            self.data_changed.emit()

    def _set_attendance_status(self, status: str) -> None:
        guest_id = self._selected_id()
        if guest_id is None:
            return

        guest = self.repository.get_by_id(guest_id)
        if guest is None:
            return

        guest.attendance_status = status
        guest.invitation_status = "Visszajelzett"
        self.repository.update(guest)
        self.data_changed.emit()

    def _delete_selected(self) -> None:
        guest_id = self._selected_id()
        if guest_id is None:
            return

        answer = QMessageBox.question(
            self,
            "Meghívott törlése",
            "Biztosan törölni szeretnéd a kiválasztott meghívottat?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer == QMessageBox.Yes:
            self.repository.delete(guest_id)
            self.data_changed.emit()
