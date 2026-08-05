from our_day.database.connection import get_connection


class PreferenceRepository:
    CATEGORIES = ("Étrend", "Érzékenység", "Allergia")

    def list_all(self, category: str | None = None) -> list[dict]:
        query = "SELECT id, category, name FROM guest_preferences"
        parameters = ()

        if category:
            query += " WHERE category = ?"
            parameters = (category,)

        query += " ORDER BY category, name COLLATE NOCASE"

        with get_connection() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [
            {
                "id": int(row["id"]),
                "category": str(row["category"]),
                "name": str(row["name"]),
            }
            for row in rows
        ]

    def create(self, category: str, name: str) -> int:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO guest_preferences(category, name)
                VALUES (?, ?)
                """,
                (category, name),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(self, preference_id: int, category: str, name: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE guest_preferences
                SET category = ?, name = ?
                WHERE id = ?
                """,
                (category, name, preference_id),
            )
            connection.commit()

    def delete(self, preference_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM guest_preference_rel WHERE preference_id = ?",
                (preference_id,),
            )
            connection.execute(
                "DELETE FROM guest_preferences WHERE id = ?",
                (preference_id,),
            )
            connection.commit()
