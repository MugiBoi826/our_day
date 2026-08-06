from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class AssignGuestsDialog(QDialog):
    def __init__(self, parent=None, guests=None, group_name: str = "") -> None:
        super().__init__(parent)
        self.guests = guests or []
        self.setWindowTitle("Meglévő személyek hozzáadása")
        self.resize(560, 640)
        self.setMinimumSize(500, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        title = QLabel("Meglévő személyek hozzáadása")
        title.setObjectName("pageTitle")
        description = QLabel(
            f"Válaszd ki, kik kerüljenek a(z) „{group_name}” csoportba."
            if group_name else "Válaszd ki a csoporthoz rendelendő személyeket."
        )
        description.setObjectName("pageSubtitle")
        description.setWordWrap(True)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Keresés név szerint...")
        self.search_input.textChanged.connect(self._apply_filter)

        self.guest_list = QListWidget()
        self.guest_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.guest_list.itemChanged.connect(self._update_selection_label)

        for guest in self.guests:
            details = [guest.guest_type, guest.attendance_status]
            if guest.family_name:
                details.append(guest.family_name)
            item = QListWidgetItem(f"{guest.name}\n{' • '.join(details)}")
            item.setData(Qt.UserRole, guest.id)
            item.setData(Qt.UserRole + 1, guest.name.lower())
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.guest_list.addItem(item)

        self.selection_label = QLabel("0 személy kiválasztva")
        self.selection_label.setObjectName("pageSubtitle")

        actions = QHBoxLayout()
        select_all = QPushButton("Mind kijelölése")
        select_all.setObjectName("secondaryButton")
        select_all.clicked.connect(self._select_all_visible)
        clear_all = QPushButton("Kijelölés törlése")
        clear_all.setObjectName("secondaryButton")
        clear_all.clicked.connect(self._clear_selection)
        actions.addWidget(select_all)
        actions.addWidget(clear_all)
        actions.addStretch()

        footer = QHBoxLayout()
        cancel = QPushButton("Mégse")
        cancel.setObjectName("secondaryButton")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Hozzáadás")
        save.setObjectName("primaryButton")
        save.setDefault(True)
        save.clicked.connect(self._accept)
        footer.addStretch()
        footer.addWidget(cancel)
        footer.addWidget(save)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.search_input)
        layout.addLayout(actions)
        layout.addWidget(self.guest_list, 1)
        layout.addWidget(self.selection_label)
        layout.addLayout(footer)

    def _apply_filter(self, text: str) -> None:
        search = text.strip().lower()
        for index in range(self.guest_list.count()):
            item = self.guest_list.item(index)
            item.setHidden(bool(search) and search not in item.data(Qt.UserRole + 1))

    def _select_all_visible(self) -> None:
        self.guest_list.blockSignals(True)
        for index in range(self.guest_list.count()):
            item = self.guest_list.item(index)
            if not item.isHidden():
                item.setCheckState(Qt.Checked)
        self.guest_list.blockSignals(False)
        self._update_selection_label()

    def _clear_selection(self) -> None:
        self.guest_list.blockSignals(True)
        for index in range(self.guest_list.count()):
            self.guest_list.item(index).setCheckState(Qt.Unchecked)
        self.guest_list.blockSignals(False)
        self._update_selection_label()

    def _update_selection_label(self, *_args) -> None:
        self.selection_label.setText(f"{len(self.get_selected_guest_ids())} személy kiválasztva")

    def _accept(self) -> None:
        if not self.get_selected_guest_ids():
            QMessageBox.information(self, "Nincs kiválasztott személy", "Válassz ki legalább egy személyt.")
            return
        self.accept()

    def get_selected_guest_ids(self) -> list[int]:
        result = []
        for index in range(self.guest_list.count()):
            item = self.guest_list.item(index)
            if item.checkState() == Qt.Checked:
                result.append(int(item.data(Qt.UserRole)))
        return result
