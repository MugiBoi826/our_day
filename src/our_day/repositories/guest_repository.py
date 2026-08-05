from our_day.database.connection import get_connection
from our_day.models.guest import Guest


class GuestRepository:
    FIELDS = """
        g.id,
        g.name,
        g.email,
        g.phone,
        g.guest_type,
        g.invitation_status,
        g.attendance_status,
        g.has_plus_one,
        g.plus_one_name,
        g.attends_dinner,
        g.dietary_notes,
        COALESCE(t.name, g.table_name, '') AS table_name,
        g.table_id,
        g.parent_guest_id,
        g.family_group_id,
        g.family_name,
        g.notes,
        g.invitation_group_id,
        g.response_date,
        g.is_contact_person
    """

    def list_all(self) -> list[Guest]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self.FIELDS}
                FROM guests g
                LEFT JOIN guest_tables t
                    ON t.id = g.table_id
                ORDER BY
                    COALESCE(g.family_name, ''),
                    CASE
                        WHEN g.parent_guest_id IS NULL THEN 0
                        ELSE 1
                    END,
                    g.name COLLATE NOCASE
                """
            ).fetchall()

            guests = [
                self._row_to_guest(row)
                for row in rows
            ]
            self._load_preferences(connection, guests)

        return guests

    def list_by_group(
        self,
        group_id: int | None,
    ) -> list[Guest]:
        guests = self.list_all()

        if group_id is None:
            return [
                guest
                for guest in guests
                if guest.invitation_group_id is None
            ]

        return [
            guest
            for guest in guests
            if guest.invitation_group_id == group_id
        ]

    def get_by_id(
        self,
        guest_id: int,
    ) -> Guest | None:
        with get_connection() as connection:
            row = connection.execute(
                f"""
                SELECT {self.FIELDS}
                FROM guests g
                LEFT JOIN guest_tables t
                    ON t.id = g.table_id
                WHERE g.id = ?
                """,
                (guest_id,),
            ).fetchone()

            if row is None:
                return None

            guest = self._row_to_guest(row)
            self._load_preferences(
                connection,
                [guest],
            )

        return guest

    def get_linked_members(
        self,
        root_guest_id: int,
    ) -> list[Guest]:
        with get_connection() as connection:
            rows = connection.execute(
                f"""
                SELECT {self.FIELDS}
                FROM guests g
                LEFT JOIN guest_tables t
                    ON t.id = g.table_id
                WHERE g.parent_guest_id = ?
                ORDER BY g.name COLLATE NOCASE
                """,
                (root_guest_id,),
            ).fetchall()

            guests = [
                self._row_to_guest(row)
                for row in rows
            ]
            self._load_preferences(
                connection,
                guests,
            )

        return guests

    def create_group(
        self,
        root: Guest,
        members: list[Guest],
    ) -> int:
        with get_connection() as connection:
            root_id = self._insert(
                connection,
                root,
            )

            family_group_id = (
                root_id
                if members
                else None
            )

            connection.execute(
                """
                UPDATE guests
                SET family_group_id = ?
                WHERE id = ?
                """,
                (
                    family_group_id,
                    root_id,
                ),
            )

            self._save_preferences(
                connection,
                root_id,
                root.preference_ids,
            )

            for member in members:
                member.parent_guest_id = root_id
                member.family_group_id = family_group_id
                member.family_name = root.family_name
                member.table_id = root.table_id
                member.invitation_group_id = (
                    root.invitation_group_id
                )

                member_id = self._insert(
                    connection,
                    member,
                )

                self._save_preferences(
                    connection,
                    member_id,
                    member.preference_ids,
                )

            connection.commit()
            return root_id

    def update_group(
        self,
        root: Guest,
        members: list[Guest],
    ) -> None:
        if root.id is None:
            raise ValueError(
                "A meghívott azonosítója hiányzik."
            )

        with get_connection() as connection:
            self._update(
                connection,
                root,
            )
            self._save_preferences(
                connection,
                root.id,
                root.preference_ids,
            )

            existing_rows = connection.execute(
                """
                SELECT id
                FROM guests
                WHERE parent_guest_id = ?
                """,
                (root.id,),
            ).fetchall()

            existing_ids = {
                int(row["id"])
                for row in existing_rows
            }

            incoming_ids = {
                int(member.id)
                for member in members
                if member.id is not None
            }

            for removed_id in (
                existing_ids - incoming_ids
            ):
                connection.execute(
                    """
                    DELETE FROM guest_preference_rel
                    WHERE guest_id = ?
                    """,
                    (removed_id,),
                )
                connection.execute(
                    """
                    DELETE FROM guests
                    WHERE id = ?
                    """,
                    (removed_id,),
                )

            family_group_id = (
                root.id
                if members
                else None
            )

            connection.execute(
                """
                UPDATE guests
                SET family_group_id = ?
                WHERE id = ?
                """,
                (
                    family_group_id,
                    root.id,
                ),
            )

            for member in members:
                member.parent_guest_id = root.id
                member.family_group_id = (
                    family_group_id
                )
                member.family_name = root.family_name
                member.table_id = root.table_id
                member.invitation_group_id = (
                    root.invitation_group_id
                )

                if member.id is None:
                    member_id = self._insert(
                        connection,
                        member,
                    )
                else:
                    self._update(
                        connection,
                        member,
                    )
                    member_id = member.id

                self._save_preferences(
                    connection,
                    member_id,
                    member.preference_ids,
                )

            connection.commit()

    def create(
        self,
        guest: Guest,
    ) -> int:
        return self.create_group(
            guest,
            [],
        )

    def update(
        self,
        guest: Guest,
    ) -> None:
        members = self.get_linked_members(
            guest.id or 0
        )
        self.update_group(
            guest,
            members,
        )

    def delete(
        self,
        guest_id: int,
    ) -> None:
        with get_connection() as connection:
            child_rows = connection.execute(
                """
                SELECT id
                FROM guests
                WHERE parent_guest_id = ?
                """,
                (guest_id,),
            ).fetchall()

            ids_to_delete = [
                guest_id,
                *[
                    int(row["id"])
                    for row in child_rows
                ],
            ]

            for current_id in ids_to_delete:
                connection.execute(
                    """
                    DELETE FROM guest_preference_rel
                    WHERE guest_id = ?
                    """,
                    (current_id,),
                )
                connection.execute(
                    """
                    DELETE FROM guests
                    WHERE id = ?
                    """,
                    (current_id,),
                )

            connection.commit()

    def get_summary(self) -> dict[str, int]:
        guests = self.list_all()

        confirmed = [
            guest
            for guest in guests
            if guest.attendance_status
            == "Részt vesz"
        ]

        return {
            "records": len(guests),
            "planned": len(guests),
            "confirmed": len(confirmed),
            "waiting": sum(
                1
                for guest in guests
                if guest.attendance_status
                == "Válaszra vár"
            ),
            "declined": sum(
                1
                for guest in guests
                if guest.attendance_status
                == "Nem vesz részt"
            ),
            "dinner": sum(
                1
                for guest in confirmed
                if guest.attends_dinner
            ),
            "not_dinner": sum(
                1
                for guest in confirmed
                if not guest.attends_dinner
            ),
            "planned_adults": sum(
                1
                for guest in guests
                if guest.guest_type == "Felnőtt"
            ),
            "planned_children": sum(
                1
                for guest in guests
                if guest.guest_type == "Gyermek"
            ),
            "confirmed_adults": sum(
                1
                for guest in confirmed
                if guest.guest_type == "Felnőtt"
            ),
            "confirmed_children": sum(
                1
                for guest in confirmed
                if guest.guest_type == "Gyermek"
            ),
        }

    def get_parent_name(
        self,
        parent_guest_id: int | None,
    ) -> str:
        if not parent_guest_id:
            return ""

        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT name
                FROM guests
                WHERE id = ?
                """,
                (parent_guest_id,),
            ).fetchone()

        return (
            str(row["name"])
            if row
            else ""
        )

    @staticmethod
    def _insert(
        connection,
        guest: Guest,
    ) -> int:
        cursor = connection.execute(
            """
            INSERT INTO guests (
                name,
                email,
                phone,
                guest_type,
                invitation_status,
                attendance_status,
                has_plus_one,
                plus_one_name,
                attends_dinner,
                dietary_notes,
                table_name,
                table_id,
                parent_guest_id,
                family_group_id,
                family_name,
                notes,
                invitation_group_id,
                response_date,
                is_contact_person
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                guest.name,
                guest.email,
                guest.phone,
                guest.guest_type,
                guest.invitation_status,
                guest.attendance_status,
                int(guest.has_plus_one),
                guest.plus_one_name,
                int(guest.attends_dinner),
                guest.dietary_notes,
                guest.table_name,
                guest.table_id,
                guest.parent_guest_id,
                guest.family_group_id,
                guest.family_name,
                guest.notes,
                guest.invitation_group_id,
                guest.response_date,
                int(guest.is_contact_person),
            ),
        )

        return int(cursor.lastrowid)

    @staticmethod
    def _update(
        connection,
        guest: Guest,
    ) -> None:
        connection.execute(
            """
            UPDATE guests
            SET
                name = ?,
                email = ?,
                phone = ?,
                guest_type = ?,
                invitation_status = ?,
                attendance_status = ?,
                has_plus_one = ?,
                plus_one_name = ?,
                attends_dinner = ?,
                dietary_notes = ?,
                table_name = ?,
                table_id = ?,
                parent_guest_id = ?,
                family_group_id = ?,
                family_name = ?,
                notes = ?,
                invitation_group_id = ?,
                response_date = ?,
                is_contact_person = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                guest.name,
                guest.email,
                guest.phone,
                guest.guest_type,
                guest.invitation_status,
                guest.attendance_status,
                int(guest.has_plus_one),
                guest.plus_one_name,
                int(guest.attends_dinner),
                guest.dietary_notes,
                guest.table_name,
                guest.table_id,
                guest.parent_guest_id,
                guest.family_group_id,
                guest.family_name,
                guest.notes,
                guest.invitation_group_id,
                guest.response_date,
                int(guest.is_contact_person),
                guest.id,
            ),
        )

    @staticmethod
    def _save_preferences(
        connection,
        guest_id: int,
        preference_ids: list[int],
    ) -> None:
        connection.execute(
            """
            DELETE FROM guest_preference_rel
            WHERE guest_id = ?
            """,
            (guest_id,),
        )

        if not preference_ids:
            return

        connection.executemany(
            """
            INSERT INTO guest_preference_rel (
                guest_id,
                preference_id
            )
            VALUES (?, ?)
            """,
            [
                (
                    guest_id,
                    int(preference_id),
                )
                for preference_id in preference_ids
            ],
        )

    @staticmethod
    def _load_preferences(
        connection,
        guests: list[Guest],
    ) -> None:
        if not guests:
            return

        guest_map = {
            guest.id: guest
            for guest in guests
            if guest.id is not None
        }

        if not guest_map:
            return

        placeholders = ",".join(
            "?"
            for _ in guest_map
        )

        rows = connection.execute(
            f"""
            SELECT
                guest_id,
                preference_id
            FROM guest_preference_rel
            WHERE guest_id IN ({placeholders})
            """,
            tuple(guest_map.keys()),
        ).fetchall()

        for guest in guest_map.values():
            guest.preference_ids.clear()

        for row in rows:
            guest = guest_map.get(
                int(row["guest_id"])
            )

            if guest is not None:
                guest.preference_ids.append(
                    int(row["preference_id"])
                )

    @staticmethod
    def _row_to_guest(row) -> Guest:
        return Guest(
            id=int(row["id"]),
            name=str(row["name"]),
            email=str(row["email"] or ""),
            phone=str(row["phone"] or ""),
            guest_type=str(row["guest_type"]),
            invitation_status=str(
                row["invitation_status"]
            ),
            attendance_status=str(
                row["attendance_status"]
            ),
            has_plus_one=bool(
                row["has_plus_one"]
            ),
            plus_one_name=str(
                row["plus_one_name"] or ""
            ),
            attends_dinner=bool(
                row["attends_dinner"]
            ),
            dietary_notes=str(
                row["dietary_notes"] or ""
            ),
            table_name=str(
                row["table_name"] or ""
            ),
            table_id=(
                int(row["table_id"])
                if row["table_id"] is not None
                else None
            ),
            parent_guest_id=(
                int(row["parent_guest_id"])
                if row["parent_guest_id"]
                is not None
                else None
            ),
            family_group_id=(
                int(row["family_group_id"])
                if row["family_group_id"]
                is not None
                else None
            ),
            family_name=str(
                row["family_name"] or ""
            ),
            notes=str(
                row["notes"] or ""
            ),
            invitation_group_id=(
                int(row["invitation_group_id"])
                if row["invitation_group_id"]
                is not None
                else None
            ),
            response_date=row["response_date"],
            is_contact_person=bool(
                row["is_contact_person"]
            ),
        )
