from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class SeatingPreferenceDialog(QDialog):
    def __init__(
        self,
        parent,
        guest,
        all_guests,
        preferences,
    ) -> None:
        super().__init__(parent)
        self.guest = guest
        self.setWindowTitle(
            f"Ültetési preferenciák – {guest.name}"
        )
        self.resize(560, 620)

        layout = QVBoxLayout(self)
        title = QLabel(guest.name)
        title.setObjectName("pageTitle")
        helper = QLabel(
            "Add meg, kik mellett szeretne ülni, "
            "és kitől legyen távol."
        )
        helper.setObjectName("pageSubtitle")
        helper.setWordWrap(True)

        tabs = QTabWidget()
        self.with_list = self._make_list(
            all_guests,
            preferences.get("with", []),
        )
        self.avoid_list = self._make_list(
            all_guests,
            preferences.get("avoid", []),
        )
        tabs.addTab(
            self._wrap(self.with_list),
            "Üljön mellette",
        )
        tabs.addTab(
            self._wrap(self.avoid_list),
            "Ne üljön mellette",
        )

        self.accessibility = QCheckBox(
            "Könnyen megközelíthető hely szükséges"
        )
        self.accessibility.setChecked(
            guest.accessibility_required
        )
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "További ültetési megjegyzés"
        )
        self.notes.setPlainText(guest.seating_notes)

        buttons = QHBoxLayout()
        cancel = QPushButton("Mégse")
        cancel.setObjectName("secondaryButton")
        save = QPushButton("Mentés")
        save.setObjectName("primaryButton")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)

        layout.addWidget(title)
        layout.addWidget(helper)
        layout.addWidget(tabs, 1)
        layout.addWidget(self.accessibility)
        layout.addWidget(self.notes)
        layout.addLayout(buttons)

    def _make_list(self, guests, selected_ids):
        widget = QListWidget()
        for guest in guests:
            if guest.id == self.guest.id:
                continue
            item = QListWidgetItem(guest.name)
            item.setData(Qt.UserRole, guest.id)
            item.setFlags(
                item.flags() | Qt.ItemIsUserCheckable
            )
            item.setCheckState(
                Qt.Checked
                if guest.id in selected_ids
                else Qt.Unchecked
            )
            widget.addItem(item)
        return widget

    @staticmethod
    def _wrap(widget):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(widget)
        return page

    @staticmethod
    def _checked_ids(widget):
        return [
            int(item.data(Qt.UserRole))
            for index in range(widget.count())
            if (
                (item := widget.item(index))
                .checkState() == Qt.Checked
            )
        ]

    def values(self):
        return {
            "with": self._checked_ids(self.with_list),
            "avoid": self._checked_ids(self.avoid_list),
            "notes": self.notes.toPlainText().strip(),
            "accessibility": self.accessibility.isChecked(),
        }
