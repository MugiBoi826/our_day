from datetime import date, timedelta
from our_day.database.connection import get_connection
from our_day.models.task import Task


class TaskRepository:
    def list_all(self) -> list[Task]:
        with get_connection() as connection:
            rows = connection.execute(
                """SELECT id,title,description,due_date,priority,status FROM tasks
                ORDER BY CASE WHEN status='Elkészült' THEN 1 ELSE 0 END,
                due_date IS NULL, due_date, id DESC"""
            ).fetchall()
        return [self._row(r) for r in rows]

    def get_by_id(self, task_id: int) -> Task | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id,title,description,due_date,priority,status FROM tasks WHERE id=?",
                (task_id,)
            ).fetchone()
        return self._row(row) if row else None

    def create(self, task: Task) -> int:
        with get_connection() as connection:
            cur = connection.execute(
                "INSERT INTO tasks(title,description,due_date,priority,status) VALUES(?,?,?,?,?)",
                (task.title,task.description,task.due_date.isoformat() if task.due_date else None,
                 task.priority,task.status)
            )
            connection.commit()
            return int(cur.lastrowid)

    def update(self, task: Task) -> None:
        with get_connection() as connection:
            connection.execute(
                """UPDATE tasks SET title=?,description=?,due_date=?,priority=?,status=?,
                updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (task.title,task.description,task.due_date.isoformat() if task.due_date else None,
                 task.priority,task.status,task.id)
            )
            connection.commit()

    def delete(self, task_id: int) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            connection.commit()

    def get_summary(self) -> dict[str,int]:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) total, SUM(CASE WHEN status='Elkészült' THEN 1 ELSE 0 END) done FROM tasks"
            ).fetchone()
        total, done = int(row["total"] or 0), int(row["done"] or 0)
        return {"total":total,"done":done,"open":total-done}

    def get_upcoming(self, days_ahead: int = 10) -> list[Task]:
        limit = date.today() + timedelta(days=days_ahead)
        return [t for t in self.list_all() if t.status!="Elkészült" and t.due_date and t.due_date<=limit]

    @staticmethod
    def _row(row):
        return Task(id=int(row["id"]),title=row["title"],description=row["description"] or "",
                    due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
                    priority=row["priority"],status=row["status"])
