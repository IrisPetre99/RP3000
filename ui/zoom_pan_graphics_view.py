from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QMouseEvent
from PyQt5.QtCore import QRectF, Qt, pyqtSignal

class ZoomPanGraphicsView(QGraphicsView):
    leftClick = pyqtSignal(QMouseEvent)

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene().addItem(self.pixmap_item)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def set_image(self, qimage, reset_view=False):
        pix = QPixmap.fromImage(qimage)
        self.pixmap_item.setPixmap(pix)
        self.setSceneRect(QRectF(pix.rect()))
        if reset_view:
            self.resetTransform()

    def wheelEvent(self, event):
        zoom_factor = 1.25
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.leftClick.emit(event)
        elif event.button() == Qt.MiddleButton:
            new_event = QMouseEvent(
                event.type(),
                event.pos(),
                event.globalPos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mousePressEvent(new_event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            new_event = QMouseEvent(
                event.type(),
                event.pos(),
                event.globalPos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mouseReleaseEvent(new_event)
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.MiddleButton:
            new_event = QMouseEvent(
                event.type(),
                event.pos(),
                event.globalPos(),
                Qt.LeftButton,
                Qt.LeftButton,
                event.modifiers()
            )
            super().mouseMoveEvent(new_event)
        else:
            super().mouseMoveEvent(event)
