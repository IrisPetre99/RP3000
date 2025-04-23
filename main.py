import sys
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QSlider, QFileDialog,
    QVBoxLayout, QHBoxLayout, QSpinBox, QLineEdit, QSizePolicy,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsSceneWheelEvent
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QImage

class ZoomPanGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene().addItem(self.pixmap_item)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def set_image(self, qimage):
        pix = QPixmap.fromImage(qimage)
        self.pixmap_item.setPixmap(pix)
        self.setSceneRect(QRectF(pix.rect()))
        self.resetTransform()

    def wheelEvent(self, event: QGraphicsSceneWheelEvent):
        zoom_factor = 1.25
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)


class VideoFrameComparer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Frame Comparer")
        self.setFixedSize(1950, 700)

        self.cap = None
        self.total_frames = 0
        self.frame_index = 0
        self.offset = 1
        self.video_path = ""

        self.init_ui()

    def init_ui(self):
        # Apply the system's native style
        QApplication.setStyle("fusion")

        # Top: Load video
        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        self.video_path_label = QLabel("No video loaded")
        self.video_path_label.setWordWrap(True)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setVisible(False)
        self.slider.valueChanged.connect(self.update_frames)

        # Timestamp input
        self.timestamp_input = QLineEdit()
        self.timestamp_input.setPlaceholderText("Enter timestamp (mm:ss)")
        self.timestamp_input.editingFinished.connect(self.update_frame_from_timestamp)
        self.timestamp_input.setVisible(False)

        # Offset
        self.offset_selector = QSpinBox()
        self.offset_selector.setMinimum(1)
        self.offset_selector.setValue(1)
        self.offset_selector.setPrefix("Offset: ")
        self.offset_selector.valueChanged.connect(self.update_offset)
        self.offset_selector.setVisible(False)

        # Prev/Next
        self.prev_button = QPushButton("<< Prev")
        self.next_button = QPushButton("Next >>")
        self.prev_button.clicked.connect(self.go_prev)
        self.next_button.clicked.connect(self.go_next)
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)

        # Frame numbers above image views
        self.label1 = QLabel("Frame: -")
        self.label2 = QLabel("Frame: -")

        # Image views
        self.image_view1 = ZoomPanGraphicsView()
        self.image_view2 = ZoomPanGraphicsView()
        self.image_view1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_view2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_view1.setBaseSize(600, 400) 
        self.image_view2.setBaseSize(600, 400)

        # Layouts
        main_layout = QVBoxLayout()

        # Top area: Load video + path
        load_layout = QHBoxLayout()
        load_layout.addWidget(self.load_button)
        load_layout.addWidget(self.video_path_label)
        main_layout.addLayout(load_layout)

        # Slider and Timestamp input (on the same line)
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.timestamp_input)
        slider_layout.addWidget(self.slider)
        main_layout.addLayout(slider_layout)

        # Prev/Next/Offset buttons (on a separate line)
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.prev_button)
        control_layout.addWidget(self.offset_selector)
        control_layout.addWidget(self.next_button)
        main_layout.addLayout(control_layout)

        # Frame numbers
        label_layout = QHBoxLayout()
        label_layout.addWidget(self.label1, alignment=Qt.AlignCenter)
        label_layout.addWidget(self.label2, alignment=Qt.AlignCenter)
        main_layout.addLayout(label_layout)

        # Images at the very bottom
        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_view1)
        image_layout.addWidget(self.image_view2)
        main_layout.addLayout(image_layout)

        self.setLayout(main_layout)

    def load_video(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if not file_name:
            return

        self.cap = cv2.VideoCapture(file_name)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_path = file_name

        self.video_path_label.setText(file_name)
        self.slider.setMaximum(self.total_frames - 2)
        self.slider.setValue(0)
        self.slider.setVisible(True)
        self.timestamp_input.setVisible(True)
        self.offset_selector.setVisible(True)

        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)

        self.update_frames(0)

    def update_offset(self, val):
        self.offset = val
        self.update_frames(self.frame_index)

    def get_frame(self, index):
        if index >= self.total_frames:
            return None
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, frame = self.cap.read()
        if not ret:
            return None
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        return QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

    def update_frames(self, value):
        self.frame_index = value
        frame1 = self.get_frame(value)
        frame2 = self.get_frame(value + self.offset)

        if frame1:
            self.label1.setText(f"Frame: {value}")
            self.image_view1.set_image(frame1)
        if frame2:
            self.label2.setText(f"Frame: {value + self.offset}")
            self.image_view2.set_image(frame2)

        # Update timestamp based on slider value
        seconds = int(self.frame_index / self.cap.get(cv2.CAP_PROP_FPS))
        minutes = seconds // 60
        seconds = seconds % 60
        self.timestamp_input.setText(f"{minutes:02}:{seconds:02}")

    def update_frame_from_timestamp(self):
        timestamp = self.timestamp_input.text()
        if ':' not in timestamp:
            return

        minutes, seconds = map(int, timestamp.split(':'))
        frame_time = minutes * 60 + seconds
        frame_index = int(frame_time * self.cap.get(cv2.CAP_PROP_FPS))

        # Set frame to closest second
        self.slider.setValue(min(frame_index, self.total_frames - 1))

    def go_prev(self):
        new_index = max(0, self.frame_index - 1)
        self.slider.setValue(new_index)

    def go_next(self):
        new_index = min(self.total_frames - self.offset - 1, self.frame_index + 1)
        self.slider.setValue(new_index)


# Run the app
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoFrameComparer()
    window.show()
    sys.exit(app.exec_())
