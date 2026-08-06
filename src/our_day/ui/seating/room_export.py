from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QRectF,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QImage,
    QPageLayout,
    QPageSize,
    QPainter,
)
from PySide6.QtPrintSupport import (
    QPrintDialog,
    QPrinter,
)


class RoomExportService:
    @staticmethod
    def save_image(
        scene,
        file_path: str,
    ) -> Path:
        destination = Path(file_path)

        source_rect = (
            scene.itemsBoundingRect()
            .adjusted(
                -40,
                -40,
                40,
                40,
            )
        )

        width = max(
            1200,
            int(source_rect.width()),
        )
        height = max(
            800,
            int(source_rect.height()),
        )

        image = QImage(
            width,
            height,
            QImage.Format_ARGB32,
        )
        image.fill(
            QColor("#FFFFFF")
        )

        painter = QPainter(image)
        painter.setRenderHint(
            QPainter.Antialiasing
        )

        scene.render(
            painter,
            QRectF(
                0,
                0,
                width,
                height,
            ),
            source_rect,
            Qt.KeepAspectRatio,
        )

        painter.end()

        if not image.save(
            str(destination)
        ):
            raise RuntimeError(
                "A teremkép mentése nem sikerült."
            )

        return destination

    @staticmethod
    def print_scene(
        parent,
        scene,
    ) -> bool:
        printer = QPrinter(
            QPrinter.HighResolution
        )

        printer.setPageOrientation(
            QPageLayout.Landscape
        )
        printer.setPageSize(
            QPageSize(
                QPageSize.A4
            )
        )

        dialog = QPrintDialog(
            printer,
            parent,
        )
        dialog.setWindowTitle(
            "Teremnézet nyomtatása"
        )

        if not dialog.exec():
            return False

        painter = QPainter(printer)
        painter.setRenderHint(
            QPainter.Antialiasing
        )

        page_rect = printer.pageRect(
            QPrinter.DevicePixel
        )
        source_rect = (
            scene.itemsBoundingRect()
            .adjusted(
                -30,
                -30,
                30,
                30,
            )
        )

        scene.render(
            painter,
            QRectF(page_rect),
            source_rect,
            Qt.KeepAspectRatio,
        )

        painter.end()
        return True
