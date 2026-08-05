from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatisticCard(QFrame):
    def __init__(self, title: str, value: str) -> None:
        super().__init__()
        self.setObjectName("statCard")
        self.setMinimumHeight(110)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,18,20,18)
        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)
