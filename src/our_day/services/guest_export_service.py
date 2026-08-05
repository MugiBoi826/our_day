from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

import xlsxwriter

from our_day.database.connection import get_connection


class GuestExportService:
    SHEET_HEADER_COLOR = "#6B4EA0"
    LIGHT_PURPLE = "#F1ECFA"
    LIGHT_GREEN = "#ECFDF3"
    LIGHT_YELLOW = "#FFF8E1"
    LIGHT_RED = "#FFF0F0"
    BORDER_COLOR = "#DDD9E6"

    @classmethod
    def export(cls, file_path: str | Path) -> None:
        destination = Path(file_path)

        if destination.suffix.lower() != ".xlsx":
            destination = destination.with_suffix(".xlsx")

        data = cls._load_data()

        workbook = xlsxwriter.Workbook(str(destination))

        try:
            formats = cls._create_formats(workbook)
            cls._write_summary_sheet(
                workbook,
                formats,
                data,
            )
            cls._write_guests_sheet(
                workbook,
                formats,
                data,
            )
            cls._write_groups_sheet(
                workbook,
                formats,
                data,
            )
            cls._write_tables_sheet(
                workbook,
                formats,
                data,
            )
            cls._write_preferences_sheet(
                workbook,
                formats,
                data,
            )
            cls._write_rsvp_sheet(
                workbook,
                formats,
                data,
            )
        finally:
            workbook.close()

    @staticmethod
    def _load_data() -> dict:
        with get_connection() as connection:
            guest_rows = connection.execute(
                """
                SELECT
                    g.id,
                    g.name,
                    g.email,
                    g.phone,
                    g.guest_type,
                    g.invitation_status,
                    g.attendance_status,
                    g.attends_dinner,
                    g.dietary_notes,
                    g.table_id,
                    COALESCE(t.name, g.table_name, '') AS table_name,
                    g.invitation_group_id,
                    ig.name AS group_name,
                    ig.group_type,
                    g.family_name,
                    g.parent_guest_id,
                    parent.name AS linked_guest_name,
                    g.is_contact_person,
                    g.response_date,
                    g.notes
                FROM guests g
                LEFT JOIN guest_tables t
                    ON t.id = g.table_id
                LEFT JOIN invitation_groups ig
                    ON ig.id = g.invitation_group_id
                LEFT JOIN guests parent
                    ON parent.id = g.parent_guest_id
                ORDER BY
                    COALESCE(ig.name, ''),
                    g.name COLLATE NOCASE
                """
            ).fetchall()

            group_rows = connection.execute(
                """
                SELECT
                    ig.id,
                    ig.name,
                    ig.group_type,
                    ig.contact_name,
                    ig.email,
                    ig.phone,
                    ig.invitation_sent_date,
                    ig.rsvp_due_date,
                    ig.notes,
                    ig.contact_guest_id,
                    contact_guest.name AS contact_guest_name,
                    COUNT(g.id) AS total,
                    SUM(
                        CASE
                            WHEN g.attendance_status = 'Részt vesz'
                            THEN 1 ELSE 0
                        END
                    ) AS confirmed,
                    SUM(
                        CASE
                            WHEN g.attendance_status = 'Válaszra vár'
                            THEN 1 ELSE 0
                        END
                    ) AS waiting,
                    SUM(
                        CASE
                            WHEN g.attendance_status = 'Nem vesz részt'
                            THEN 1 ELSE 0
                        END
                    ) AS declined
                FROM invitation_groups ig
                LEFT JOIN guests g
                    ON g.invitation_group_id = ig.id
                LEFT JOIN guests contact_guest
                    ON contact_guest.id = ig.contact_guest_id
                GROUP BY
                    ig.id,
                    ig.name,
                    ig.group_type,
                    ig.contact_name,
                    ig.email,
                    ig.phone,
                    ig.invitation_sent_date,
                    ig.rsvp_due_date,
                    ig.notes,
                    ig.contact_guest_id,
                    contact_guest.name
                ORDER BY ig.name COLLATE NOCASE
                """
            ).fetchall()

            table_rows = connection.execute(
                """
                SELECT
                    t.id,
                    t.name,
                    t.capacity,
                    t.notes,
                    COUNT(
                        CASE
                            WHEN g.attendance_status = 'Részt vesz'
                            THEN g.id
                        END
                    ) AS assigned
                FROM guest_tables t
                LEFT JOIN guests g
                    ON g.table_id = t.id
                GROUP BY t.id, t.name, t.capacity, t.notes
                ORDER BY t.name COLLATE NOCASE
                """
            ).fetchall()

            preference_rows = connection.execute(
                """
                SELECT
                    p.id,
                    p.category,
                    p.name,
                    g.id AS guest_id,
                    g.name AS guest_name,
                    g.attendance_status
                FROM guest_preferences p
                LEFT JOIN guest_preference_rel rel
                    ON rel.preference_id = p.id
                LEFT JOIN guests g
                    ON g.id = rel.guest_id
                ORDER BY
                    p.category,
                    p.name COLLATE NOCASE,
                    g.name COLLATE NOCASE
                """
            ).fetchall()

        preferences_by_guest: dict[int, list[str]] = defaultdict(list)
        preference_people: dict[tuple[str, str], list[str]] = defaultdict(list)

        for row in preference_rows:
            if row["guest_id"] is None:
                continue

            label = f'{row["category"]}: {row["name"]}'
            preferences_by_guest[int(row["guest_id"])].append(label)

            if row["attendance_status"] == "Részt vesz":
                preference_people[
                    (str(row["category"]), str(row["name"]))
                ].append(str(row["guest_name"]))

        guests = []
        for row in guest_rows:
            guest_id = int(row["id"])
            guests.append(
                {
                    **dict(row),
                    "preferences": preferences_by_guest.get(
                        guest_id,
                        [],
                    ),
                }
            )

        return {
            "guests": guests,
            "groups": [dict(row) for row in group_rows],
            "tables": [dict(row) for row in table_rows],
            "preference_people": preference_people,
        }

    @classmethod
    def _create_formats(cls, workbook) -> dict:
        return {
            "title": workbook.add_format(
                {
                    "bold": True,
                    "font_size": 20,
                    "font_color": "#3F2D5F",
                }
            ),
            "subtitle": workbook.add_format(
                {
                    "font_color": "#6F6F76",
                    "font_size": 10,
                }
            ),
            "section": workbook.add_format(
                {
                    "bold": True,
                    "font_size": 13,
                    "font_color": "#3F2D5F",
                    "bg_color": cls.LIGHT_PURPLE,
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                }
            ),
            "header": workbook.add_format(
                {
                    "bold": True,
                    "font_color": "#FFFFFF",
                    "bg_color": cls.SHEET_HEADER_COLOR,
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                    "align": "center",
                    "valign": "vcenter",
                    "text_wrap": True,
                }
            ),
            "cell": workbook.add_format(
                {
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                    "valign": "top",
                }
            ),
            "cell_wrap": workbook.add_format(
                {
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                    "valign": "top",
                    "text_wrap": True,
                }
            ),
            "integer": workbook.add_format(
                {
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                    "align": "center",
                    "num_format": "0",
                }
            ),
            "date": workbook.add_format(
                {
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                    "align": "center",
                    "num_format": "yyyy.mm.dd.",
                }
            ),
            "kpi_label": workbook.add_format(
                {
                    "bold": True,
                    "font_color": "#6F6F76",
                    "bg_color": "#F8F7FB",
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                    "align": "center",
                }
            ),
            "kpi_value": workbook.add_format(
                {
                    "bold": True,
                    "font_size": 18,
                    "font_color": "#3F2D5F",
                    "bg_color": "#FFFFFF",
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                    "align": "center",
                }
            ),
            "success": workbook.add_format(
                {
                    "font_color": "#067647",
                    "bg_color": cls.LIGHT_GREEN,
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                }
            ),
            "warning": workbook.add_format(
                {
                    "font_color": "#9A6700",
                    "bg_color": cls.LIGHT_YELLOW,
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                }
            ),
            "danger": workbook.add_format(
                {
                    "font_color": "#B42318",
                    "bg_color": cls.LIGHT_RED,
                    "border": 1,
                    "border_color": cls.BORDER_COLOR,
                }
            ),
        }

    @staticmethod
    def _as_excel_date(value):
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        return datetime.fromisoformat(str(value))

    @classmethod
    def _write_title(
        cls,
        worksheet,
        formats,
        title: str,
        subtitle: str,
        last_column: int,
    ) -> None:
        worksheet.merge_range(
            0,
            0,
            0,
            last_column,
            title,
            formats["title"],
        )
        worksheet.merge_range(
            1,
            0,
            1,
            last_column,
            subtitle,
            formats["subtitle"],
        )
        worksheet.set_row(0, 28)
        worksheet.set_row(1, 20)

    @classmethod
    def _write_summary_sheet(
        cls,
        workbook,
        formats,
        data,
    ) -> None:
        worksheet = workbook.add_worksheet("Összesítés")
        worksheet.hide_gridlines(2)

        guests = data["guests"]
        confirmed = [
            guest
            for guest in guests
            if guest["attendance_status"] == "Részt vesz"
        ]
        waiting = sum(
            1
            for guest in guests
            if guest["attendance_status"] == "Válaszra vár"
        )
        declined = sum(
            1
            for guest in guests
            if guest["attendance_status"] == "Nem vesz részt"
        )
        adults = sum(
            1
            for guest in confirmed
            if guest["guest_type"] == "Felnőtt"
        )
        children = sum(
            1
            for guest in confirmed
            if guest["guest_type"] == "Gyermek"
        )
        dinner = sum(
            1
            for guest in confirmed
            if guest["attends_dinner"]
        )
        unassigned = sum(
            1
            for guest in confirmed
            if guest["table_id"] is None
        )
        special = sum(
            1
            for guest in confirmed
            if guest["preferences"]
        )

        cls._write_title(
            worksheet,
            formats,
            "Our Day – vendégösszesítés",
            "Automatikusan generált esküvői vendéglista és statisztika",
            5,
        )

        kpis = (
            ("Tervezett", len(guests)),
            ("Részt vesz", len(confirmed)),
            ("Válaszra vár", waiting),
            ("Nem vesz részt", declined),
            ("Felnőtt", adults),
            ("Gyermek", children),
            ("Vacsorázik", dinner),
            ("Speciális igény", special),
            ("Nincs asztala", unassigned),
        )

        for index, (label, value) in enumerate(kpis):
            row = 3 + (index // 3) * 2
            column = (index % 3) * 2
            worksheet.write(
                row,
                column,
                label,
                formats["kpi_label"],
            )
            worksheet.write(
                row + 1,
                column,
                value,
                formats["kpi_value"],
            )

        answered = len(confirmed) + declined
        response_rate = (
            answered / len(guests)
            if guests
            else 0
        )

        worksheet.write(
            10,
            0,
            "RSVP-válaszadási arány",
            formats["section"],
        )
        worksheet.write_number(
            11,
            0,
            response_rate,
            workbook.add_format(
                {
                    "num_format": "0%",
                    "font_size": 16,
                    "bold": True,
                    "font_color": "#5B3F8C",
                }
            ),
        )

        worksheet.set_column("A:A", 23)
        worksheet.set_column("B:B", 4)
        worksheet.set_column("C:C", 23)
        worksheet.set_column("D:D", 4)
        worksheet.set_column("E:E", 23)
        worksheet.set_column("F:F", 4)
        worksheet.freeze_panes(3, 0)

    @classmethod
    def _write_guests_sheet(
        cls,
        workbook,
        formats,
        data,
    ) -> None:
        worksheet = workbook.add_worksheet("Vendégek")
        worksheet.hide_gridlines(2)

        headers = (
            "Meghívási csoport",
            "Csoport típusa",
            "Név",
            "Felnőtt / gyermek",
            "Meghívás állapota",
            "RSVP",
            "Vacsora",
            "Asztal",
            "Kapcsolattartó",
            "Kapcsolódó személy",
            "Telefon",
            "E-mail",
            "Étrend / érzékenység / allergia",
            "Válasz dátuma",
            "Megjegyzés",
        )

        cls._write_title(
            worksheet,
            formats,
            "Teljes vendéglista",
            "A lista szűrhető és nyomtatható.",
            len(headers) - 1,
        )

        header_row = 3
        for column, header in enumerate(headers):
            worksheet.write(
                header_row,
                column,
                header,
                formats["header"],
            )

        for row_index, guest in enumerate(
            data["guests"],
            start=header_row + 1,
        ):
            values = (
                guest["group_name"] or "Csoport nélkül",
                guest["group_type"] or "—",
                guest["name"],
                guest["guest_type"],
                guest["invitation_status"],
                guest["attendance_status"],
                "Igen" if guest["attends_dinner"] else "Nem",
                guest["table_name"] or "—",
                "Igen" if guest["is_contact_person"] else "Nem",
                guest["linked_guest_name"] or "—",
                guest["phone"] or "",
                guest["email"] or "",
                ", ".join(guest["preferences"]) or "—",
                guest["response_date"] or "",
                guest["notes"] or "",
            )

            for column, value in enumerate(values):
                cell_format = (
                    formats["cell_wrap"]
                    if column in (12, 14)
                    else formats["cell"]
                )
                worksheet.write(
                    row_index,
                    column,
                    value,
                    cell_format,
                )

        last_row = header_row + max(len(data["guests"]), 1)
        worksheet.autofilter(
            header_row,
            0,
            last_row,
            len(headers) - 1,
        )
        worksheet.freeze_panes(header_row + 1, 2)
        worksheet.set_column("A:A", 23)
        worksheet.set_column("B:B", 17)
        worksheet.set_column("C:C", 24)
        worksheet.set_column("D:D", 18)
        worksheet.set_column("E:F", 18)
        worksheet.set_column("G:G", 11)
        worksheet.set_column("H:H", 18)
        worksheet.set_column("I:J", 18)
        worksheet.set_column("K:L", 22)
        worksheet.set_column("M:M", 38)
        worksheet.set_column("N:N", 16)
        worksheet.set_column("O:O", 35)

        worksheet.conditional_format(
            header_row + 1,
            5,
            last_row,
            5,
            {
                "type": "text",
                "criteria": "containing",
                "value": "Részt vesz",
                "format": formats["success"],
            },
        )
        worksheet.conditional_format(
            header_row + 1,
            5,
            last_row,
            5,
            {
                "type": "text",
                "criteria": "containing",
                "value": "Válaszra vár",
                "format": formats["warning"],
            },
        )
        worksheet.conditional_format(
            header_row + 1,
            5,
            last_row,
            5,
            {
                "type": "text",
                "criteria": "containing",
                "value": "Nem vesz részt",
                "format": formats["danger"],
            },
        )

    @classmethod
    def _write_groups_sheet(
        cls,
        workbook,
        formats,
        data,
    ) -> None:
        worksheet = workbook.add_worksheet("Csoportok")
        worksheet.hide_gridlines(2)

        headers = (
            "Csoport",
            "Típus",
            "Kapcsolattartó",
            "Telefon",
            "E-mail",
            "Meghívó kiküldve",
            "RSVP-határidő",
            "Összesen",
            "Részt vesz",
            "Válaszra vár",
            "Nem vesz részt",
            "Megjegyzés",
        )

        cls._write_title(
            worksheet,
            formats,
            "Meghívási csoportok",
            "Családok, párok, társaságok és RSVP-állapotuk.",
            len(headers) - 1,
        )

        header_row = 3
        for column, header in enumerate(headers):
            worksheet.write(
                header_row,
                column,
                header,
                formats["header"],
            )

        for row_index, group in enumerate(
            data["groups"],
            start=header_row + 1,
        ):
            contact_name = (
                group["contact_guest_name"]
                or group["contact_name"]
                or "—"
            )

            values = (
                group["name"],
                group["group_type"],
                contact_name,
                group["phone"] or "",
                group["email"] or "",
                group["invitation_sent_date"] or "",
                group["rsvp_due_date"] or "",
                group["total"] or 0,
                group["confirmed"] or 0,
                group["waiting"] or 0,
                group["declined"] or 0,
                group["notes"] or "",
            )

            for column, value in enumerate(values):
                worksheet.write(
                    row_index,
                    column,
                    value,
                    (
                        formats["cell_wrap"]
                        if column == 11
                        else formats["cell"]
                    ),
                )

        last_row = header_row + max(len(data["groups"]), 1)
        worksheet.autofilter(
            header_row,
            0,
            last_row,
            len(headers) - 1,
        )
        worksheet.freeze_panes(header_row + 1, 1)
        worksheet.set_column("A:A", 25)
        worksheet.set_column("B:B", 19)
        worksheet.set_column("C:C", 24)
        worksheet.set_column("D:E", 22)
        worksheet.set_column("F:G", 17)
        worksheet.set_column("H:K", 14)
        worksheet.set_column("L:L", 35)

    @classmethod
    def _write_tables_sheet(
        cls,
        workbook,
        formats,
        data,
    ) -> None:
        worksheet = workbook.add_worksheet("Asztalok")
        worksheet.hide_gridlines(2)

        headers = (
            "Asztal",
            "Férőhely",
            "Hozzárendelve",
            "Szabad hely",
            "Állapot",
            "Megjegyzés",
        )

        cls._write_title(
            worksheet,
            formats,
            "Asztalok és kihasználtság",
            "A részt vevő vendégek alapján számolva.",
            len(headers) - 1,
        )

        header_row = 3
        for column, header in enumerate(headers):
            worksheet.write(
                header_row,
                column,
                header,
                formats["header"],
            )

        for row_index, table in enumerate(
            data["tables"],
            start=header_row + 1,
        ):
            assigned = int(table["assigned"] or 0)
            capacity = int(table["capacity"])
            remaining = capacity - assigned

            if remaining < 0:
                status = "Túlfoglalt"
            elif remaining == 0:
                status = "Megtelt"
            else:
                status = "Van szabad hely"

            values = (
                table["name"],
                capacity,
                assigned,
                remaining,
                status,
                table["notes"] or "",
            )

            for column, value in enumerate(values):
                worksheet.write(
                    row_index,
                    column,
                    value,
                    formats["cell"],
                )

        last_row = header_row + max(len(data["tables"]), 1)
        worksheet.autofilter(
            header_row,
            0,
            last_row,
            len(headers) - 1,
        )
        worksheet.freeze_panes(header_row + 1, 1)
        worksheet.set_column("A:A", 24)
        worksheet.set_column("B:D", 16)
        worksheet.set_column("E:E", 18)
        worksheet.set_column("F:F", 35)

        worksheet.conditional_format(
            header_row + 1,
            4,
            last_row,
            4,
            {
                "type": "text",
                "criteria": "containing",
                "value": "Túlfoglalt",
                "format": formats["danger"],
            },
        )

    @classmethod
    def _write_preferences_sheet(
        cls,
        workbook,
        formats,
        data,
    ) -> None:
        worksheet = workbook.add_worksheet("Étkezési igények")
        worksheet.hide_gridlines(2)

        headers = (
            "Kategória",
            "Megnevezés",
            "Érintett vendégek száma",
            "Vendégek",
        )

        cls._write_title(
            worksheet,
            formats,
            "Étkezési igények és allergiák",
            "Csak a visszaigazolt vendégek jelennek meg.",
            len(headers) - 1,
        )

        header_row = 3
        for column, header in enumerate(headers):
            worksheet.write(
                header_row,
                column,
                header,
                formats["header"],
            )

        rows = sorted(
            data["preference_people"].items(),
            key=lambda item: (
                item[0][0],
                item[0][1],
            ),
        )

        for row_index, ((category, name), people) in enumerate(
            rows,
            start=header_row + 1,
        ):
            values = (
                category,
                name,
                len(people),
                ", ".join(people),
            )

            for column, value in enumerate(values):
                worksheet.write(
                    row_index,
                    column,
                    value,
                    (
                        formats["cell_wrap"]
                        if column == 3
                        else formats["cell"]
                    ),
                )

        last_row = header_row + max(len(rows), 1)
        worksheet.autofilter(
            header_row,
            0,
            last_row,
            len(headers) - 1,
        )
        worksheet.freeze_panes(header_row + 1, 0)
        worksheet.set_column("A:A", 18)
        worksheet.set_column("B:B", 25)
        worksheet.set_column("C:C", 24)
        worksheet.set_column("D:D", 55)

    @classmethod
    def _write_rsvp_sheet(
        cls,
        workbook,
        formats,
        data,
    ) -> None:
        worksheet = workbook.add_worksheet("RSVP")
        worksheet.hide_gridlines(2)

        headers = (
            "Csoport",
            "Típus",
            "RSVP-határidő",
            "Összesen",
            "Részt vesz",
            "Válaszra vár",
            "Nem vesz részt",
            "Állapot",
        )

        cls._write_title(
            worksheet,
            formats,
            "RSVP-követés",
            "Csoportonkénti válaszadási állapot.",
            len(headers) - 1,
        )

        header_row = 3
        for column, header in enumerate(headers):
            worksheet.write(
                header_row,
                column,
                header,
                formats["header"],
            )

        today = datetime.now().date()

        for row_index, group in enumerate(
            data["groups"],
            start=header_row + 1,
        ):
            due_value = group["rsvp_due_date"]
            waiting = int(group["waiting"] or 0)

            if waiting == 0:
                status = "Lezárt"
            elif not due_value:
                status = "Nincs határidő"
            else:
                due_date = datetime.fromisoformat(
                    str(due_value)
                ).date()
                days_left = (due_date - today).days

                if days_left < 0:
                    status = f"{abs(days_left)} napja lejárt"
                elif days_left == 0:
                    status = "Ma esedékes"
                elif days_left <= 10:
                    status = f"{days_left} nap múlva"
                else:
                    status = "Folyamatban"

            values = (
                group["name"],
                group["group_type"],
                due_value or "",
                group["total"] or 0,
                group["confirmed"] or 0,
                waiting,
                group["declined"] or 0,
                status,
            )

            for column, value in enumerate(values):
                worksheet.write(
                    row_index,
                    column,
                    value,
                    formats["cell"],
                )

        last_row = header_row + max(len(data["groups"]), 1)
        worksheet.autofilter(
            header_row,
            0,
            last_row,
            len(headers) - 1,
        )
        worksheet.freeze_panes(header_row + 1, 1)
        worksheet.set_column("A:A", 26)
        worksheet.set_column("B:B", 19)
        worksheet.set_column("C:C", 17)
        worksheet.set_column("D:G", 15)
        worksheet.set_column("H:H", 20)

        worksheet.conditional_format(
            header_row + 1,
            7,
            last_row,
            7,
            {
                "type": "text",
                "criteria": "containing",
                "value": "lejárt",
                "format": formats["danger"],
            },
        )
        worksheet.conditional_format(
            header_row + 1,
            7,
            last_row,
            7,
            {
                "type": "text",
                "criteria": "containing",
                "value": "nap múlva",
                "format": formats["warning"],
            },
        )
