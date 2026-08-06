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
        header = workbook.add_format(
            {
                "bold": True,
                "font_color": "white",
                "bg_color": "#6B4EA0",
                "border": 1,
            }
        )
        cell = workbook.add_format(
            {"border": 1, "valign": "top"}
        )
        wrap = workbook.add_format(
            {
                "border": 1,
                "valign": "top",
                "text_wrap": True,
            }
        )

        seating = workbook.add_worksheet("Ültetési rend")
        catering = workbook.add_worksheet("Catering")
        unassigned = workbook.add_worksheet("Asztal nélkül")

        columns = [
            "Asztal",
            "Név",
            "Típus",
            "Vacsora",
            "Étrend / allergia",
            "Megjegyzés",
        ]
        for sheet in (seating, catering):
            for col, value in enumerate(columns):
                sheet.write(0, col, value, header)

        table_map = {table.id: table for table in tables}
        row = 1
        catering_row = 1
        for guest in sorted(
            [g for g in guests if g.table_id is not None],
            key=lambda g: (
                table_map[g.table_id].name,
                g.name,
            ),
        ):
            table = table_map[guest.table_id]
            preferences = ", ".join(
                preference_map[pref_id]
                for pref_id in guest.preference_ids
                if pref_id in preference_map
            )
            values = [
                table.name,
                guest.name,
                guest.guest_type,
                "Igen" if guest.attends_dinner else "Nem",
                preferences,
                guest.seating_notes or guest.notes,
            ]
            for col, value in enumerate(values):
                seating.write(
                    row,
                    col,
                    value,
                    wrap if col in (4, 5) else cell,
                )
            row += 1
            if guest.attends_dinner:
                for col, value in enumerate(values):
                    catering.write(
                        catering_row,
                        col,
                        value,
                        wrap if col in (4, 5) else cell,
                    )
                catering_row += 1

        unassigned_headers = [
            "Név",
            "Típus",
            "Csoport",
            "Étrend / allergia",
        ]
        for col, value in enumerate(unassigned_headers):
            unassigned.write(0, col, value, header)
        for row_index, guest in enumerate(
            [g for g in guests if g.table_id is None],
            start=1,
        ):
            preferences = ", ".join(
                preference_map[pref_id]
                for pref_id in guest.preference_ids
                if pref_id in preference_map
            )
            values = [
                guest.name,
                guest.guest_type,
                guest.family_name,
                preferences,
            ]
            for col, value in enumerate(values):
                unassigned.write(
                    row_index,
                    col,
                    value,
                    wrap if col == 3 else cell,
                )

        for sheet in (seating, catering):
            sheet.freeze_panes(1, 0)
            sheet.autofilter(0, 0, max(row - 1, 1), 5)
            sheet.set_column("A:A", 24)
            sheet.set_column("B:B", 25)
            sheet.set_column("C:D", 16)
            sheet.set_column("E:F", 38)
        unassigned.set_column("A:A", 25)
        unassigned.set_column("B:C", 18)
        unassigned.set_column("D:D", 40)

        workbook.close()
        return destination
