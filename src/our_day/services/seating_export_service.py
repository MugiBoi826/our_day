from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import xlsxwriter


class SeatingExportService:
    @staticmethod
    def export(
        file_path,
        tables,
        guests,
        preference_map,
    ) -> Path:
        destination = Path(file_path)

        if destination.suffix.lower() != ".xlsx":
            destination = destination.with_suffix(".xlsx")

        workbook = xlsxwriter.Workbook(str(destination))

        formats = SeatingExportService._create_formats(
            workbook
        )

        table_map = {
            table.id: table
            for table in tables
        }

        assigned_guests = [
            guest
            for guest in guests
            if guest.table_id is not None
        ]
        unassigned_guests = [
            guest
            for guest in guests
            if guest.table_id is None
        ]

        SeatingExportService._write_tables_sheet(
            workbook,
            tables,
            assigned_guests,
            table_map,
            preference_map,
            formats,
        )
        SeatingExportService._write_catering_sheet(
            workbook,
            tables,
            assigned_guests,
            preference_map,
            formats,
        )
        SeatingExportService._write_diet_sheet(
            workbook,
            assigned_guests,
            preference_map,
            formats,
        )
        SeatingExportService._write_unassigned_sheet(
            workbook,
            unassigned_guests,
            preference_map,
            formats,
        )

        workbook.close()
        return destination

    @staticmethod
    def _create_formats(workbook) -> dict:
        return {
            "title": workbook.add_format(
                {
                    "bold": True,
                    "font_size": 16,
                    "font_color": "#4F347D",
                    "bottom": 2,
                    "bottom_color": "#6B4EA0",
                }
            ),
            "section": workbook.add_format(
                {
                    "bold": True,
                    "font_size": 12,
                    "font_color": "#4F347D",
                    "bg_color": "#F1ECFA",
                    "border": 1,
                }
            ),
            "header": workbook.add_format(
                {
                    "bold": True,
                    "font_color": "white",
                    "bg_color": "#6B4EA0",
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                }
            ),
            "cell": workbook.add_format(
                {
                    "border": 1,
                    "valign": "top",
                }
            ),
            "center": workbook.add_format(
                {
                    "border": 1,
                    "align": "center",
                    "valign": "top",
                }
            ),
            "wrap": workbook.add_format(
                {
                    "border": 1,
                    "valign": "top",
                    "text_wrap": True,
                }
            ),
            "warning": workbook.add_format(
                {
                    "border": 1,
                    "bg_color": "#FFF8E1",
                    "font_color": "#7A5B00",
                    "text_wrap": True,
                }
            ),
            "danger": workbook.add_format(
                {
                    "border": 1,
                    "bg_color": "#FFF0F0",
                    "font_color": "#B42318",
                    "text_wrap": True,
                }
            ),
            "total_label": workbook.add_format(
                {
                    "bold": True,
                    "bg_color": "#EEEAF5",
                    "border": 1,
                }
            ),
            "total_value": workbook.add_format(
                {
                    "bold": True,
                    "bg_color": "#EEEAF5",
                    "border": 1,
                    "align": "center",
                }
            ),
        }

    @staticmethod
    def _write_tables_sheet(
        workbook,
        tables,
        assigned_guests,
        table_map,
        preference_map,
        formats,
    ) -> None:
        sheet = workbook.add_worksheet("Asztalok")

        sheet.write(
            0,
            0,
            "Ültetési rend – részletes vendéglista",
            formats["title"],
        )

        headers = (
            "Asztal",
            "Sorszám",
            "Vendég neve",
            "Típus",
            "Család / csoport",
            "Vacsorázik",
            "Étrend / allergia",
            "Ültetési megjegyzés",
        )

        for column, value in enumerate(headers):
            sheet.write(
                2,
                column,
                value,
                formats["header"],
            )

        sorted_guests = sorted(
            assigned_guests,
            key=lambda guest: (
                table_map[guest.table_id].name,
                guest.name,
            ),
        )

        table_sequence = defaultdict(int)
        row = 3

        for guest in sorted_guests:
            table = table_map[guest.table_id]
            table_sequence[table.id] += 1

            preferences = SeatingExportService._preferences_text(
                guest,
                preference_map,
            )

            values = (
                table.name,
                table_sequence[table.id],
                guest.name,
                guest.guest_type,
                guest.family_name or "",
                "Igen" if guest.attends_dinner else "Nem",
                preferences,
                guest.seating_notes or guest.notes or "",
            )

            for column, value in enumerate(values):
                cell_format = (
                    formats["wrap"]
                    if column in (4, 6, 7)
                    else (
                        formats["center"]
                        if column in (1, 3, 5)
                        else formats["cell"]
                    )
                )
                sheet.write(
                    row,
                    column,
                    value,
                    cell_format,
                )

            row += 1

        sheet.freeze_panes(3, 0)
        sheet.autofilter(
            2,
            0,
            max(row - 1, 2),
            len(headers) - 1,
        )

        sheet.set_column("A:A", 25)
        sheet.set_column("B:B", 9)
        sheet.set_column("C:C", 26)
        sheet.set_column("D:D", 14)
        sheet.set_column("E:E", 23)
        sheet.set_column("F:F", 12)
        sheet.set_column("G:G", 38)
        sheet.set_column("H:H", 40)

    @staticmethod
    def _write_catering_sheet(
        workbook,
        tables,
        assigned_guests,
        preference_map,
        formats,
    ) -> None:
        sheet = workbook.add_worksheet("Catering")

        sheet.write(
            0,
            0,
            "Catering összesítő asztalonként",
            formats["title"],
        )

        headers = (
            "Asztal",
            "Összes fő",
            "Felnőtt",
            "Gyermek",
            "Vacsorázik",
            "Nem vacsorázik",
            "Speciális étrend / allergia",
            "Kapacitás",
            "Szabad hely",
            "Állapot",
        )

        for column, value in enumerate(headers):
            sheet.write(
                2,
                column,
                value,
                formats["header"],
            )

        guests_by_table = defaultdict(list)

        for guest in assigned_guests:
            guests_by_table[guest.table_id].append(
                guest
            )

        row = 3
        total_guests = 0
        total_adults = 0
        total_children = 0
        total_dinner = 0
        total_no_dinner = 0
        total_capacity = 0

        for table in tables:
            table_guests = guests_by_table[table.id]

            adults = sum(
                guest.guest_type == "Felnőtt"
                for guest in table_guests
            )
            children = sum(
                guest.guest_type == "Gyermek"
                for guest in table_guests
            )
            dinner = sum(
                guest.attends_dinner
                for guest in table_guests
            )
            no_dinner = len(table_guests) - dinner

            preference_counter = Counter()

            for guest in table_guests:
                for preference_id in guest.preference_ids:
                    if preference_id in preference_map:
                        preference_counter[
                            preference_map[preference_id]
                        ] += 1

            preference_summary = ", ".join(
                f"{name}: {count}"
                for name, count in sorted(
                    preference_counter.items()
                )
            )

            free_places = (
                table.capacity
                - len(table_guests)
            )

            if free_places < 0:
                status = "Túlfoglalt"
                status_format = formats["danger"]
            elif free_places == 0:
                status = "Megtelt"
                status_format = formats["warning"]
            else:
                status = "Rendben"
                status_format = formats["cell"]

            values = (
                table.name,
                len(table_guests),
                adults,
                children,
                dinner,
                no_dinner,
                preference_summary,
                table.capacity,
                free_places,
                status,
            )

            for column, value in enumerate(values):
                if column == 6:
                    cell_format = formats["wrap"]
                elif column == 9:
                    cell_format = status_format
                elif column in (1, 2, 3, 4, 5, 7, 8):
                    cell_format = formats["center"]
                else:
                    cell_format = formats["cell"]

                sheet.write(
                    row,
                    column,
                    value,
                    cell_format,
                )

            total_guests += len(table_guests)
            total_adults += adults
            total_children += children
            total_dinner += dinner
            total_no_dinner += no_dinner
            total_capacity += table.capacity
            row += 1

        totals = (
            "Összesen",
            total_guests,
            total_adults,
            total_children,
            total_dinner,
            total_no_dinner,
            "",
            total_capacity,
            total_capacity - total_guests,
            "",
        )

        for column, value in enumerate(totals):
            sheet.write(
                row,
                column,
                value,
                (
                    formats["total_label"]
                    if column in (0, 6, 9)
                    else formats["total_value"]
                ),
            )

        sheet.freeze_panes(3, 0)
        sheet.set_column("A:A", 26)
        sheet.set_column("B:F", 14)
        sheet.set_column("G:G", 46)
        sheet.set_column("H:J", 14)

    @staticmethod
    def _write_diet_sheet(
        workbook,
        assigned_guests,
        preference_map,
        formats,
    ) -> None:
        sheet = workbook.add_worksheet(
            "Étrend összesítő"
        )

        sheet.write(
            0,
            0,
            "Teljes étrendi és allergia összesítő",
            formats["title"],
        )

        summary_headers = (
            "Kategória / igény",
            "Érintett vendégek száma",
            "Vendégek",
        )

        for column, value in enumerate(
            summary_headers
        ):
            sheet.write(
                2,
                column,
                value,
                formats["header"],
            )

        preference_guests = defaultdict(list)

        for guest in assigned_guests:
            if not guest.attends_dinner:
                continue

            for preference_id in guest.preference_ids:
                if preference_id in preference_map:
                    preference_guests[
                        preference_map[preference_id]
                    ].append(guest.name)

        row = 3

        for preference_name, guest_names in sorted(
            preference_guests.items()
        ):
            sheet.write(
                row,
                0,
                preference_name,
                formats["cell"],
            )
            sheet.write(
                row,
                1,
                len(guest_names),
                formats["center"],
            )
            sheet.write(
                row,
                2,
                ", ".join(sorted(guest_names)),
                formats["wrap"],
            )
            row += 1

        if not preference_guests:
            sheet.write(
                row,
                0,
                "Nincs rögzített speciális étrend vagy allergia.",
                formats["warning"],
            )

        sheet.set_column("A:A", 34)
        sheet.set_column("B:B", 22)
        sheet.set_column("C:C", 60)

    @staticmethod
    def _write_unassigned_sheet(
        workbook,
        unassigned_guests,
        preference_map,
        formats,
    ) -> None:
        sheet = workbook.add_worksheet(
            "Asztal nélkül"
        )

        sheet.write(
            0,
            0,
            "Asztalhoz még nem rendelt vendégek",
            formats["title"],
        )

        headers = (
            "Név",
            "Típus",
            "Család / csoport",
            "Vacsorázik",
            "Étrend / allergia",
            "Ültetési megjegyzés",
        )

        for column, value in enumerate(headers):
            sheet.write(
                2,
                column,
                value,
                formats["header"],
            )

        row = 3

        for guest in sorted(
            unassigned_guests,
            key=lambda guest: guest.name,
        ):
            values = (
                guest.name,
                guest.guest_type,
                guest.family_name or "",
                "Igen" if guest.attends_dinner else "Nem",
                SeatingExportService._preferences_text(
                    guest,
                    preference_map,
                ),
                guest.seating_notes or guest.notes or "",
            )

            for column, value in enumerate(values):
                cell_format = (
                    formats["wrap"]
                    if column in (2, 4, 5)
                    else (
                        formats["center"]
                        if column in (1, 3)
                        else formats["cell"]
                    )
                )

                sheet.write(
                    row,
                    column,
                    value,
                    cell_format,
                )

            row += 1

        sheet.freeze_panes(3, 0)
        sheet.set_column("A:A", 27)
        sheet.set_column("B:B", 14)
        sheet.set_column("C:C", 24)
        sheet.set_column("D:D", 13)
        sheet.set_column("E:F", 42)

    @staticmethod
    def _preferences_text(
        guest,
        preference_map,
    ) -> str:
        return ", ".join(
            preference_map[preference_id]
            for preference_id in guest.preference_ids
            if preference_id in preference_map
        )
