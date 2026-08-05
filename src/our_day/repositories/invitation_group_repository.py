from datetime import date

from our_day.database.connection import get_connection
from our_day.models.invitation_group import InvitationGroup


class InvitationGroupRepository:
    def list_all(self) -> list[InvitationGroup]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, name, group_type, contact_name, email, phone,
                       invitation_sent_date, rsvp_due_date, notes,
                       contact_guest_id
                FROM invitation_groups
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()
        return [self._row(row) for row in rows]

    def get_by_id(self, group_id: int) -> InvitationGroup | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, name, group_type, contact_name, email, phone,
                       invitation_sent_date, rsvp_due_date, notes,
                       contact_guest_id
                FROM invitation_groups
                WHERE id = ?
                """,
                (group_id,),
            ).fetchone()
        return self._row(row) if row else None

    def create(self, group: InvitationGroup) -> int:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO invitation_groups(
                    name, group_type, contact_name, email, phone,
                    invitation_sent_date, rsvp_due_date, notes,
                    contact_guest_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group.name,
                    group.group_type,
                    group.contact_name,
                    group.email,
                    group.phone,
                    self._to_db(group.invitation_sent_date),
                    self._to_db(group.rsvp_due_date),
                    group.notes,
                    group.contact_guest_id,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update(self, group: InvitationGroup) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE invitation_groups
                SET name=?, group_type=?, contact_name=?, email=?, phone=?,
                    invitation_sent_date=?, rsvp_due_date=?, notes=?,
                    contact_guest_id=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (
                    group.name,
                    group.group_type,
                    group.contact_name,
                    group.email,
                    group.phone,
                    self._to_db(group.invitation_sent_date),
                    self._to_db(group.rsvp_due_date),
                    group.notes,
                    group.contact_guest_id,
                    group.id,
                ),
            )
            connection.commit()

    def delete(self, group_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                "UPDATE guests SET invitation_group_id=NULL WHERE invitation_group_id=?",
                (group_id,),
            )
            connection.execute(
                "DELETE FROM invitation_groups WHERE id=?",
                (group_id,),
            )
            connection.commit()


    def get_rsvp_overview(self) -> list[dict[str, object]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    ig.id,
                    ig.name,
                    ig.group_type,
                    ig.rsvp_due_date,
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
                GROUP BY
                    ig.id,
                    ig.name,
                    ig.group_type,
                    ig.rsvp_due_date
                ORDER BY
                    CASE
                        WHEN ig.rsvp_due_date IS NULL THEN 1
                        ELSE 0
                    END,
                    ig.rsvp_due_date,
                    ig.name COLLATE NOCASE
                """
            ).fetchall()

        return [
            {
                "id": int(row["id"]),
                "name": str(row["name"]),
                "group_type": str(row["group_type"]),
                "rsvp_due_date": self._from_db(
                    row["rsvp_due_date"]
                ),
                "total": int(row["total"] or 0),
                "confirmed": int(row["confirmed"] or 0),
                "waiting": int(row["waiting"] or 0),
                "declined": int(row["declined"] or 0),
            }
            for row in rows
        ]

    def list_group_members(
        self,
        group_id: int,
    ) -> list[dict[str, object]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, name
                FROM guests
                WHERE invitation_group_id = ?
                ORDER BY name COLLATE NOCASE
                """,
                (group_id,),
            ).fetchall()

        return [
            {
                "id": int(row["id"]),
                "name": str(row["name"]),
            }
            for row in rows
        ]

    def set_contact_guest(
        self,
        group_id: int,
        contact_guest_id: int | None,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE guests
                SET is_contact_person = 0
                WHERE invitation_group_id = ?
                """,
                (group_id,),
            )

            if contact_guest_id is not None:
                connection.execute(
                    """
                    UPDATE guests
                    SET is_contact_person = 1
                    WHERE id = ?
                      AND invitation_group_id = ?
                    """,
                    (
                        contact_guest_id,
                        group_id,
                    ),
                )

            connection.execute(
                """
                UPDATE invitation_groups
                SET contact_guest_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    contact_guest_id,
                    group_id,
                ),
            )
            connection.commit()

    def get_contact_guest_name(
        self,
        group_id: int,
    ) -> str:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT g.name
                FROM invitation_groups ig
                LEFT JOIN guests g
                    ON g.id = ig.contact_guest_id
                WHERE ig.id = ?
                """,
                (group_id,),
            ).fetchone()

        return (
            str(row["name"])
            if row and row["name"]
            else ""
        )

    def get_member_count(self, group_id: int) -> int:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) count FROM guests WHERE invitation_group_id=?",
                (group_id,),
            ).fetchone()
        return int(row["count"])


    def get_summary(self, group_id: int) -> dict[str, int]:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(
                        CASE
                            WHEN attendance_status = 'Részt vesz'
                            THEN 1 ELSE 0
                        END
                    ) AS confirmed,
                    SUM(
                        CASE
                            WHEN attendance_status = 'Válaszra vár'
                            THEN 1 ELSE 0
                        END
                    ) AS waiting,
                    SUM(
                        CASE
                            WHEN attendance_status = 'Nem vesz részt'
                            THEN 1 ELSE 0
                        END
                    ) AS declined,
                    SUM(
                        CASE
                            WHEN attendance_status = 'Részt vesz'
                                 AND attends_dinner = 1
                            THEN 1 ELSE 0
                        END
                    ) AS dinner
                FROM guests
                WHERE invitation_group_id = ?
                """,
                (group_id,),
            ).fetchone()

        return {
            "total": int(row["total"] or 0),
            "confirmed": int(row["confirmed"] or 0),
            "waiting": int(row["waiting"] or 0),
            "declined": int(row["declined"] or 0),
            "dinner": int(row["dinner"] or 0),
        }

    @staticmethod
    def _to_db(value):
        return value.isoformat() if value else None

    @staticmethod
    def _from_db(value):
        return date.fromisoformat(value) if value else None

    @classmethod
    def _row(cls, row) -> InvitationGroup:
        return InvitationGroup(
            id=int(row["id"]),
            name=str(row["name"]),
            group_type=str(row["group_type"]),
            contact_name=str(row["contact_name"] or ""),
            email=str(row["email"] or ""),
            phone=str(row["phone"] or ""),
            invitation_sent_date=cls._from_db(row["invitation_sent_date"]),
            rsvp_due_date=cls._from_db(row["rsvp_due_date"]),
            notes=str(row["notes"] or ""),
            contact_guest_id=(
                int(row["contact_guest_id"])
                if row["contact_guest_id"] is not None
                else None
            ),
        )
