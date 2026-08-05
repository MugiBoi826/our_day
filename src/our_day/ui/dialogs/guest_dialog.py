from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from our_day.models.guest import Guest


class PersonDialog(QDialog):
    def __init__(
        self,
        parent=None,
        guest: Guest | None = None,
        preferences=None,
    ) -> None:
        super().__init__(parent)
        self.guest = guest
        self.preferences = preferences or []

        self.setWindowTitle(
            "Családtag szerkesztése"
            if guest
            else "Új családtag"
        )
        self.resize(560, 650)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()

        self.type_input = QComboBox()
        self.type_input.addItems(("Felnőtt", "Gyermek"))

        self.attendance_input = QComboBox()
        self.attendance_input.addItems(
            ("Válaszra vár", "Részt vesz", "Nem vesz részt")
        )

        self.dinner_input = QCheckBox("Részt vesz a vacsorán")
        self.dinner_input.setChecked(True)

        self.preferences_list = QListWidget()
        self.preferences_list.setMinimumHeight(180)

        for preference in self.preferences:
            item = QListWidgetItem(
                f"{preference['category']}: {preference['name']}"
            )
            item.setData(Qt.UserRole, preference["id"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.preferences_list.addItem(item)

        self.notes_input = QTextEdit()
        self.notes_input.setMinimumHeight(90)

        form.addRow("Név *", self.name_input)
        form.addRow("Vendég típusa", self.type_input)
        form.addRow("Részvétel", self.attendance_input)
        form.addRow("Vacsora", self.dinner_input)
        form.addRow(
            "Étrend / érzékenység / allergia",
            self.preferences_list,
        )
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

        if guest:
            self._load_guest(guest)

    def _load_guest(self, guest: Guest) -> None:
        self.name_input.setText(guest.name)
        self.type_input.setCurrentText(guest.guest_type)
        self.attendance_input.setCurrentText(
            guest.attendance_status
        )
        self.dinner_input.setChecked(guest.attends_dinner)
        self.notes_input.setPlainText(guest.notes)

        for index in range(self.preferences_list.count()):
            item = self.preferences_list.item(index)
            if item.data(Qt.UserRole) in guest.preference_ids:
                item.setCheckState(Qt.Checked)

    def _save(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                "Hiányzó név",
                "A családtag neve kötelező.",
            )
            return
        self.accept()

    def get_guest(self) -> Guest:
        preference_ids = [
            self.preferences_list.item(index).data(Qt.UserRole)
            for index in range(self.preferences_list.count())
            if self.preferences_list.item(index).checkState()
            == Qt.Checked
        ]

        return Guest(
            id=self.guest.id if self.guest else None,
            name=self.name_input.text().strip(),
            guest_type=self.type_input.currentText(),
            invitation_status="Visszajelzett",
            attendance_status=self.attendance_input.currentText(),
            attends_dinner=self.dinner_input.isChecked(),
            notes=self.notes_input.toPlainText().strip(),
            preference_ids=preference_ids,
        )


class GuestDialog(QDialog):
    def __init__(
        self,
        parent=None,
        guest: Guest | None = None,
        members=None,
        tables=None,
        preferences=None,
    ) -> None:
        super().__init__(parent)

        self.guest = guest
        self.members = list(members or [])
        self.tables = tables or []
        self.preferences = preferences or []

        self.setWindowTitle(
            "Meghívott szerkesztése"
            if guest
            else "Új meghívott"
        )
        self.resize(780, 860)
        self.setMinimumSize(700, 700)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(18)

        title = QLabel(self.windowTitle())
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.entry_mode = QComboBox()
        self.entry_mode.addItems(("Személy", "Család"))
        self.entry_mode.currentTextChanged.connect(
            self._update_mode
        )

        self.family_name_input = QLineEdit()
        self.family_name_input.setPlaceholderText(
            "Például: Kovács család"
        )

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            "Kapcsolattartó vagy fő meghívott neve"
        )

        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()

        self.type_input = QComboBox()
        self.type_input.addItems(("Felnőtt", "Gyermek"))

        self.invitation_status_input = QComboBox()
        self.invitation_status_input.addItems(
            ("Tervezett", "Meghívó elküldve", "Visszajelzett")
        )

        self.attendance_input = QComboBox()
        self.attendance_input.addItems(
            ("Válaszra vár", "Részt vesz", "Nem vesz részt")
        )

        self.dinner_input = QCheckBox("Részt vesz a vacsorán")
        self.dinner_input.setChecked(True)

        self.table_input = QComboBox()
        self.table_input.addItem("Nincs asztal", None)
        for table in self.tables:
            self.table_input.addItem(
                f"{table.name} ({table.capacity} fő)",
                table.id,
            )

        self.preferences_list = QListWidget()
        self.preferences_list.setMinimumHeight(180)

        for preference in self.preferences:
            item = QListWidgetItem(
                f"{preference['category']}: {preference['name']}"
            )
            item.setData(Qt.UserRole, preference["id"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.preferences_list.addItem(item)

        self.notes_input = QTextEdit()
        self.notes_input.setMinimumHeight(80)

        base_card = QFrame()
        base_card.setObjectName("contentCard")
        base_layout = QVBoxLayout(base_card)
        base_title = QLabel("Alapadatok")
        base_title.setObjectName("sectionTitle")
        base_layout.addWidget(base_title)

        form = QFormLayout()
        form.addRow("Bejegyzés típusa", self.entry_mode)
        self.family_name_label = QLabel("Család neve")
        form.addRow(
            self.family_name_label,
            self.family_name_input,
        )
        form.addRow("Fő meghívott neve *", self.name_input)
        form.addRow("E-mail", self.email_input)
        form.addRow("Telefon", self.phone_input)
        form.addRow("Vendég típusa", self.type_input)
        form.addRow("Meghívás", self.invitation_status_input)
        form.addRow("Részvétel", self.attendance_input)
        form.addRow("Vacsora", self.dinner_input)
        form.addRow("Asztal", self.table_input)
        form.addRow(
            "Étrend / érzékenység / allergia",
            self.preferences_list,
        )
        form.addRow("Megjegyzés", self.notes_input)
        base_layout.addLayout(form)
        layout.addWidget(base_card)

        self.family_card = QFrame()
        self.family_card.setObjectName("contentCard")
        family_layout = QVBoxLayout(self.family_card)

        family_header = QHBoxLayout()
        family_title = QLabel("További családtagok")
        family_title.setObjectName("sectionTitle")

        add_member = QPushButton("+ Családtag")
        add_member.setObjectName("primaryButton")
        add_member.clicked.connect(self._add_member)

        remove_member = QPushButton("Eltávolítás")
        remove_member.setObjectName("dangerButton")
        remove_member.clicked.connect(self._remove_member)

        family_header.addWidget(family_title)
        family_header.addStretch()
        family_header.addWidget(add_member)
        family_header.addWidget(remove_member)

        self.members_table = QTableWidget(0, 5)
        self.members_table.setHorizontalHeaderLabels(
            ["Név", "Típus", "Részvétel", "Vacsora", "Index"]
        )
        self.members_table.setColumnHidden(4, True)
        self.members_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self.members_table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        self.members_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        self.members_table.doubleClicked.connect(
            self._edit_member
        )

        family_layout.addLayout(family_header)
        family_layout.addWidget(self.members_table)
        layout.addWidget(self.family_card)
        layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        footer = QFrame()
        footer.setObjectName("dialogFooter")
        footer.setMinimumHeight(72)
        footer.setStyleSheet(
            """
            QFrame#dialogFooter {
                background: #FFFFFF;
                border-top: 1px solid #E7E8EE;
            }
            """
        )

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(22, 14, 22, 14)
        footer_layout.setSpacing(10)

        cancel = QPushButton("Mégse")
        cancel.setObjectName("secondaryButton")
        cancel.setMinimumWidth(110)
        cancel.clicked.connect(self.reject)

        save = QPushButton("Mentés")
        save.setObjectName("primaryButton")
        save.setMinimumWidth(120)
        save.setDefault(True)
        save.setAutoDefault(True)
        save.clicked.connect(self._save)

        footer_layout.addStretch()
        footer_layout.addWidget(cancel)
        footer_layout.addWidget(save)

        root.addWidget(footer, 0)

        if guest:
            self._load_guest(guest)

        self._update_mode(self.entry_mode.currentText())
        self._refresh_members()

    def _update_mode(self, mode: str) -> None:
        is_family = mode == "Család"

        self.family_name_label.setVisible(is_family)
        self.family_name_input.setVisible(is_family)
        self.family_card.setVisible(is_family)

    def _load_guest(self, guest: Guest) -> None:
        self.entry_mode.setCurrentText(
            "Család"
            if guest.family_name or self.members
            else "Személy"
        )
        self.family_name_input.setText(guest.family_name)
        self.name_input.setText(guest.name)
        self.email_input.setText(guest.email)
        self.phone_input.setText(guest.phone)
        self.type_input.setCurrentText(guest.guest_type)
        self.invitation_status_input.setCurrentText(
            guest.invitation_status
        )
        self.attendance_input.setCurrentText(
            guest.attendance_status
        )
        self.dinner_input.setChecked(guest.attends_dinner)
        self.notes_input.setPlainText(guest.notes)

        table_index = self.table_input.findData(guest.table_id)
        if table_index >= 0:
            self.table_input.setCurrentIndex(table_index)

        for index in range(self.preferences_list.count()):
            item = self.preferences_list.item(index)
            if item.data(Qt.UserRole) in guest.preference_ids:
                item.setCheckState(Qt.Checked)

    def _add_member(self) -> None:
        dialog = PersonDialog(
            self,
            preferences=self.preferences,
        )
        if dialog.exec():
            self.members.append(dialog.get_guest())
            self._refresh_members()

    def _edit_member(self) -> None:
        row = self.members_table.currentRow()
        if row < 0:
            return

        index = int(self.members_table.item(row, 4).text())
        member = self.members[index]

        dialog = PersonDialog(
            self,
            member,
            self.preferences,
        )

        if dialog.exec():
            self.members[index] = dialog.get_guest()
            self._refresh_members()

    def _remove_member(self) -> None:
        row = self.members_table.currentRow()
        if row < 0:
            QMessageBox.information(
                self,
                "Nincs kiválasztás",
                "Válassz ki egy családtagot.",
            )
            return

        index = int(self.members_table.item(row, 4).text())
        del self.members[index]
        self._refresh_members()

    def _refresh_members(self) -> None:
        self.members_table.setRowCount(len(self.members))

        for row, member in enumerate(self.members):
            values = (
                member.name,
                member.guest_type,
                member.attendance_status,
                "Igen" if member.attends_dinner else "Nem",
                str(row),
            )

            for column, value in enumerate(values):
                self.members_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

    def _save(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                "Hiányzó név",
                "A fő meghívott neve kötelező.",
            )
            return

        if (
            self.entry_mode.currentText() == "Család"
            and not self.family_name_input.text().strip()
        ):
            QMessageBox.warning(
                self,
                "Hiányzó családnév",
                "Család típusnál add meg a család nevét.",
            )
            return

        self.accept()

    def get_guest(self) -> Guest:
        preference_ids = [
            self.preferences_list.item(index).data(Qt.UserRole)
            for index in range(self.preferences_list.count())
            if self.preferences_list.item(index).checkState()
            == Qt.Checked
        ]

        is_family = self.entry_mode.currentText() == "Család"

        return Guest(
            id=self.guest.id if self.guest else None,
            name=self.name_input.text().strip(),
            email=self.email_input.text().strip(),
            phone=self.phone_input.text().strip(),
            guest_type=self.type_input.currentText(),
            invitation_status=self.invitation_status_input.currentText(),
            attendance_status=self.attendance_input.currentText(),
            attends_dinner=self.dinner_input.isChecked(),
            table_id=self.table_input.currentData(),
            family_name=(
                self.family_name_input.text().strip()
                if is_family
                else ""
            ),
            notes=self.notes_input.toPlainText().strip(),
            preference_ids=preference_ids,
        )

    def get_members(self) -> list[Guest]:
        if self.entry_mode.currentText() != "Család":
            return []
        return self.members
