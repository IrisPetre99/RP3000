from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QMouseEvent, QTransform
from PyQt5.QtCore import QRectF, Qt, pyqtSignal, QPointF

class ZoomPanGraphicsView(QGraphicsView):
    leftClick = pyqtSignal(QMouseEvent)
    transformChanged = pyqtSignal(QTransform, QPointF)

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene().addItem(self.pixmap_item)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._sync_enabled = True

    def set_image(self, qimage, reset_view=False):
        pix = QPixmap.fromImage(qimage)
        self.pixmap_item.setPixmap(pix)
        self.setSceneRect(QRectF(pix.rect()))
        if reset_view:
            self.resetTransform()
            self.centerOn(self.scene().sceneRect().center())

    def wheelEvent(self, event):
        zoom_factor = 1.25
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)
        self._emit_transform()

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
            self._emit_transform()
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
            self._emit_transform()
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
            self._emit_transform()
        else:
            super().mouseMoveEvent(event)

    def _emit_transform(self):
        if self._sync_enabled:
            viewport_center = self.mapToScene(self.viewport().rect().center())
            self.transformChanged.emit(self.transform(), viewport_center)

    def sync_with(self, other_view):
        self.transformChanged.connect(other_view._apply_transform)
        other_view.transformChanged.connect(self._apply_transform)

    def _apply_transform(self, transform, viewport_center):
        if self._sync_enabled:
            self._sync_enabled = False
            self.setTransform(transform)
            self.centerOn(viewport_center)
            self._sync_enabled = True
