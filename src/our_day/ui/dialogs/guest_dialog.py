from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from our_day.models.guest import Guest


class GuestDialog(QDialog):
    def __init__(
        self,
        parent=None,
        guest: Guest | None = None,
        companion: Guest | None = None,
        tables=None,
    ) -> None:
        super().__init__(parent)

        self.guest = guest
        self.companion = companion
        self.tables = tables or []

        self.setWindowTitle(
            "Meghívott szerkesztése" if guest else "Új meghívott"
        )
        self.resize(760, 820)
        self.setMinimumSize(680, 680)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 26, 28, 24)
        content_layout.setSpacing(18)

        title = QLabel(
            "Meghívott szerkesztése" if guest else "Új meghívott"
        )
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Rögzítsd a meghívott és az esetleges kísérő adatait."
        )
        subtitle.setObjectName("pageSubtitle")

        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("A meghívott teljes neve")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("pelda@email.hu")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+36 30 123 4567")

        self.guest_type_input = QComboBox()
        self.guest_type_input.addItems(("Felnőtt", "Gyermek"))

        self.invitation_status_input = QComboBox()
        self.invitation_status_input.addItems(
            ("Tervezett", "Meghívó elküldve", "Visszajelzett")
        )

        self.attendance_status_input = QComboBox()
        self.attendance_status_input.addItems(
            ("Válaszra vár", "Részt vesz", "Nem vesz részt")
        )

        self.attends_dinner_input = QCheckBox("Részt vesz a vacsorán")
        self.attends_dinner_input.setChecked(True)

        self.dietary_input = QTextEdit()
        self.dietary_input.setPlaceholderText(
            "Ételérzékenység, allergia vagy egyéb étkezési igény"
        )
        self.dietary_input.setMinimumHeight(75)

        self.table_input = QComboBox()
        self.table_input.addItem("Nincs asztal", None)

        for table in self.tables:
            self.table_input.addItem(
                f"{table.name} ({table.capacity} fő)",
                table.id,
            )

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Egyéb megjegyzés")
        self.notes_input.setMinimumHeight(75)

        guest_card = self._create_card(
            "Meghívott adatai",
            (
                ("Név *", self.name_input),
                ("Vendég típusa", self.guest_type_input),
                ("E-mail-cím", self.email_input),
                ("Telefonszám", self.phone_input),
                ("Meghívás állapota", self.invitation_status_input),
                ("Részvétel", self.attendance_status_input),
                ("Vacsora", self.attends_dinner_input),
                ("Ételérzékenység / igény", self.dietary_input),
                ("Asztal", self.table_input),
                ("Megjegyzés", self.notes_input),
            ),
        )

        content_layout.addWidget(guest_card)

        self.has_companion_input = QCheckBox("Kísérővel érkezhet")
        self.has_companion_input.toggled.connect(
            self._toggle_companion_section
        )

        content_layout.addWidget(self.has_companion_input)

        self.companion_card = QFrame()
        self.companion_card.setObjectName("contentCard")

        companion_layout = QVBoxLayout(self.companion_card)
        companion_layout.setContentsMargins(22, 20, 22, 20)
        companion_layout.setSpacing(12)

        companion_title = QLabel("Kísérő adatai")
        companion_title.setObjectName("sectionTitle")

        companion_form = QFormLayout()
        companion_form.setSpacing(12)

        self.companion_name_input = QLineEdit()
        self.companion_name_input.setPlaceholderText(
            "A kísérő teljes neve"
        )

        self.companion_type_input = QComboBox()
        self.companion_type_input.addItems(("Felnőtt", "Gyermek"))

        self.companion_email_input = QLineEdit()
        self.companion_email_input.setPlaceholderText("pelda@email.hu")

        self.companion_phone_input = QLineEdit()
        self.companion_phone_input.setPlaceholderText("+36 30 123 4567")

        self.companion_attendance_input = QComboBox()
        self.companion_attendance_input.addItems(
            ("Válaszra vár", "Részt vesz", "Nem vesz részt")
        )

        self.companion_dinner_input = QCheckBox(
            "Részt vesz a vacsorán"
        )
        self.companion_dinner_input.setChecked(True)

        self.companion_dietary_input = QTextEdit()
        self.companion_dietary_input.setPlaceholderText(
            "Ételérzékenység vagy egyéb étkezési igény"
        )
        self.companion_dietary_input.setMinimumHeight(70)

        for label, widget in (
            ("Név *", self.companion_name_input),
            ("Vendég típusa", self.companion_type_input),
            ("E-mail-cím", self.companion_email_input),
            ("Telefonszám", self.companion_phone_input),
            ("Részvétel", self.companion_attendance_input),
            ("Vacsora", self.companion_dinner_input),
            ("Ételérzékenység / igény", self.companion_dietary_input),
        ):
            companion_form.addRow(label, widget)

        companion_layout.addWidget(companion_title)
        companion_layout.addLayout(companion_form)

        self.companion_card.setVisible(False)
        content_layout.addWidget(self.companion_card)
        content_layout.addStretch()

        scroll_area.setWidget(content)
        root_layout.addWidget(scroll_area, 1)

        footer = QFrame()
        footer.setObjectName("dialogFooter")
        footer.setStyleSheet(
            """
            QFrame#dialogFooter {
                background: #FFFFFF;
                border-top: 1px solid #E7E8EE;
            }
            """
        )
        footer.setMinimumHeight(70)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(22, 14, 22, 14)
        footer_layout.setSpacing(10)

        cancel_button = QPushButton("Mégse")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.setMinimumWidth(110)
        cancel_button.clicked.connect(self.reject)

        save_button = QPushButton("Mentés")
        save_button.setObjectName("primaryButton")
        save_button.setMinimumWidth(120)
        save_button.setDefault(True)
        save_button.setAutoDefault(True)
        save_button.clicked.connect(self._validate_and_accept)

        footer_layout.addStretch()
        footer_layout.addWidget(cancel_button)
        footer_layout.addWidget(save_button)

        root_layout.addWidget(footer, 0)

        if guest:
            self._load_guest(guest)

        if companion:
            self.has_companion_input.setChecked(True)
            self._load_companion(companion)

    @staticmethod
    def _create_card(
        title: str,
        fields: tuple[tuple[str, QWidget], ...],
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("contentCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")

        form = QFormLayout()
        form.setSpacing(12)

        for label, widget in fields:
            form.addRow(label, widget)

        layout.addWidget(title_label)
        layout.addLayout(form)

        return card

    def _toggle_companion_section(self, checked: bool) -> None:
        self.companion_card.setVisible(checked)

    def _load_guest(self, guest: Guest) -> None:
        self.name_input.setText(guest.name)
        self.email_input.setText(guest.email)
        self.phone_input.setText(guest.phone)
        self.guest_type_input.setCurrentText(guest.guest_type)
        self.invitation_status_input.setCurrentText(
            guest.invitation_status
        )
        self.attendance_status_input.setCurrentText(
            guest.attendance_status
        )
        self.attends_dinner_input.setChecked(guest.attends_dinner)
        self.dietary_input.setPlainText(guest.dietary_notes)
        self.notes_input.setPlainText(guest.notes)

        table_index = self.table_input.findData(guest.table_id)
        if table_index >= 0:
            self.table_input.setCurrentIndex(table_index)

    def _load_companion(self, companion: Guest) -> None:
        self.companion_name_input.setText(companion.name)
        self.companion_type_input.setCurrentText(
            companion.guest_type
        )
        self.companion_email_input.setText(companion.email)
        self.companion_phone_input.setText(companion.phone)
        self.companion_attendance_input.setCurrentText(
            companion.attendance_status
        )
        self.companion_dinner_input.setChecked(
            companion.attends_dinner
        )
        self.companion_dietary_input.setPlainText(
            companion.dietary_notes
        )

    def _validate_and_accept(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                "Hiányzó név",
                "A meghívott nevének megadása kötelező.",
            )
            self.name_input.setFocus()
            return

        if (
            self.has_companion_input.isChecked()
            and not self.companion_name_input.text().strip()
        ):
            QMessageBox.warning(
                self,
                "Hiányzó név",
                "A kísérő nevének megadása kötelező.",
            )
            self.companion_name_input.setFocus()
            return

        self.accept()

    def get_guest(self) -> Guest:
        table_id = self.table_input.currentData()

        return Guest(
            id=self.guest.id if self.guest else None,
            name=self.name_input.text().strip(),
            email=self.email_input.text().strip(),
            phone=self.phone_input.text().strip(),
            guest_type=self.guest_type_input.currentText(),
            invitation_status=self.invitation_status_input.currentText(),
            attendance_status=self.attendance_status_input.currentText(),
            has_plus_one=self.has_companion_input.isChecked(),
            plus_one_name=(
                self.companion_name_input.text().strip()
                if self.has_companion_input.isChecked()
                else ""
            ),
            attends_dinner=self.attends_dinner_input.isChecked(),
            dietary_notes=self.dietary_input.toPlainText().strip(),
            table_name="",
            table_id=table_id,
            parent_guest_id=(
                self.guest.parent_guest_id if self.guest else None
            ),
            notes=self.notes_input.toPlainText().strip(),
        )

    def get_companion(self) -> Guest | None:
        if not self.has_companion_input.isChecked():
            return None

        return Guest(
            id=self.companion.id if self.companion else None,
            name=self.companion_name_input.text().strip(),
            email=self.companion_email_input.text().strip(),
            phone=self.companion_phone_input.text().strip(),
            guest_type=self.companion_type_input.currentText(),
            invitation_status=self.invitation_status_input.currentText(),
            attendance_status=self.companion_attendance_input.currentText(),
            has_plus_one=False,
            plus_one_name="",
            attends_dinner=self.companion_dinner_input.isChecked(),
            dietary_notes=self.companion_dietary_input.toPlainText().strip(),
            table_name="",
            table_id=self.table_input.currentData(),
            parent_guest_id=(
                self.guest.id if self.guest else None
            ),
            notes="",
        )
