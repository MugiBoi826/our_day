from __future__ import annotations

from PySide6.QtCore import (
    QByteArray,
    QDataStream,
    QIODevice,
    Qt,
    Signal,
)
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QListWidget


MIME_TYPE = "application/x-ourday-guests"


class GuestDropList(QListWidget):
    guests_dropped = Signal(list, object)

    def __init__(
        self,
        table_id=None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.table_id = table_id

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)

    def startDrag(self, supported_actions) -> None:
        guest_ids = [
            int(item.data(Qt.UserRole))
            for item in self.selectedItems()
            if item.data(Qt.UserRole) is not None
        ]

        if not guest_ids:
            return

        payload = QByteArray()
        stream = QDataStream(
            payload,
            QIODevice.WriteOnly,
        )

        stream.writeInt32(len(guest_ids))

        for guest_id in guest_ids:
            stream.writeInt32(guest_id)

        mime_data = self.mimeData([])
        mime_data.setData(
            MIME_TYPE,
            payload,
        )

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()
            return

        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()
            return

        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        if not event.mimeData().hasFormat(MIME_TYPE):
            super().dropEvent(event)
            return

        payload = event.mimeData().data(
            MIME_TYPE
        )
        stream = QDataStream(
            payload,
            QIODevice.ReadOnly,
        )

        count = stream.readInt32()
        guest_ids = [
            stream.readInt32()
            for _ in range(count)
        ]

        self.guests_dropped.emit(
            guest_ids,
            self.table_id,
        )
        event.acceptProposedAction()
