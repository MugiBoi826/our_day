from datetime import date, timedelta
from our_day.database.connection import get_connection
from our_day.models.entry import Entry


class EntryRepository:
    FIELDS = """id, entry_type, title, description, contact_name, phone, email,
    deposit_amount, total_amount, status, deposit_due_date, deposit_paid_date,
    payment_due_date"""

    def list_all(self, entry_type: str | None = None) -> list[Entry]:
        query = f"SELECT {self.FIELDS} FROM entries"
        params = ()
        if entry_type:
            query += " WHERE entry_type = ?"
            params = (entry_type,)
        query += " ORDER BY id DESC"
        with get_connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._row(row) for row in rows]

    def get_by_id(self, entry_id: int) -> Entry | None:
        with get_connection() as connection:
            row = connection.execute(
                f"SELECT {self.FIELDS} FROM entries WHERE id = ?", (entry_id,)
            ).fetchone()
        return self._row(row) if row else None

    def create(self, e: Entry) -> int:
        with get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO entries (
                    entry_type,title,description,contact_name,phone,email,
                    deposit_amount,total_amount,status,deposit_due_date,
                    deposit_paid_date,payment_due_date
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (e.entry_type,e.title,e.description,e.contact_name,e.phone,e.email,
                 e.deposit_amount,e.total_amount,e.status,self._to_db(e.deposit_due_date),
                 self._to_db(e.deposit_paid_date),self._to_db(e.payment_due_date))
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(self, e: Entry) -> None:
        with get_connection() as connection:
            connection.execute(
                """UPDATE entries SET entry_type=?,title=?,description=?,contact_name=?,
                phone=?,email=?,deposit_amount=?,total_amount=?,status=?,
                deposit_due_date=?,deposit_paid_date=?,payment_due_date=?,
                updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (e.entry_type,e.title,e.description,e.contact_name,e.phone,e.email,
                 e.deposit_amount,e.total_amount,e.status,self._to_db(e.deposit_due_date),
                 self._to_db(e.deposit_paid_date),self._to_db(e.payment_due_date),e.id)
            )
            connection.commit()

    def delete(self, entry_id: int) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM entries WHERE id=?", (entry_id,))
            connection.commit()

    def get_financial_summary(self, entry_type: str | None = None) -> dict[str, float]:
        active_statuses = (
            "Lefoglalva",
            "Részben fizetve",
            "Kifizetve",
        )

        placeholders = ",".join(
            "?"
            for _ in active_statuses
        )

        query = f"""
        SELECT
          COALESCE(
            SUM(
              CASE
                WHEN status IN ({placeholders})
                THEN total_amount
                ELSE 0
              END
            ),
            0
          ) AS total_planned,
          COALESCE(
            SUM(
              CASE
                WHEN status IN ('Lefoglalva', 'Részben fizetve')
                THEN deposit_amount
                ELSE 0
              END
            ),
            0
          ) AS active_deposits,
          COALESCE(
            SUM(
              CASE
                WHEN status = 'Kifizetve'
                THEN total_amount
                WHEN status = 'Részben fizetve'
                THEN deposit_amount
                ELSE 0
              END
            ),
            0
          ) AS paid_total,
          COALESCE(
            SUM(
              CASE
                WHEN status = 'Lefoglalva'
                THEN MAX(total_amount - deposit_amount, 0)
                WHEN status = 'Részben fizetve'
                THEN MAX(total_amount - deposit_amount, 0)
                ELSE 0
              END
            ),
            0
          ) AS remaining
        FROM entries
        """

        params: tuple = active_statuses

        if entry_type:
            query += " WHERE entry_type = ?"
            params = (
                *active_statuses,
                entry_type,
            )

        with get_connection() as connection:
            row = connection.execute(
                query,
                params,
            ).fetchone()

        return {
            "total": float(row["total_planned"]),
            "deposits": float(row["active_deposits"]),
            "paid": float(row["paid_total"]),
            "remaining": float(row["remaining"]),
        }

    def get_upcoming_deadlines(self, days_ahead: int = 10) -> list[dict]:
        today = date.today()
        limit = today + timedelta(days=days_ahead)
        result = []
        for e in self.list_all("Szolgáltatás"):
            if e.status not in (
                "Lefoglalva",
                "Részben fizetve",
            ):
                continue
            if e.deposit_due_date and not e.deposit_paid_date and e.deposit_due_date <= limit:
                result.append({"title":e.title,"kind":"Foglaló fizetési határidő","date":e.deposit_due_date})
            if e.payment_due_date and e.payment_due_date <= limit:
                result.append({"title":e.title,"kind":"Teljes fizetési határidő","date":e.payment_due_date})
        return sorted(result, key=lambda x: x["date"])

    @staticmethod
    def _to_db(value): return value.isoformat() if value else None
    @staticmethod
    def _from_db(value): return date.fromisoformat(value) if value else None

    @classmethod
    def _row(cls, row):
        return Entry(
            id=int(row["id"]), entry_type=row["entry_type"], title=row["title"],
            description=row["description"] or "", contact_name=row["contact_name"] or "",
            phone=row["phone"] or "", email=row["email"] or "",
            deposit_amount=float(row["deposit_amount"]), total_amount=float(row["total_amount"]),
            status=row["status"], deposit_due_date=cls._from_db(row["deposit_due_date"]),
            deposit_paid_date=cls._from_db(row["deposit_paid_date"]),
            payment_due_date=cls._from_db(row["payment_due_date"])
        )
