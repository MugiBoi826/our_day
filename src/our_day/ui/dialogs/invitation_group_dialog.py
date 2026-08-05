from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTextEdit, QVBoxLayout, QWidget
)

from our_day.models.invitation_group import InvitationGroup


class InvitationGroupDialog(QDialog):
    def __init__(
        self,
        parent=None,
        group: InvitationGroup | None = None,
        group_members=None,
    ) -> None:
        super().__init__(parent)
        self.group = group
        self.group_members = group_members or []
        self.setWindowTitle("Meghívási csoport szerkesztése" if group else "Új meghívási csoport")
        self.resize(560, 520)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.type_input = QComboBox()
        self.type_input.addItems(("Személy", "Pár", "Család", "Baráti társaság", "Munkahelyi csoport", "Egyéb"))
        self.type_input.currentTextChanged.connect(
            self._update_contact_visibility
        )
        self.contact_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()

        self.contact_guest_label = QLabel("Kapcsolattartó családtag")
        self.contact_guest_input = QComboBox()
        self.contact_guest_input.addItem("Nincs kiválasztva", None)
        for member in self.group_members:
            self.contact_guest_input.addItem(
                member["name"],
                member["id"],
            )

        self.sent_enabled = QCheckBox("Megadva")
        self.sent_date = QDateEdit(QDate.currentDate())
        self.sent_date.setCalendarPopup(True)
        self.sent_date.setDisplayFormat("yyyy.MM.dd.")
        self.sent_date.setEnabled(False)
        self.sent_enabled.toggled.connect(self.sent_date.setEnabled)

        sent_container = QWidget()
        sent_layout = QHBoxLayout(sent_container)
        sent_layout.setContentsMargins(0,0,0,0)
        sent_layout.addWidget(self.sent_enabled)
        sent_layout.addWidget(self.sent_date)

        self.rsvp_enabled = QCheckBox("Megadva")
        self.rsvp_date = QDateEdit(QDate.currentDate())
        self.rsvp_date.setCalendarPopup(True)
        self.rsvp_date.setDisplayFormat("yyyy.MM.dd.")
        self.rsvp_date.setEnabled(False)
        self.rsvp_enabled.toggled.connect(self.rsvp_date.setEnabled)

        rsvp_container = QWidget()
        rsvp_layout = QHBoxLayout(rsvp_container)
        rsvp_layout.setContentsMargins(0,0,0,0)
        rsvp_layout.addWidget(self.rsvp_enabled)
        rsvp_layout.addWidget(self.rsvp_date)

        self.notes_input = QTextEdit()

        form.addRow("Csoport neve *", self.name_input)
        form.addRow("Típus", self.type_input)
        form.addRow(
            self.contact_guest_label,
            self.contact_guest_input,
        )
        self.contact_name_label = QLabel("Kapcsolattartó neve")
        self.email_label = QLabel("Kapcsolattartó e-mail")
        self.phone_label = QLabel("Kapcsolattartó telefon")
        form.addRow(self.contact_name_label, self.contact_input)
        form.addRow(self.email_label, self.email_input)
        form.addRow(self.phone_label, self.phone_input)
        form.addRow("Meghívó kiküldése", sent_container)
        form.addRow("RSVP-határidő", rsvp_container)
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

        if group:
            self._load(group)

        self._update_contact_visibility(
            self.type_input.currentText()
        )

    def _update_contact_visibility(
        self,
        group_type: str,
    ) -> None:
        is_family = group_type == "Család"

        self.contact_guest_label.setVisible(is_family)
        self.contact_guest_input.setVisible(is_family)

        self.contact_name_label.setVisible(is_family)
        self.contact_input.setVisible(is_family)
        self.email_label.setVisible(is_family)
        self.email_input.setVisible(is_family)
        self.phone_label.setVisible(is_family)
        self.phone_input.setVisible(is_family)

        if not is_family:
            self.contact_guest_input.setCurrentIndex(0)

    def _load(self, group: InvitationGroup) -> None:
        self.name_input.setText(group.name)
        self.type_input.setCurrentText(group.group_type)
        self.contact_input.setText(group.contact_name)
        self.email_input.setText(group.email)
        self.phone_input.setText(group.phone)
        self.notes_input.setPlainText(group.notes)
        contact_index = self.contact_guest_input.findData(
            group.contact_guest_id
        )
        if contact_index >= 0:
            self.contact_guest_input.setCurrentIndex(
                contact_index
            )
        if group.invitation_sent_date:
            self.sent_enabled.setChecked(True)
            self.sent_date.setDate(QDate(group.invitation_sent_date.year, group.invitation_sent_date.month, group.invitation_sent_date.day))
        if group.rsvp_due_date:
            self.rsvp_enabled.setChecked(True)
            self.rsvp_date.setDate(QDate(group.rsvp_due_date.year, group.rsvp_due_date.month, group.rsvp_due_date.day))

    def _save(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Hiányzó név", "A csoport neve kötelező.")
            return
        self.accept()

    def _get_date(self, enabled, editor):
        if not enabled.isChecked():
            return None
        value = editor.date()
        return date(value.year(), value.month(), value.day())

    def get_group(self) -> InvitationGroup:
        return InvitationGroup(
            id=self.group.id if self.group else None,
            name=self.name_input.text().strip(),
            group_type=self.type_input.currentText(),
            contact_name=self.contact_input.text().strip(),
            email=self.email_input.text().strip(),
            phone=self.phone_input.text().strip(),
            invitation_sent_date=self._get_date(self.sent_enabled, self.sent_date),
            rsvp_due_date=self._get_date(self.rsvp_enabled, self.rsvp_date),
            notes=self.notes_input.toPlainText().strip(),
            contact_guest_id=(
                self.contact_guest_input.currentData()
                if self.type_input.currentText() == "Család"
                else None
            ),
        )
