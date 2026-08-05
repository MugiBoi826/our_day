from datetime import date

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from our_day.services.formatting import format_currency
from our_day.ui.widgets.statistic_card import StatisticCard


class DashboardPage(QWidget):
    create_entry_requested = Signal()

    def __init__(self, entry_repo, task_repo, guest_repo) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.task_repo = task_repo
        self.guest_repo = guest_repo

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(20)

        header = QHBoxLayout()
        header_text = QVBoxLayout()

        title = QLabel("Áttekintés")
        title.setObjectName("pageTitle")

        subtitle = QLabel(
            "Esküvői tervek, költségek, feladatok és meghívottak egy helyen."
        )
        subtitle.setObjectName("pageSubtitle")

        header_text.addWidget(title)
        header_text.addWidget(subtitle)

        add_button = QPushButton("+ Új szolgáltatás")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.create_entry_requested.emit)

        header.addLayout(header_text)
        header.addStretch()
        header.addWidget(add_button)
        layout.addLayout(header)

        finance_grid = QGridLayout()
        finance_grid.setHorizontalSpacing(18)
        finance_grid.setVerticalSpacing(18)

        self.total_card = StatisticCard("Teljes tervezett költség", "0 Ft", "accent")
        self.deposit_card = StatisticCard("Aktív foglalók", "0 Ft", "warning")
        self.paid_card = StatisticCard("Rendezett összegek", "0 Ft", "success")
        self.remaining_card = StatisticCard("Fennmaradó összeg", "0 Ft", "danger")
        self.tasks_card = StatisticCard("Elvégzett feladatok", "0 / 0")
        self.guests_card = StatisticCard("Visszaigazolt létszám", "0 / 0")
        self.dinner_card = StatisticCard("Vacsorázó vendégek", "0", "success")

        cards = (
            self.total_card,
            self.deposit_card,
            self.paid_card,
            self.remaining_card,
            self.tasks_card,
            self.guests_card,
            self.dinner_card,
        )

        for index, card in enumerate(cards):
            finance_grid.addWidget(card, index // 3, index % 3)

        layout.addLayout(finance_grid)

        guest_card = QFrame()
        guest_card.setObjectName("contentCard")
        guest_layout = QHBoxLayout(guest_card)
        guest_layout.setContentsMargins(24, 18, 24, 18)
        guest_layout.setSpacing(28)

        self.guest_summary_label = QLabel()
        self.guest_summary_label.setWordWrap(True)
        self.guest_summary_label.setStyleSheet(
            "background: transparent; font-size: 15px;"
        )
        guest_layout.addWidget(self.guest_summary_label, 1)
        layout.addWidget(guest_card)

        deadline_card = QFrame()
        deadline_card.setObjectName("contentCard")
        deadline_layout = QVBoxLayout(deadline_card)
        deadline_layout.setContentsMargins(24, 20, 24, 20)

        deadline_title = QLabel("Közelgő határidők")
        deadline_title.setObjectName("sectionTitle")

        self.deadlines = QVBoxLayout()
        self.deadlines.setSpacing(8)

        deadline_layout.addWidget(deadline_title)
        deadline_layout.addLayout(self.deadlines)
        layout.addWidget(deadline_card)
        layout.addStretch()

    def refresh(self) -> None:
        financial = self.entry_repo.get_financial_summary("Szolgáltatás")
        task_summary = self.task_repo.get_summary()
        guest_summary = self.guest_repo.get_summary()

        self.total_card.set_value(format_currency(financial["total"]))
        self.deposit_card.set_value(format_currency(financial["deposits"]))
        self.paid_card.set_value(format_currency(financial["paid"]))
        self.remaining_card.set_value(format_currency(financial["remaining"]))
        self.tasks_card.set_value(
            f"{task_summary['done']} / {task_summary['total']}"
        )
        self.guests_card.set_value(
            f"{guest_summary['confirmed']} / {guest_summary['planned']}"
        )
        self.dinner_card.set_value(str(guest_summary["dinner"]))

        self.guest_summary_label.setText(
            "<b>Meghívottak:</b> "
            f"{guest_summary['planned']} tervezett fő • "
            f"{guest_summary['confirmed']} részt vesz • "
            f"{guest_summary['waiting']} válaszra vár • "
            f"{guest_summary['declined']} nem vesz részt • "
            f"{guest_summary['confirmed_adults']} felnőtt • "
            f"{guest_summary['confirmed_children']} gyermek • "
            f"{guest_summary['dinner']} vacsorázik • "
            f"{guest_summary['not_dinner']} nem vacsorázik"
        )

        self._refresh_deadlines()

    def _refresh_deadlines(self) -> None:
        while self.deadlines.count():
            item = self.deadlines.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        items = [
            (deadline["title"] + " — " + deadline["kind"], deadline["date"])
            for deadline in self.entry_repo.get_upcoming_deadlines()
        ]
        items.extend(
            (task.title + " — Feladat", task.due_date)
            for task in self.task_repo.get_upcoming()
        )

        if not items:
            label = QLabel("Nincs 10 napon belüli vagy lejárt határidő.")
            label.setStyleSheet("color: #6F6F76; background: transparent;")
            self.deadlines.addWidget(label)
            return

        for text, due_date in sorted(items, key=lambda item: item[1]):
            days = (due_date - date.today()).days

            if days < 0:
                status = f"{abs(days)} napja lejárt"
                background = "#FFF0F0"
                border = "#E8B6B6"
                color = "#9B2525"
            elif days == 0:
                status = "Ma esedékes"
                background = "#FFF4E5"
                border = "#E6C58A"
                color = "#8A5A00"
            else:
                status = f"{days} nap múlva"
                background = "#FFF9E8"
                border = "#E8D79A"
                color = "#7B6200"

            label = QLabel(
                f"{text} | {due_date.strftime('%Y.%m.%d.')} | {status}"
            )
            label.setStyleSheet(
                f"""
                QLabel {{
                    padding: 10px;
                    background: {background};
                    color: {color};
                    border: 1px solid {border};
                    border-radius: 8px;
                }}
                """
            )
            self.deadlines.addWidget(label)
