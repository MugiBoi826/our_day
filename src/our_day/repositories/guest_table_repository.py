from our_day.database.connection import get_connection
from our_day.models.guest_table import GuestTable


class GuestTableRepository:
    def list_all(self) -> list[GuestTable]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, name, capacity, notes FROM guest_tables ORDER BY name COLLATE NOCASE"
            ).fetchall()
        return [
            GuestTable(
                id=int(row["id"]),
                name=str(row["name"]),
                capacity=int(row["capacity"]),
                notes=str(row["notes"] or ""),
            )
            for row in rows
        ]

    def create(self, table: GuestTable) -> int:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO guest_tables(name, capacity, notes) VALUES(?,?,?)",
                (table.name, table.capacity, table.notes),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(self, table: GuestTable) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE guest_tables SET name=?, capacity=?, notes=? WHERE id=?",
                (table.name, table.capacity, table.notes, table.id),
            )
            connection.commit()

    def delete(self, table_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE guests SET table_id=NULL, table_name='' WHERE table_id=?",
                (table_id,),
            )
            connection.execute("DELETE FROM guest_tables WHERE id=?", (table_id,))
            connection.commit()

    def get_by_id(self, table_id: int) -> GuestTable | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id,name,capacity,notes FROM guest_tables WHERE id=?",
                (table_id,),
            ).fetchone()
        if not row:
            return None
        return GuestTable(int(row["id"]), row["name"], int(row["capacity"]), row["notes"] or "")
