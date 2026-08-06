from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from our_day.services.formatting import format_currency
from our_day.ui.widgets.statistic_card import StatisticCard


class DashboardPage(QWidget):
    create_service_requested = Signal()
    create_task_requested = Signal()
    create_guest_requested = Signal()
    create_group_requested = Signal()
    export_guests_requested = Signal()
    backup_requested = Signal()
    open_page_requested = Signal(int)

    def __init__(
        self,
        entry_repo,
        task_repo,
        guest_repo,
        group_repo,
        wedding_repo,
    ) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self.task_repo = task_repo
        self.guest_repo = guest_repo
        self.group_repo = group_repo
        self.wedding_repo = wedding_repo

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(34, 28, 34, 32)
        layout.setSpacing(20)

        layout.addWidget(self._create_hero())
        layout.addLayout(self._create_primary_kpis())
        layout.addWidget(self._create_alert_section())
        layout.addWidget(self._create_timeline_section())
        layout.addLayout(self._create_secondary_sections())
        layout.addWidget(self._create_quick_actions())

        scroll.setWidget(content)
        root_layout.addWidget(scroll)

    def _create_hero(self) -> QFrame:
        hero = QFrame()
        hero.setObjectName("weddingHero")

        layout = QHBoxLayout(hero)
        layout.setContentsMargins(30, 26, 30, 26)
        layout.setSpacing(24)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)

        self.wedding_title = QLabel("Our Day")
        self.wedding_title.setObjectName("weddingTitle")

        self.wedding_countdown = QLabel(
            "Add meg az esküvő alapadatait a Beállításokban."
        )
        self.wedding_countdown.setObjectName("weddingCountdown")

        self.wedding_location = QLabel()
        self.wedding_location.setObjectName("weddingLocation")
        self.wedding_location.setWordWrap(True)

        self.wedding_progress = QLabel()
        self.wedding_progress.setObjectName("weddingProgress")
        self.wedding_progress.setWordWrap(True)

        text_layout.addWidget(self.wedding_title)
        text_layout.addWidget(self.wedding_countdown)
        text_layout.addWidget(self.wedding_location)
        text_layout.addSpacing(4)
        text_layout.addWidget(self.wedding_progress)

        actions = QVBoxLayout()
        actions.setSpacing(10)

        service_button = QPushButton("+ Új szolgáltatás")
        service_button.setObjectName("primaryButton")
        service_button.clicked.connect(
            self.create_service_requested.emit
        )

        task_button = QPushButton("+ Új feladat")
        task_button.setObjectName("secondaryButton")
        task_button.clicked.connect(
            self.create_task_requested.emit
        )

        actions.addWidget(service_button)
        actions.addWidget(task_button)
        actions.addStretch()

        layout.addLayout(text_layout, 1)
        layout.addLayout(actions)

        return hero

    def _create_primary_kpis(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        self.budget_card = StatisticCard(
            "Költségkeret",
            "Nincs megadva",
            "accent",
        )
        self.planned_card = StatisticCard(
            "Tervezett költség",
            "0 Ft",
            "accent",
        )
        self.paid_card = StatisticCard(
            "Eddig rendezve",
            "0 Ft",
            "success",
        )
        self.remaining_card = StatisticCard(
            "Még fizetendő",
            "0 Ft",
            "danger",
        )
        self.tasks_card = StatisticCard(
            "Feladatok",
            "0 / 0",
        )
        self.guests_card = StatisticCard(
            "Visszaigazolt vendégek",
            "0 / 0",
        )

        cards = (
            self.budget_card,
            self.planned_card,
            self.paid_card,
            self.remaining_card,
            self.tasks_card,
            self.guests_card,
        )

        for index, card in enumerate(cards):
            grid.addWidget(card, index // 3, index % 3)

        return grid

    def _create_alert_section(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("contentCard")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()

        title = QLabel("Figyelmet igényel")
        title.setObjectName("sectionTitle")

        self.alert_count = QLabel("0")
        self.alert_count.setObjectName("alertBadge")
        self.alert_count.setAlignment(Qt.AlignCenter)
        self.alert_count.setMinimumWidth(30)

        header.addWidget(title)
        header.addWidget(self.alert_count)
        header.addStretch()

        self.alerts_layout = QVBoxLayout()
        self.alerts_layout.setSpacing(8)

        layout.addLayout(header)
        layout.addLayout(self.alerts_layout)

        return frame

    def _create_timeline_section(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("contentCard")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()

        title = QLabel("Következő események")
        title.setObjectName("sectionTitle")

        subtitle = QLabel(
            "Feladatok, fizetések és RSVP-határidők egy közös listában."
        )
        subtitle.setObjectName("pageSubtitle")

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header.addLayout(title_box)
        header.addStretch()

        self.timeline_layout = QVBoxLayout()
        self.timeline_layout.setSpacing(8)

        layout.addLayout(header)
        layout.addLayout(self.timeline_layout)

        return frame

    def _create_secondary_sections(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        guest_frame = QFrame()
        guest_frame.setObjectName("contentCard")
        guest_layout = QVBoxLayout(guest_frame)
        guest_layout.setContentsMargins(22, 20, 22, 20)
        guest_layout.setSpacing(10)

        guest_title = QLabel("Vendégek")
        guest_title.setObjectName("sectionTitle")

        self.guest_summary = QLabel()
        self.guest_summary.setWordWrap(True)
        self.guest_summary.setObjectName("dashboardDetail")

        guest_button = QPushButton("Meghívottkezelő megnyitása")
        guest_button.setObjectName("secondaryButton")
        guest_button.clicked.connect(
            lambda: self.open_page_requested.emit(4)
        )

        guest_layout.addWidget(guest_title)
        guest_layout.addWidget(self.guest_summary)
        guest_layout.addStretch()
        guest_layout.addWidget(guest_button)

        seating_frame = QFrame()
        seating_frame.setObjectName("contentCard")
        seating_layout = QVBoxLayout(seating_frame)
        seating_layout.setContentsMargins(22, 20, 22, 20)
        seating_layout.setSpacing(10)

        seating_title = QLabel("Ültetés")
        seating_title.setObjectName("sectionTitle")

        self.seating_summary = QLabel()
        self.seating_summary.setWordWrap(True)
        self.seating_summary.setObjectName("dashboardDetail")

        statistics_button = QPushButton("Statisztikák megnyitása")
        statistics_button.setObjectName("secondaryButton")
        statistics_button.clicked.connect(
            lambda: self.open_page_requested.emit(5)
        )

        seating_layout.addWidget(seating_title)
        seating_layout.addWidget(self.seating_summary)
        seating_layout.addStretch()
        seating_layout.addWidget(statistics_button)

        grid.addWidget(guest_frame, 0, 0)
        grid.addWidget(seating_frame, 0, 1)

        return grid

    def _create_quick_actions(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("contentCard")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QLabel("Gyors műveletek")
        title.setObjectName("sectionTitle")

        buttons = QGridLayout()
        buttons.setHorizontalSpacing(10)
        buttons.setVerticalSpacing(10)

        actions = (
            ("Új szolgáltatás", self.create_service_requested.emit),
            ("Új feladat", self.create_task_requested.emit),
            ("Új vendég", self.create_guest_requested.emit),
            ("Új csoport", self.create_group_requested.emit),
            ("Vendéglista export", self.export_guests_requested.emit),
            ("Biztonsági mentés", self.backup_requested.emit),
        )

        for index, (text, callback) in enumerate(actions):
            button = QPushButton(text)
            button.setObjectName(
                "primaryButton"
                if index < 2
                else "secondaryButton"
            )
            button.setMinimumHeight(42)
            button.clicked.connect(callback)
            buttons.addWidget(button, index // 3, index % 3)

        layout.addWidget(title)
        layout.addLayout(buttons)

        return frame

    def refresh(self) -> None:
        financial = self.entry_repo.get_financial_summary(
            "Szolgáltatás"
        )
        task_summary = self.task_repo.get_summary()
        guest_summary = self.guest_repo.get_summary()
        wedding = self.wedding_repo.get_active()

        self._refresh_wedding_header(
            wedding,
            financial,
            task_summary,
            guest_summary,
        )

        self.planned_card.set_value(
            format_currency(financial["total"])
        )
        self.paid_card.set_value(
            format_currency(financial["paid"])
        )
        self.remaining_card.set_value(
            format_currency(financial["remaining"])
        )

        if wedding and wedding.budget_amount > 0:
            available = (
                wedding.budget_amount
                - financial["total"]
            )
            self.budget_card.set_value(
                format_currency(wedding.budget_amount)
            )
            self.budget_card.set_variant(
                "danger"
                if available < 0
                else "accent"
            )
        else:
            self.budget_card.set_value("Nincs megadva")
            self.budget_card.set_variant("neutral")

        self.tasks_card.set_value(
            f"{task_summary['done']} / "
            f"{task_summary['total']} kész"
        )
        self.guests_card.set_value(
            f"{guest_summary['confirmed']} / "
            f"{guest_summary['planned']} fő"
        )

        self._refresh_alerts(
            financial,
            task_summary,
            guest_summary,
        )
        self._refresh_timeline()
        self._refresh_guest_summary(guest_summary)
        self._refresh_seating_summary(guest_summary)

    def _refresh_wedding_header(
        self,
        wedding,
        financial,
        task_summary,
        guest_summary,
    ) -> None:
        if wedding is None:
            self.wedding_title.setText("Our Day")
            self.wedding_countdown.setText(
                "Add meg az esküvő alapadatait a Beállításokban."
            )
            self.wedding_location.clear()
            self.wedding_progress.setText(
                "A dashboard az alapadatok megadása után "
                "személyre szabott szervezési központtá válik."
            )
            return

        self.wedding_title.setText(
            wedding.couple_name or "Our Day"
        )

        if wedding.wedding_date:
            days = (
                wedding.wedding_date
                - date.today()
            ).days
            formatted_date = (
                wedding.wedding_date
                .strftime("%Y.%m.%d.")
            )

            if days > 1:
                countdown = (
                    f"Még {days} nap az esküvőig "
                    f"• {formatted_date}"
                )
            elif days == 1:
                countdown = (
                    f"Holnap lesz az esküvő! "
                    f"• {formatted_date}"
                )
            elif days == 0:
                countdown = (
                    f"Ma van a nagy nap! "
                    f"• {formatted_date}"
                )
            else:
                countdown = (
                    f"Az esküvő {abs(days)} napja volt "
                    f"• {formatted_date}"
                )
        else:
            countdown = (
                "Az esküvő dátuma még nincs megadva."
            )

        self.wedding_countdown.setText(countdown)

        location_parts = [
            value
            for value in (
                wedding.venue_name,
                wedding.venue_address,
            )
            if value
        ]
        self.wedding_location.setText(
            " • ".join(location_parts)
        )

        budget_text = (
            format_currency(wedding.budget_amount)
            if wedding.budget_amount > 0
            else "nincs megadva"
        )

        self.wedding_progress.setText(
            f"Keret: {budget_text} • "
            f"Tervezett költség: "
            f"{format_currency(financial['total'])} • "
            f"{task_summary['open']} nyitott feladat • "
            f"{guest_summary['waiting']} válaszra váró vendég"
        )

    def _refresh_alerts(
        self,
        financial,
        task_summary,
        guest_summary,
    ) -> None:
        self._clear_layout(self.alerts_layout)

        alerts: list[tuple[str, str, str]] = []

        overdue_tasks = [
            task
            for task in self.task_repo.get_upcoming(3650)
            if task.due_date
            and task.due_date < date.today()
        ]
        if overdue_tasks:
            alerts.append(
                (
                    "danger",
                    f"{len(overdue_tasks)} lejárt feladat",
                    "A feladatlista azonnali ellenőrzést igényel.",
                )
            )

        payment_deadlines = (
            self.entry_repo.get_upcoming_deadlines(10)
        )
        overdue_payments = [
            item
            for item in payment_deadlines
            if item["date"] < date.today()
        ]
        upcoming_payments = [
            item
            for item in payment_deadlines
            if item["date"] >= date.today()
        ]

        if overdue_payments:
            alerts.append(
                (
                    "danger",
                    f"{len(overdue_payments)} lejárt fizetés",
                    "Ellenőrizd a szolgáltatások pénzügyi állapotát.",
                )
            )
        if upcoming_payments:
            alerts.append(
                (
                    "warning",
                    f"{len(upcoming_payments)} fizetés 10 napon belül",
                    "Készülj fel a közelgő foglalókra vagy végösszegekre.",
                )
            )

        overdue_rsvp = [
            group
            for group in self.group_repo.get_rsvp_overview()
            if group["waiting"] > 0
            and group["rsvp_due_date"]
            and group["rsvp_due_date"] < date.today()
        ]
        if overdue_rsvp:
            alerts.append(
                (
                    "danger",
                    f"{len(overdue_rsvp)} lejárt RSVP-csoport",
                    "A csoportokban még vannak válaszra váró vendégek.",
                )
            )

        unassigned = (
            self.guest_repo
            .get_unassigned_confirmed_count()
        )
        if unassigned:
            alerts.append(
                (
                    "warning",
                    f"{unassigned} visszaigazolt vendégnek nincs asztala",
                    "Az ültetési rend még nem teljes.",
                )
            )

        overbooked = sum(
            1
            for table in self.guest_repo.get_table_summary()
            if table["remaining"] < 0
        )
        if overbooked:
            alerts.append(
                (
                    "danger",
                    f"{overbooked} túlfoglalt asztal",
                    "Módosítsd az asztalkiosztást vagy a kapacitást.",
                )
            )

        if guest_summary["waiting"]:
            alerts.append(
                (
                    "info",
                    f"{guest_summary['waiting']} vendég válaszára várunk",
                    "Érdemes rövidesen emlékeztetőt küldeni.",
                )
            )

        self.alert_count.setText(str(len(alerts)))

        if not alerts:
            self.alert_count.setVisible(False)
            label = QLabel(
                "Minden rendben – jelenleg nincs sürgős figyelmeztetés."
            )
            label.setObjectName("emptyState")
            self.alerts_layout.addWidget(label)
            return

        self.alert_count.setVisible(True)

        for variant, title, description in alerts[:7]:
            self.alerts_layout.addWidget(
                self._alert_widget(
                    variant,
                    title,
                    description,
                )
            )

    def _refresh_timeline(self) -> None:
        self._clear_layout(self.timeline_layout)

        items: list[dict] = []

        for deadline in (
            self.entry_repo
            .get_upcoming_deadlines(45)
        ):
            items.append(
                {
                    "date": deadline["date"],
                    "type": "Fizetés",
                    "title": deadline["title"],
                    "detail": deadline["kind"],
                }
            )

        for task in self.task_repo.get_upcoming(45):
            items.append(
                {
                    "date": task.due_date,
                    "type": "Feladat",
                    "title": task.title,
                    "detail": task.priority,
                }
            )

        for group in self.group_repo.get_rsvp_overview():
            if (
                group["waiting"] > 0
                and group["rsvp_due_date"]
                and group["rsvp_due_date"]
                <= date.today().fromordinal(
                    date.today().toordinal() + 45
                )
            ):
                items.append(
                    {
                        "date": group["rsvp_due_date"],
                        "type": "RSVP",
                        "title": group["name"],
                        "detail": (
                            f"{group['waiting']} válaszra vár"
                        ),
                    }
                )

        items.sort(
            key=lambda item: (
                item["date"],
                item["type"],
                item["title"],
            )
        )

        if not items:
            label = QLabel(
                "Nincs közelgő esemény a következő 45 napban."
            )
            label.setObjectName("emptyState")
            self.timeline_layout.addWidget(label)
            return

        for item in items[:10]:
            self.timeline_layout.addWidget(
                self._timeline_widget(item)
            )

    def _refresh_guest_summary(
        self,
        guest_summary,
    ) -> None:
        total = guest_summary["planned"]
        confirmed = guest_summary["confirmed"]
        response_rate = (
            round(
                (
                    confirmed
                    + guest_summary["declined"]
                )
                / total
                * 100
            )
            if total
            else 0
        )

        self.guest_summary.setText(
            f"<b>{confirmed} fő vesz részt</b><br>"
            f"{guest_summary['confirmed_adults']} felnőtt, "
            f"{guest_summary['confirmed_children']} gyermek<br>"
            f"{guest_summary['dinner']} vacsorázó • "
            f"{guest_summary['waiting']} válaszra vár<br>"
            f"Válaszadási arány: {response_rate}%"
        )

    def _refresh_seating_summary(
        self,
        guest_summary,
    ) -> None:
        tables = self.guest_repo.get_table_summary()
        capacity = sum(
            table["capacity"]
            for table in tables
        )
        assigned = sum(
            table["assigned"]
            for table in tables
        )
        unassigned = (
            self.guest_repo
            .get_unassigned_confirmed_count()
        )
        overbooked = sum(
            1
            for table in tables
            if table["remaining"] < 0
        )

        self.seating_summary.setText(
            f"<b>{assigned} / {capacity} hely kiosztva</b><br>"
            f"{len(tables)} rögzített asztal<br>"
            f"{unassigned} visszaigazolt vendég asztal nélkül<br>"
            f"{overbooked} túlfoglalt asztal"
        )

    @staticmethod
    def _alert_widget(
        variant: str,
        title: str,
        description: str,
    ) -> QFrame:
        colors = {
            "danger": (
                "#FFF0F0",
                "#E8B6B6",
                "#9B2525",
            ),
            "warning": (
                "#FFF8E1",
                "#E9D58A",
                "#7A5B00",
            ),
            "info": (
                "#F1ECFA",
                "#D8C8EF",
                "#5B3F8C",
            ),
        }
        background, border, color = colors[variant]

        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background: {background};
                border: 1px solid {border};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
                color: {color};
            }}
            """
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-weight: 700;"
        )

        description_label = QLabel(description)
        description_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(description_label)

        return frame

    @staticmethod
    def _timeline_widget(item: dict) -> QFrame:
        due_date = item["date"]
        days = (due_date - date.today()).days

        if days < 0:
            status = f"{abs(days)} napja lejárt"
            color = "#B42318"
        elif days == 0:
            status = "Ma"
            color = "#9A6700"
        elif days == 1:
            status = "Holnap"
            color = "#9A6700"
        else:
            status = f"{days} nap múlva"
            color = "#5B3F8C"

        frame = QFrame()
        frame.setObjectName("timelineItem")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        date_label = QLabel(
            due_date.strftime("%m.%d.")
        )
        date_label.setObjectName("timelineDate")
        date_label.setFixedWidth(54)
        date_label.setAlignment(Qt.AlignCenter)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)

        title_label = QLabel(
            f"{item['type']} • {item['title']}"
        )
        title_label.setStyleSheet(
            "font-weight: 650; background: transparent;"
        )

        detail_label = QLabel(item["detail"])
        detail_label.setObjectName("pageSubtitle")

        status_label = QLabel(status)
        status_label.setStyleSheet(
            f"""
            color: {color};
            font-weight: 650;
            background: transparent;
            """
        )

        text_layout.addWidget(title_label)
        text_layout.addWidget(detail_label)

        layout.addWidget(date_label)
        layout.addLayout(text_layout, 1)
        layout.addWidget(status_label)

        return frame

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()
