from __future__ import annotations

import json
import sqlite3
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from our_day.database.connection import get_connection


SUPABASE_URL = "https://nhgprzjnaunfcdbefbsx.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_r21ppU3g50eYM1lZ1pZaEw_kW9DWj9X"


class SupabaseSyncError(RuntimeError):
    pass


class SupabaseSyncService:
    """Small, dependency-free bridge between Supabase and the SQLite cache."""

    def __init__(self) -> None:
        self.access_token: str | None = None
        self.wedding_id: str | None = None

    @property
    def is_signed_in(self) -> bool:
        return bool(self.access_token)

    def sign_in(self, email: str, password: str) -> None:
        payload = self._request(
            "POST",
            "/auth/v1/token?grant_type=password",
            {"email": email, "password": password},
            authenticated=False,
        )
        self.access_token = payload.get("access_token")
        if not self.access_token:
            raise SupabaseSyncError("A bejelentkezés nem adott hozzáférési tokent.")
        weddings = self._request(
            "GET",
            "/rest/v1/weddings?select=id&order=created_at.asc&limit=1",
        )
        if not weddings:
            raise SupabaseSyncError("Ehhez a fiókhoz még nem tartozik esküvő.")
        self.wedding_id = weddings[0]["id"]

    def download_to_cache(self) -> dict[str, int]:
        """Replace the local cache with the current authenticated cloud wedding."""
        wedding_id = self._require_wedding()
        wedding = self._get_one("weddings", f"id=eq.{wedding_id}")
        tables = self._get_all("guest_tables", wedding_id)
        groups = self._get_all("invitation_groups", wedding_id)
        preferences = self._get_all("guest_preferences", wedding_id)
        guests = self._get_all("guests", wedding_id)
        tasks = self._get_all("tasks", wedding_id)
        entries = self._get_all("entries", wedding_id)

        guest_ids = [row["id"] for row in guests]
        preference_links = self._get_relations("guest_preference_rel", guest_ids)
        seating_links = self._get_relations("guest_seating_preferences", guest_ids)

        with get_connection() as connection:
            self._clear_cache(connection)
            connection.execute(
                """
                INSERT INTO weddings(
                    id, bride_name, groom_name, wedding_date, venue_name,
                    venue_address, budget_amount, notes, is_active,
                    created_at, updated_at
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    wedding.get("bride_name", ""), wedding.get("groom_name", ""),
                    wedding.get("wedding_date"), wedding.get("venue_name"),
                    wedding.get("venue_address"), wedding.get("budget_amount", 0),
                    wedding.get("notes"), wedding.get("created_at"),
                    wedding.get("updated_at"),
                ),
            )

            table_map = self._insert_tables(connection, tables)
            group_map = self._insert_groups(connection, groups)
            preference_map = self._insert_preferences(connection, preferences)
            guest_map = self._insert_guests(connection, guests, table_map, group_map)
            self._finish_guest_links(connection, guests, groups, guest_map, group_map)
            self._insert_simple(connection, "tasks", tasks)
            self._insert_simple(connection, "entries", entries)
            self._insert_relations(
                connection, preference_links, seating_links, guest_map, preference_map
            )
            connection.commit()

        return {
            "guests": len(guests), "tasks": len(tasks), "entries": len(entries),
            "tables": len(tables), "groups": len(groups),
        }

    def upload_cache(self) -> dict[str, int]:
        """Upload locally edited primary records; Supabase remains authoritative."""
        wedding_id = self._require_wedding()
        with get_connection() as connection:
            wedding = connection.execute(
                "SELECT * FROM weddings WHERE is_active = 1 ORDER BY id LIMIT 1"
            ).fetchone()
            if wedding:
                self._request(
                    "PATCH", f"/rest/v1/weddings?id=eq.{wedding_id}",
                    self._pick(dict(wedding), (
                        "bride_name", "groom_name", "wedding_date", "venue_name",
                        "venue_address", "budget_amount", "notes", "updated_at",
                    )),
                )

            table_map = self._upsert_rows(connection, "guest_tables", wedding_id, (
                "name", "capacity", "notes", "position_x", "position_y", "shape",
            ))
            group_map = self._upsert_rows(connection, "invitation_groups", wedding_id, (
                "name", "group_type", "contact_name", "email", "phone",
                "invitation_sent_date", "rsvp_due_date", "notes", "updated_at",
            ))
            preference_map = self._upsert_rows(
                connection, "guest_preferences", wedding_id, ("category", "name")
            )
            guest_map = self._upsert_guests(connection, wedding_id, table_map, group_map)
            self._upload_guest_links(connection, guest_map, group_map, preference_map)
            self._upsert_rows(connection, "tasks", wedding_id, (
                "title", "description", "due_date", "priority", "status", "updated_at",
            ))
            self._upsert_rows(connection, "entries", wedding_id, (
                "entry_type", "title", "description", "contact_name", "phone", "email",
                "deposit_amount", "total_amount", "status", "deposit_due_date",
                "deposit_paid_date", "payment_due_date", "updated_at",
            ))
            self._delete_removed_rows(connection, wedding_id)
        return {
            "guests": len(guest_map), "tables": len(table_map), "groups": len(group_map)
        }

    def _request(self, method: str, path: str, body=None, authenticated=True):
        headers = {"apikey": SUPABASE_PUBLISHABLE_KEY, "Content-Type": "application/json"}
        if authenticated:
            if not self.access_token:
                raise SupabaseSyncError("Előbb jelentkezz be.")
            headers["Authorization"] = f"Bearer {self.access_token}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(SUPABASE_URL + path, data=data, headers=headers, method=method)
        if method == "POST" and path.startswith("/rest/"):
            request.add_header("Prefer", "resolution=merge-duplicates,return=representation")
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise SupabaseSyncError(f"Supabase hiba ({error.code}): {detail}") from error
        except (URLError, TimeoutError) as error:
            raise SupabaseSyncError(f"A felhő nem érhető el: {error}") from error

    def _require_wedding(self) -> str:
        if not self.wedding_id:
            raise SupabaseSyncError("Előbb jelentkezz be.")
        return self.wedding_id

    def _get_one(self, table: str, query: str):
        rows = self._request("GET", f"/rest/v1/{table}?select=*&{query}&limit=1")
        if not rows:
            raise SupabaseSyncError(f"Nem található felhőadat: {table}.")
        return rows[0]

    def _get_all(self, table: str, wedding_id: str):
        return self._request(
            "GET", f"/rest/v1/{table}?select=*&wedding_id=eq.{wedding_id}&limit=10000"
        ) or []

    def _get_relations(self, table: str, guest_ids: list[str]):
        if not guest_ids:
            return []
        ids = ",".join(guest_ids)
        return self._request(
            "GET", f"/rest/v1/{table}?select=*&guest_id=in.({quote(ids, safe=',')})&limit=10000"
        ) or []

    @staticmethod
    def _clear_cache(connection: sqlite3.Connection) -> None:
        for table in (
            "guest_preference_rel", "guest_seating_preferences", "guests",
            "invitation_groups", "guest_preferences", "guest_tables", "tasks",
            "entries", "weddings",
        ):
            connection.execute(f"DELETE FROM {table}")

    @staticmethod
    def _local_id(connection, table: str, row: dict) -> int:
        legacy = row.get("legacy_id")
        if legacy is not None:
            return int(legacy)
        current = connection.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0]
        return int(current)

    def _insert_tables(self, connection, rows):
        mapping = {}
        for row in rows:
            local_id = self._local_id(connection, "guest_tables", row)
            connection.execute(
                "INSERT INTO guest_tables(id,name,capacity,notes,position_x,position_y,shape,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (local_id, row["name"], row.get("capacity", 8), row.get("notes"),
                 row.get("position_x", 40), row.get("position_y", 40), row.get("shape", "Kerek"),
                 row.get("created_at") or "1970-01-01 00:00:00"),
            )
            mapping[row["id"]] = local_id
            self._store_legacy_id("guest_tables", row, local_id)
        return mapping

    def _insert_groups(self, connection, rows):
        mapping = {}
        for row in rows:
            local_id = self._local_id(connection, "invitation_groups", row)
            connection.execute(
                """INSERT INTO invitation_groups(id,name,group_type,contact_name,email,phone,
                invitation_sent_date,rsvp_due_date,notes,created_at,updated_at,contact_guest_id)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,NULL)""",
                (local_id, row["name"], row.get("group_type") or "Egyéb", row.get("contact_name"),
                 row.get("email"), row.get("phone"), row.get("invitation_sent_date"),
                 row.get("rsvp_due_date"), row.get("notes"),
                 row.get("created_at") or "1970-01-01 00:00:00",
                 row.get("updated_at") or "1970-01-01 00:00:00"),
            )
            mapping[row["id"]] = local_id
            self._store_legacy_id("invitation_groups", row, local_id)
        return mapping

    def _insert_preferences(self, connection, rows):
        mapping = {}
        for row in rows:
            local_id = self._local_id(connection, "guest_preferences", row)
            connection.execute("INSERT INTO guest_preferences(id,category,name) VALUES(?,?,?)",
                               (local_id, row["category"], row["name"]))
            mapping[row["id"]] = local_id
            self._store_legacy_id("guest_preferences", row, local_id)
        return mapping

    def _insert_guests(self, connection, rows, table_map, group_map):
        mapping = {}
        for row in rows:
            local_id = self._local_id(connection, "guests", row)
            connection.execute(
                """INSERT INTO guests(id,name,email,phone,guest_type,invitation_status,
                attendance_status,has_plus_one,plus_one_name,attends_dinner,dietary_notes,
                table_id,parent_guest_id,family_name,invitation_group_id,response_date,
                is_contact_person,seating_notes,accessibility_required,notes,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,NULL,?,?,?,?,?,?,?,?,?)""",
                (local_id,row["name"],row.get("email"),row.get("phone"),row.get("guest_type") or "Felnőtt",
                 row.get("invitation_status") or "Tervezett",row.get("attendance_status") or "Válaszra vár",
                 int(bool(row.get("has_plus_one"))),row.get("plus_one_name"),int(row.get("attends_dinner", True)),
                 row.get("dietary_notes"),table_map.get(row.get("table_id")),row.get("family_name"),
                 group_map.get(row.get("invitation_group_id")),row.get("response_date"),
                 int(bool(row.get("is_contact_person"))),row.get("seating_notes"),
                 int(bool(row.get("accessibility_required"))),row.get("notes"),
                 row.get("created_at") or "1970-01-01 00:00:00",
                 row.get("updated_at") or "1970-01-01 00:00:00"),
            )
            mapping[row["id"]] = local_id
            self._store_legacy_id("guests", row, local_id)
        return mapping

    @staticmethod
    def _finish_guest_links(connection, guests, groups, guest_map, group_map):
        for row in guests:
            connection.execute("UPDATE guests SET parent_guest_id=? WHERE id=?",
                               (guest_map.get(row.get("parent_guest_id")), guest_map[row["id"]]))
        for row in groups:
            connection.execute("UPDATE invitation_groups SET contact_guest_id=? WHERE id=?",
                               (guest_map.get(row.get("contact_guest_id")), group_map[row["id"]]))

    def _insert_simple(self, connection, table, rows):
        allowed = {
            "tasks": ("title","description","due_date","priority","status","created_at","updated_at"),
            "entries": ("entry_type","title","description","contact_name","phone","email","deposit_amount",
                        "total_amount","status","deposit_due_date","deposit_paid_date","payment_due_date","created_at","updated_at"),
        }[table]
        for row in rows:
            local_id = int(row.get("legacy_id") or connection.execute(
                f"SELECT COALESCE(MAX(id),0)+1 FROM {table}").fetchone()[0])
            columns = ",".join(("id",) + allowed)
            marks = ",".join("?" for _ in range(len(allowed) + 1))
            values = tuple(
                row.get(key) or "1970-01-01 00:00:00"
                if key in ("created_at", "updated_at") else row.get(key)
                for key in allowed
            )
            connection.execute(f"INSERT INTO {table}({columns}) VALUES({marks})",
                               (local_id,) + values)
            self._store_legacy_id(table, row, local_id)

    def _store_legacy_id(self, table: str, row: dict, local_id: int) -> None:
        if row.get("legacy_id") is None:
            self._request(
                "PATCH", f"/rest/v1/{table}?id=eq.{row['id']}",
                {"legacy_id": local_id},
            )

    @staticmethod
    def _insert_relations(connection, preference_links, seating_links, guest_map, preference_map):
        for row in preference_links:
            guest_id, pref_id = guest_map.get(row["guest_id"]), preference_map.get(row["preference_id"])
            if guest_id and pref_id:
                connection.execute("INSERT INTO guest_preference_rel VALUES(?,?)", (guest_id, pref_id))
        for row in seating_links:
            guest_id, related_id = guest_map.get(row["guest_id"]), guest_map.get(row["related_guest_id"])
            if guest_id and related_id:
                connection.execute("INSERT INTO guest_seating_preferences VALUES(?,?,?)",
                                   (guest_id, related_id, row["relation_type"]))

    @staticmethod
    def _pick(row: dict, columns):
        return {key: row.get(key) for key in columns if key in row}

    def _upsert_rows(self, connection, table, wedding_id, columns):
        mapping = {}
        for source in connection.execute(f"SELECT * FROM {table}"):
            row = dict(source)
            payload = {"wedding_id": wedding_id, "legacy_id": row["id"], **self._pick(row, columns)}
            result = self._request("POST", f"/rest/v1/{table}?on_conflict=wedding_id,legacy_id", payload)
            if result:
                mapping[row["id"]] = result[0]["id"]
        return mapping

    def _upsert_guests(self, connection, wedding_id, table_map, group_map):
        mapping = {}
        rows = [dict(row) for row in connection.execute("SELECT * FROM guests")]
        for row in rows:
            payload = {"wedding_id": wedding_id, "legacy_id": row["id"], **self._pick(row, (
                "name","email","phone","guest_type","invitation_status","attendance_status",
                "plus_one_name","dietary_notes","family_name","response_date","seating_notes","notes","updated_at",
            ))}
            payload.update({"has_plus_one": bool(row.get("has_plus_one")),
                            "attends_dinner": bool(row.get("attends_dinner")),
                            "accessibility_required": bool(row.get("accessibility_required")),
                            "is_contact_person": bool(row.get("is_contact_person")),
                            "table_id": table_map.get(row.get("table_id")),
                            "invitation_group_id": group_map.get(row.get("invitation_group_id"))})
            result = self._request("POST", "/rest/v1/guests?on_conflict=wedding_id,legacy_id", payload)
            if result:
                mapping[row["id"]] = result[0]["id"]
        return mapping

    def _upload_guest_links(self, connection, guest_map, group_map, preference_map):
        for row in connection.execute(
            "SELECT id,parent_guest_id FROM guests WHERE parent_guest_id IS NOT NULL"
        ):
            if row["id"] in guest_map and row["parent_guest_id"] in guest_map:
                self._request(
                    "PATCH", f"/rest/v1/guests?id=eq.{guest_map[row['id']]}",
                    {"parent_guest_id": guest_map[row["parent_guest_id"]]},
                )
        for row in connection.execute(
            "SELECT id,contact_guest_id FROM invitation_groups WHERE contact_guest_id IS NOT NULL"
        ):
            if row["id"] in group_map and row["contact_guest_id"] in guest_map:
                self._request(
                    "PATCH", f"/rest/v1/invitation_groups?id=eq.{group_map[row['id']]}",
                    {"contact_guest_id": guest_map[row["contact_guest_id"]]},
                )

        cloud_guest_ids = list(guest_map.values())
        if cloud_guest_ids:
            ids = quote(",".join(cloud_guest_ids), safe=",")
            self._request(
                "DELETE", f"/rest/v1/guest_preference_rel?guest_id=in.({ids})"
            )
            self._request(
                "DELETE", f"/rest/v1/guest_seating_preferences?guest_id=in.({ids})"
            )
        for row in connection.execute("SELECT guest_id,preference_id FROM guest_preference_rel"):
            if row["guest_id"] in guest_map and row["preference_id"] in preference_map:
                self._request("POST", "/rest/v1/guest_preference_rel", {
                    "guest_id": guest_map[row["guest_id"]],
                    "preference_id": preference_map[row["preference_id"]],
                })
        for row in connection.execute(
            "SELECT guest_id,related_guest_id,relation_type FROM guest_seating_preferences"
        ):
            if row["guest_id"] in guest_map and row["related_guest_id"] in guest_map:
                self._request("POST", "/rest/v1/guest_seating_preferences", {
                    "guest_id": guest_map[row["guest_id"]],
                    "related_guest_id": guest_map[row["related_guest_id"]],
                    "relation_type": row["relation_type"],
                })

    def _delete_removed_rows(self, connection, wedding_id: str) -> None:
        """Propagate desktop deletions without touching never-downloaded cloud rows."""
        for table in (
            "guests", "invitation_groups", "guest_preferences",
            "guest_tables", "tasks", "entries",
        ):
            local_ids = {
                int(row[0]) for row in connection.execute(f"SELECT id FROM {table}")
            }
            cloud_rows = self._request(
                "GET",
                f"/rest/v1/{table}?select=id,legacy_id&wedding_id=eq.{wedding_id}&limit=10000",
            ) or []
            for cloud_row in cloud_rows:
                legacy_id = cloud_row.get("legacy_id")
                if legacy_id is not None and int(legacy_id) not in local_ids:
                    self._request(
                        "DELETE", f"/rest/v1/{table}?id=eq.{cloud_row['id']}"
                    )
