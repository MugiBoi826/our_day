from __future__ import annotations

from PySide6.QtCore import (
    QPointF,
    QRectF,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
)


class MovableTableItem(QGraphicsObject):
    position_saved = Signal(
        int,
        float,
        float,
    )

    SHAPE_SIZES = {
        "Kerek": (190, 150),
        "Ovális": (230, 140),
        "Téglalap": (220, 145),
        "Hosszú asztal": (300, 125),
        "U alakú": (260, 175),
        "Főasztal": (320, 135),
    }

    def __init__(
        self,
        table,
        guest_count: int,
        summary: str,
    ) -> None:
        super().__init__()

        self.table = table
        self.guest_count = guest_count
        self.summary = summary

        self.width, self.height = (
            self.SHAPE_SIZES.get(
                table.shape,
                self.SHAPE_SIZES["Kerek"],
            )
        )

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )

        self.setPos(
            table.position_x,
            table.position_y,
        )

        self.setToolTip(
            (
                f"{table.name}\n"
                f"{guest_count} / "
                f"{table.capacity} fő\n"
                f"{summary}"
            )
        )

    def boundingRect(self) -> QRectF:
        return QRectF(
            0,
            0,
            self.width,
            self.height,
        )

    def paint(
        self,
        painter: QPainter,
        option,
        widget=None,
    ) -> None:
        painter.setRenderHint(
            QPainter.Antialiasing
        )

        overbooked = (
            self.guest_count
            > self.table.capacity
        )

        fill = QColor(
            "#FFF0F0"
            if overbooked
            else "#F1ECFA"
        )
        border = QColor(
            "#C83E3E"
            if overbooked
            else "#6B4EA0"
        )

        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(border, 2))

        rect = self.boundingRect()

        if self.table.shape in (
            "Kerek",
            "Ovális",
        ):
            painter.drawEllipse(rect)
        elif self.table.shape == "U alakú":
            self._draw_u_shape(
                painter,
                rect,
                border,
            )
        else:
            painter.drawRoundedRect(
                rect,
                14,
                14,
            )

        self._draw_text(
            painter,
            rect,
            overbooked,
        )

    def _draw_text(
        self,
        painter: QPainter,
        rect: QRectF,
        overbooked: bool,
    ) -> None:
        text_rect = rect.adjusted(
            18,
            12,
            -18,
            -12,
        )

        painter.setPen(
            QColor("#35264D")
        )

        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        painter.setFont(title_font)

        title_rect = QRectF(
            text_rect.x(),
            text_rect.y(),
            text_rect.width(),
            42,
        )

        painter.drawText(
            title_rect,
            (
                Qt.AlignCenter
                | Qt.TextWordWrap
            ),
            self._short(
                self.table.name,
                34,
            ),
        )

        count_font = QFont()
        count_font.setPointSize(10)
        count_font.setBold(True)
        painter.setFont(count_font)

        count_rect = QRectF(
            text_rect.x(),
            title_rect.bottom() + 2,
            text_rect.width(),
            24,
        )

        painter.drawText(
            count_rect,
            Qt.AlignCenter,
            (
                f"{self.guest_count} / "
                f"{self.table.capacity} fő"
            ),
        )

        detail_font = QFont()
        detail_font.setPointSize(8)
        painter.setFont(detail_font)

        painter.setPen(
            QColor(
                "#B42318"
                if overbooked
                else "#625574"
            )
        )

        detail_rect = QRectF(
            text_rect.x(),
            count_rect.bottom() + 2,
            text_rect.width(),
            max(
                24,
                text_rect.bottom()
                - count_rect.bottom()
                - 2,
            ),
        )

        summary_line = (
            self.summary.splitlines()[0]
            if self.summary
            else ""
        )

        painter.drawText(
            detail_rect,
            (
                Qt.AlignHCenter
                | Qt.AlignTop
                | Qt.TextWordWrap
            ),
            self._short(
                summary_line,
                48,
            ),
        )

    @staticmethod
    def _draw_u_shape(
        painter: QPainter,
        rect: QRectF,
        border: QColor,
    ) -> None:
        painter.setBrush(Qt.NoBrush)
        painter.setPen(
            QPen(border, 18)
        )

        margin = 18

        painter.drawLine(
            QPointF(
                rect.left() + margin,
                rect.top() + margin,
            ),
            QPointF(
                rect.left() + margin,
                rect.bottom() - margin,
            ),
        )
        painter.drawLine(
            QPointF(
                rect.left() + margin,
                rect.bottom() - margin,
            ),
            QPointF(
                rect.right() - margin,
                rect.bottom() - margin,
            ),
        )
        painter.drawLine(
            QPointF(
                rect.right() - margin,
                rect.bottom() - margin,
            ),
            QPointF(
                rect.right() - margin,
                rect.top() + margin,
            ),
        )

    @staticmethod
    def _short(
        value: str,
        limit: int,
    ) -> str:
        text = str(value or "").strip()

        if len(text) <= limit:
            return text

        return (
            text[: limit - 1].rstrip()
            + "…"
        )

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)

        self.position_saved.emit(
            int(self.table.id),
            float(self.pos().x()),
            float(self.pos().y()),
        )
