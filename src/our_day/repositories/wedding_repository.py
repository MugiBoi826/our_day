from datetime import date

from our_day.database.connection import get_connection
from our_day.models.wedding import Wedding


class WeddingRepository:
    def get_active(self) -> Wedding | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    bride_name,
                    groom_name,
                    wedding_date,
                    venue_name,
                    venue_address,
                    budget_amount,
                    notes,
                    is_active
                FROM weddings
                WHERE is_active = 1
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()

        return self._row_to_wedding(row) if row else None

    def save_active(self, wedding: Wedding) -> int:
        with get_connection() as connection:
            current = connection.execute(
                """
                SELECT id
                FROM weddings
                WHERE is_active = 1
                ORDER BY id
                LIMIT 1
                """
            ).fetchone()

            wedding_date = (
                wedding.wedding_date.isoformat()
                if wedding.wedding_date
                else None
            )

            if current:
                wedding_id = int(current["id"])
                connection.execute(
                    """
                    UPDATE weddings
                    SET
                        bride_name = ?,
                        groom_name = ?,
                        wedding_date = ?,
                        venue_name = ?,
                        venue_address = ?,
                        budget_amount = ?,
                        notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        wedding.bride_name,
                        wedding.groom_name,
                        wedding_date,
                        wedding.venue_name,
                        wedding.venue_address,
                        wedding.budget_amount,
                        wedding.notes,
                        wedding_id,
                    ),
                )
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO weddings (
                        bride_name,
                        groom_name,
                        wedding_date,
                        venue_name,
                        venue_address,
                        budget_amount,
                        notes,
                        is_active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        wedding.bride_name,
                        wedding.groom_name,
                        wedding_date,
                        wedding.venue_name,
                        wedding.venue_address,
                        wedding.budget_amount,
                        wedding.notes,
                    ),
                )
                wedding_id = int(cursor.lastrowid)

            connection.commit()
            return wedding_id

    @staticmethod
    def _row_to_wedding(row) -> Wedding:
        return Wedding(
            id=int(row["id"]),
            bride_name=str(row["bride_name"] or ""),
            groom_name=str(row["groom_name"] or ""),
            wedding_date=(
                date.fromisoformat(str(row["wedding_date"]))
                if row["wedding_date"]
                else None
            ),
            venue_name=str(row["venue_name"] or ""),
            venue_address=str(row["venue_address"] or ""),
            budget_amount=float(row["budget_amount"] or 0),
            notes=str(row["notes"] or ""),
            is_active=bool(row["is_active"]),
        )
