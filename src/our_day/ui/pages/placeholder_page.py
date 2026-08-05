from PySide6.QtWidgets import QLabel,QVBoxLayout,QWidget
class PlaceholderPage(QWidget):
    def __init__(self,title,description):
        super().__init__(); l=QVBoxLayout(self); l.setContentsMargins(36,30,36,30)
        t=QLabel(title); t.setObjectName("pageTitle"); d=QLabel(description); d.setObjectName("pageSubtitle")
        l.addWidget(t); l.addWidget(d); l.addStretch()
