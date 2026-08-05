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

    def __init__(self, entry_repo, task_repo, guest_repo, wedding_repo) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.task_repo = task_repo
        self.guest_repo = guest_repo
        self.wedding_repo = wedding_repo

        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 30, 36, 30)
        layout.setSpacing(20)

        hero_card = QFrame()
        hero_card.setObjectName("weddingHero")
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(28, 24, 28, 24)
        hero_layout.setSpacing(20)

        hero_text = QVBoxLayout()
        hero_text.setSpacing(5)

        self.wedding_title = QLabel("Our Day")
        self.wedding_title.setObjectName("weddingTitle")

        self.wedding_countdown = QLabel(
            "Add meg az esküvő alapadatait a Beállításokban."
        )
        self.wedding_countdown.setObjectName("weddingCountdown")

        self.wedding_location = QLabel()
        self.wedding_location.setObjectName("weddingLocation")
        self.wedding_location.setWordWrap(True)

        hero_text.addWidget(self.wedding_title)
        hero_text.addWidget(self.wedding_countdown)
        hero_text.addWidget(self.wedding_location)

        add_button = QPushButton("+ Új szolgáltatás")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.create_entry_requested.emit)

        hero_layout.addLayout(hero_text, 1)
        hero_layout.addWidget(add_button)
        layout.addWidget(hero_card)

        finance_grid = QGridLayout()
        finance_grid.setHorizontalSpacing(18)
        finance_grid.setVerticalSpacing(18)

        self.total_card = StatisticCard("Teljes tervezett költség", "0 Ft", "accent")
        self.deposit_card = StatisticCard("Aktív foglalók", "0 Ft", "warning")
        self.paid_card = StatisticCard("Rendezett összegek", "0 Ft", "success")
        self.remaining_card = StatisticCard("Fennmaradó összeg", "0 Ft", "danger")
        self.budget_card = StatisticCard("Keretből rendelkezésre áll", "—", "accent")
        self.tasks_card = StatisticCard("Elvégzett feladatok", "0 / 0")
        self.guests_card = StatisticCard("Visszaigazolt létszám", "0 / 0")
        self.dinner_card = StatisticCard("Vacsorázó vendégek", "0", "success")

        cards = (
            self.total_card,
            self.deposit_card,
            self.paid_card,
            self.remaining_card,
            self.budget_card,
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

    def _refresh_wedding_header(self, wedding) -> None:
        if wedding is None:
            self.wedding_title.setText("Our Day")
            self.wedding_countdown.setText(
                "Add meg az esküvő alapadatait a Beállításokban."
            )
            self.wedding_location.clear()
            return

        self.wedding_title.setText(wedding.couple_name or "Our Day")

        if wedding.wedding_date:
            days = (wedding.wedding_date - date.today()).days
            formatted_date = wedding.wedding_date.strftime("%Y.%m.%d.")

            if days > 1:
                countdown = f"Még {days} nap az esküvőig • {formatted_date}"
            elif days == 1:
                countdown = f"Holnap lesz az esküvő! • {formatted_date}"
            elif days == 0:
                countdown = f"Ma van a nagy nap! • {formatted_date}"
            else:
                countdown = (
                    f"Az esküvő {abs(days)} napja volt • {formatted_date}"
                )
        else:
            countdown = "Az esküvő dátuma még nincs megadva."

        self.wedding_countdown.setText(countdown)

        location_parts = [
            part
            for part in (wedding.venue_name, wedding.venue_address)
            if part
        ]
        self.wedding_location.setText(" • ".join(location_parts))

    def refresh(self) -> None:
        financial = self.entry_repo.get_financial_summary("Szolgáltatás")
        task_summary = self.task_repo.get_summary()
        guest_summary = self.guest_repo.get_summary()
        wedding = self.wedding_repo.get_active()

        self._refresh_wedding_header(wedding)
        self.total_card.set_value(format_currency(financial["total"]))
        self.deposit_card.set_value(format_currency(financial["deposits"]))
        self.paid_card.set_value(format_currency(financial["paid"]))
        self.remaining_card.set_value(format_currency(financial["remaining"]))

        if wedding and wedding.budget_amount > 0:
            available_budget = wedding.budget_amount - financial["total"]
            self.budget_card.set_value(format_currency(available_budget))
            self.budget_card.set_variant(
                "danger" if available_budget < 0 else "success"
            )
        else:
            self.budget_card.set_value("Nincs megadva")
            self.budget_card.set_variant("neutral")

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
