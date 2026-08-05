from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatisticCard(QFrame):
    VARIANTS = {
        "neutral": {
            "background": "#FFFFFF",
            "border": "#E7E8EE",
            "value": "#262626",
            "title": "#777777",
        },
        "warning": {
            "background": "#FFF8E1",
            "border": "#E9D58A",
            "value": "#9A6700",
            "title": "#7A5B00",
        },
        "success": {
            "background": "#ECFDF3",
            "border": "#A7E3C0",
            "value": "#067647",
            "title": "#176B47",
        },
        "danger": {
            "background": "#FFF0F0",
            "border": "#E8B6B6",
            "value": "#B42318",
            "title": "#8F2D24",
        },
        "accent": {
            "background": "#F1ECFA",
            "border": "#D8C8EF",
            "value": "#5B3F8C",
            "title": "#6B5790",
        },
    }

    def __init__(
        self,
        title: str,
        value: str,
        variant: str = "neutral",
    ) -> None:
        super().__init__()

        self.setObjectName("statCard")
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("statTitle")

        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

        self.set_variant(variant)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_variant(self, variant: str) -> None:
        colors = self.VARIANTS.get(
            variant,
            self.VARIANTS["neutral"],
        )

        self.setStyleSheet(
            f"""
            QFrame#statCard {{
                background: {colors["background"]};
                border: 1px solid {colors["border"]};
                border-radius: 14px;
            }}

            QLabel#statTitle {{
                background: transparent;
                color: {colors["title"]};
                font-size: 13px;
            }}

            QLabel#statValue {{
                background: transparent;
                color: {colors["value"]};
                font-size: 24px;
                font-weight: 700;
            }}
            """
        )
