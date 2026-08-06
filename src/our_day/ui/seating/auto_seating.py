from __future__ import annotations

from collections import defaultdict


class AutoSeatingService:
    @staticmethod
    def create_proposal(
        guests,
        tables,
    ) -> tuple[dict[int, int], list]:
        groups = defaultdict(list)

        for guest in guests:
            key = (
                guest.invitation_group_id
                or guest.family_group_id
                or f"guest-{guest.id}"
            )
            groups[key].append(guest)

        capacities = {
            table.id: table.capacity
            for table in tables
        }

        proposal: dict[int, int] = {}
        unplaced = []

        sorted_groups = sorted(
            groups.values(),
            key=len,
            reverse=True,
        )

        for group in sorted_groups:
            candidate = next(
                (
                    table
                    for table in tables
                    if capacities[table.id]
                    >= len(group)
                ),
                None,
            )

            if candidate is None:
                unplaced.extend(group)
                continue

            for guest in group:
                proposal[guest.id] = (
                    candidate.id
                )

            capacities[candidate.id] -= (
                len(group)
            )

        return proposal, unplaced
