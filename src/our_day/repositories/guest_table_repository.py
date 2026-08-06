from our_day.database.connection import get_connection
from our_day.models.guest_table import GuestTable


class GuestTableRepository:
    FIELDS = """
        id,
        name,
        capacity,
        notes,
        position_x,
        position_y,
        shape
    """

    def list_all(self) -> list[GuestTable]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self.FIELDS}
                FROM guest_tables
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()
        return [self._row(row) for row in rows]

    def create(self, table: GuestTable) -> int:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO guest_tables(
                    name,
                    capacity,
                    notes,
                    position_x,
                    position_y,
                    shape
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    table.name,
                    table.capacity,
                    table.notes,
                    table.position_x,
                    table.position_y,
                    table.shape,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(self, table: GuestTable) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE guest_tables
                SET name = ?,
                    capacity = ?,
                    notes = ?,
                    position_x = ?,
                    position_y = ?,
                    shape = ?
                WHERE id = ?
                """,
                (
                    table.name,
                    table.capacity,
                    table.notes,
                    table.position_x,
                    table.position_y,
                    table.shape,
                    table.id,
                ),
            )
            connection.commit()

    def update_position(
        self,
        table_id: int,
        x: float,
        y: float,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE guest_tables
                SET position_x = ?,
                    position_y = ?
                WHERE id = ?
                """,
                (x, y, table_id),
            )
            connection.commit()

    def delete(self, table_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE guests
                SET table_id = NULL,
                    table_name = ''
                WHERE table_id = ?
                """,
                (table_id,),
            )
            connection.execute(
                "DELETE FROM guest_tables WHERE id = ?",
                (table_id,),
            )
            connection.commit()

    def get_by_id(
        self,
        table_id: int,
    ) -> GuestTable | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self.FIELDS}
                FROM guest_tables
                WHERE id = ?
                """,
                (table_id,),
            ).fetchone()
        return self._row(row) if row else None

    @staticmethod
    def _row(row) -> GuestTable:
        return GuestTable(
            id=int(row["id"]),
            name=str(row["name"]),
            capacity=int(row["capacity"]),
            notes=str(row["notes"] or ""),
            position_x=float(row["position_x"] or 40),
            position_y=float(row["position_y"] or 40),
            shape=str(row["shape"] or "Kerek"),
        )
