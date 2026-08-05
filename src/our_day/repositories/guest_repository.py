from our_day.database.connection import get_connection
from our_day.models.guest import Guest


class GuestRepository:
    FIELDS = """
        g.id, g.name, g.email, g.phone, g.guest_type, g.invitation_status,
        g.attendance_status, g.has_plus_one, g.plus_one_name, g.attends_dinner,
        g.dietary_notes, COALESCE(t.name, g.table_name, '') AS table_name,
        g.table_id, g.parent_guest_id, g.notes
    """

    def list_all(self) -> list[Guest]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self.FIELDS}
                FROM guests g
                LEFT JOIN guest_tables t ON t.id = g.table_id
                ORDER BY
                    CASE WHEN g.parent_guest_id IS NULL THEN 0 ELSE 1 END,
                    g.name COLLATE NOCASE
                """
            ).fetchall()
        return [self._row_to_guest(row) for row in rows]

    def get_by_id(self, guest_id: int) -> Guest | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self.FIELDS}
                FROM guests g
                LEFT JOIN guest_tables t ON t.id = g.table_id
                WHERE g.id=?
                """,
                (guest_id,),
            ).fetchone()
        return self._row_to_guest(row) if row else None

    def get_companion(self, parent_guest_id: int) -> Guest | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self.FIELDS}
                FROM guests g
                LEFT JOIN guest_tables t ON t.id = g.table_id
                WHERE g.parent_guest_id=?
                LIMIT 1
                """,
                (parent_guest_id,),
            ).fetchone()
        return self._row_to_guest(row) if row else None

    def create_with_companion(
        self,
        guest: Guest,
        companion: Guest | None = None,
    ) -> int:
        with get_connection() as connection:
            guest_id = self._insert(connection, guest)
            if companion:
                companion.parent_guest_id = guest_id
                self._insert(connection, companion)
            connection.commit()
            return guest_id

    def update_with_companion(
        self,
        guest: Guest,
        companion: Guest | None = None,
    ) -> None:
        with get_connection() as connection:
            self._update(connection, guest)
            existing = connection.execute(
                "SELECT id FROM guests WHERE parent_guest_id=? LIMIT 1",
                (guest.id,),
            ).fetchone()

            if companion:
                companion.parent_guest_id = guest.id
                if existing:
                    companion.id = int(existing["id"])
                    self._update(connection, companion)
                else:
                    self._insert(connection, companion)
            elif existing:
                connection.execute(
                    "DELETE FROM guests WHERE id=?",
                    (int(existing["id"]),),
                )
            connection.commit()

    def create(self, guest: Guest) -> int:
        return self.create_with_companion(guest)

    def update(self, guest: Guest) -> None:
        with get_connection() as connection:
            self._update(connection, guest)
            connection.commit()

    def delete(self, guest_id: int) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM guests WHERE parent_guest_id=?", (guest_id,))
            connection.execute("DELETE FROM guests WHERE id=?", (guest_id,))
            connection.commit()

    def get_summary(self) -> dict[str, int]:
        guests = self.list_all()
        return {
            "records": len(guests),
            "planned": len(guests),
            "confirmed": sum(g.confirmed_headcount for g in guests),
            "waiting": sum(g.waiting_headcount for g in guests),
            "declined": sum(g.declined_headcount for g in guests),
            "dinner": sum(g.confirmed_headcount for g in guests if g.attends_dinner),
            "children": sum(g.confirmed_headcount for g in guests if g.guest_type == "Gyermek"),
        }

    def get_parent_name(self, parent_guest_id: int | None) -> str:
        if not parent_guest_id:
            return ""
        with get_connection() as connection:
            row = connection.execute(
                "SELECT name FROM guests WHERE id=?",
                (parent_guest_id,),
            ).fetchone()
        return str(row["name"]) if row else ""

    @staticmethod
    def _insert(connection, guest: Guest) -> int:
        cursor = connection.execute(
            """
            INSERT INTO guests (
                name,email,phone,guest_type,invitation_status,attendance_status,
                has_plus_one,plus_one_name,attends_dinner,dietary_notes,
                table_name,table_id,parent_guest_id,notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                guest.name, guest.email, guest.phone, guest.guest_type,
                guest.invitation_status, guest.attendance_status,
                int(guest.has_plus_one), guest.plus_one_name,
                int(guest.attends_dinner), guest.dietary_notes,
                guest.table_name, guest.table_id, guest.parent_guest_id,
                guest.notes,
            ),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _update(connection, guest: Guest) -> None:
        connection.execute(
            """
            UPDATE guests SET
                name=?,email=?,phone=?,guest_type=?,invitation_status=?,
                attendance_status=?,has_plus_one=?,plus_one_name=?,
                attends_dinner=?,dietary_notes=?,table_name=?,table_id=?,
                parent_guest_id=?,notes=?,updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                guest.name, guest.email, guest.phone, guest.guest_type,
                guest.invitation_status, guest.attendance_status,
                int(guest.has_plus_one), guest.plus_one_name,
                int(guest.attends_dinner), guest.dietary_notes,
                guest.table_name, guest.table_id, guest.parent_guest_id,
                guest.notes, guest.id,
            ),
        )

    @staticmethod
    def _row_to_guest(row) -> Guest:
        return Guest(
            id=int(row["id"]),
            name=str(row["name"]),
            email=str(row["email"] or ""),
            phone=str(row["phone"] or ""),
            guest_type=str(row["guest_type"]),
            invitation_status=str(row["invitation_status"]),
            attendance_status=str(row["attendance_status"]),
            has_plus_one=bool(row["has_plus_one"]),
            plus_one_name=str(row["plus_one_name"] or ""),
            attends_dinner=bool(row["attends_dinner"]),
            dietary_notes=str(row["dietary_notes"] or ""),
            table_name=str(row["table_name"] or ""),
            table_id=int(row["table_id"]) if row["table_id"] is not None else None,
            parent_guest_id=(
                int(row["parent_guest_id"])
                if row["parent_guest_id"] is not None
                else None
            ),
            notes=str(row["notes"] or ""),
        )
