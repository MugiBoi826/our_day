from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup,QFrame,QLabel,QPushButton,QVBoxLayout


class Sidebar(QFrame):
    page_selected = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,24,20,24)
        title = QLabel("Our Day")
        title.setObjectName("appTitle")
        layout.addWidget(title)
        group = QButtonGroup(self)
        group.setExclusive(True)
        for index, text in enumerate(("Áttekintés","Bejegyzések","Szolgáltatások","Feladatok","Meghívottak","Statisztikák","Beállítások")):
            button = QPushButton(text)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self.page_selected.emit(i))
            group.addButton(button)
            layout.addWidget(button)
            if index == 0: button.setChecked(True)
        layout.addStretch()
