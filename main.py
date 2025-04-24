import random, sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
import cv2
import numpy as np
import os

class ZoomPanGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene().addItem(self.pixmap_item)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

    def set_image(self, qimage, reset_view=False):
        pix = QPixmap.fromImage(qimage)
        self.pixmap_item.setPixmap(pix)
        self.setSceneRect(QRectF(pix.rect()))
        if reset_view:
            self.resetTransform()

    def wheelEvent(self, event: QGraphicsSceneWheelEvent):
        zoom_factor = 1.25
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

# Convert QImage to RGB numpy
def qimage_to_rgb(qimage):
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        arr = np.array(ptr).reshape(qimage.height(), qimage.width(), 3)
        return arr

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

        self.annotations = []
        self.selected_frame1_point = None
        self.selected_frame2_point = None
        self.max_pairs = 10
        self.colors = []

        self.init_ui()

    def init_ui(self):
        QApplication.setStyle("fusion")

        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        self.video_path_label = QLabel("No video loaded")

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setVisible(False)
        self.slider.valueChanged.connect(self.update_frames)

        self.timestamp_input = QLineEdit()
        self.timestamp_input.setPlaceholderText("Enter timestamp (mm:ss)")
        self.timestamp_input.editingFinished.connect(self.update_frame_from_timestamp)
        self.timestamp_input.setVisible(False)

        self.offset_selector = QSpinBox()
        self.offset_selector.setMinimum(1)
        self.offset_selector.setValue(1)
        self.offset_selector.setPrefix("Offset: ")
        self.offset_selector.valueChanged.connect(self.update_offset)
        self.offset_selector.setVisible(False)

        self.pair_limit_selector = QSpinBox()
        self.pair_limit_selector.setMinimum(1)
        self.pair_limit_selector.setValue(self.max_pairs)
        self.pair_limit_selector.setPrefix("Max Pairs: ")
        self.pair_limit_selector.valueChanged.connect(self.set_max_pairs)

        self.prev_button = QPushButton("<< Prev")
        self.next_button = QPushButton("Next >>")
        self.prev_button.clicked.connect(self.go_prev)
        self.next_button.clicked.connect(self.go_next)

        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self.undo_annotation)

        self.label1 = QLabel("Frame: -")
        self.label2 = QLabel("Frame: -")

        self.image_view1 = ZoomPanGraphicsView()
        self.image_view2 = ZoomPanGraphicsView()
        self.image_view1.mousePressEvent = self.handle_click_frame1
        self.image_view2.mousePressEvent = self.handle_click_frame2

        self.save_button = QPushButton("Save Annotation")
        self.save_button.clicked.connect(self.export_to_kitti)


        main_layout = QVBoxLayout()

        # Top area: Load video + path
        load_layout = QHBoxLayout()
        load_layout.addWidget(self.load_button)
        load_layout.addWidget(self.video_path_label)
        main_layout.addLayout(load_layout)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.timestamp_input)
        slider_layout.addWidget(self.slider)
        main_layout.addLayout(slider_layout)

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.prev_button)
        control_layout.addWidget(self.offset_selector)
        control_layout.addWidget(self.next_button)
        control_layout.addWidget(self.pair_limit_selector)
        control_layout.addWidget(self.undo_button)
        control_layout.addWidget(self.save_button)
        main_layout.addLayout(control_layout)

        label_layout = QHBoxLayout()
        label_layout.addWidget(self.label1, alignment=Qt.AlignCenter)
        label_layout.addWidget(self.label2, alignment=Qt.AlignCenter)
        main_layout.addLayout(label_layout)

        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_view1)
        image_layout.addWidget(self.image_view2)
        main_layout.addLayout(image_layout)

        self.setLayout(main_layout)

    def set_max_pairs(self, val):
        self.max_pairs = val

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
            self.draw_annotations(frame1, frame=1)
        if frame2:
            self.label2.setText(f"Frame: {value + self.offset}")
            self.draw_annotations(frame2, frame=2)

        # Timestamp update
        seconds = int(self.frame_index / self.cap.get(cv2.CAP_PROP_FPS))
        minutes = seconds // 60
        seconds = seconds % 60
        self.timestamp_input.setText(f"{minutes:02}:{seconds:02}")

    def draw_annotations(self, qimage, frame):
        image = qimage.copy()
        painter = QPainter(image)
        cross_size = 6
        # Draw all saved annotations
        for i, (p1, p2) in enumerate(self.annotations):
            color = self.colors[i]
            pen = QPen(color, 1)
            painter.setPen(pen)

            # Convert the tuple points (x, y) to QPointF
            p1 = QPointF(p1[0], p1[1])
            p2 = QPointF(p2[0], p2[1])

            if frame == 1:
                painter.drawLine(QPointF(p1.x() - cross_size, p1.y()), QPointF(p1.x() + cross_size, p1.y()))
                painter.drawLine(QPointF(p1.x(), p1.y() - cross_size), QPointF(p1.x(), p1.y() + cross_size))
            elif frame == 2:
                painter.drawLine(QPointF(p2.x() - cross_size, p2.y()), QPointF(p2.x() + cross_size, p2.y()))
                painter.drawLine(QPointF(p2.x(), p2.y() - cross_size), QPointF(p2.x(), p2.y() + cross_size))

        # Draw the current temporary point in Frame 1 if it exists
        if frame == 1 and self.selected_frame1_point:
            pen = QPen(QColor("yellow"), 1)  # Temporary marker color
            painter.setPen(pen)
            point = QPointF(*self.selected_frame1_point)
            painter.drawLine(QPointF(point.x() - cross_size, point.y()), QPointF(point.x() + cross_size, point.y()))
            painter.drawLine(QPointF(point.x(), point.y() - cross_size), QPointF(point.x(), point.y() + cross_size))

        painter.end()

        if frame == 1:
            self.image_view1.set_image(image, reset_view=False)
        else:
            self.image_view2.set_image(image, reset_view=False)

    def handle_click_frame1(self, event):
        if len(self.annotations) >= self.max_pairs or self.selected_frame1_point is not None:
            return
        pos = event.pos()
        scene_pos = self.image_view1.mapToScene(pos)
        x, y = round(scene_pos.x()), round(scene_pos.y())
        print(f"Frame1 point selected: ({x:.1f}, {y:.1f})")
        self.selected_frame1_point = (int(round(scene_pos.x())), int(round(scene_pos.y())))
        self.draw_annotations(self.get_frame(self.frame_index), frame=1)

    def handle_click_frame2(self, event):
        if len(self.annotations) >= self.max_pairs or self.selected_frame1_point is None:
            return
        pos = event.pos()
        scene_pos = self.image_view2.mapToScene(pos)
        x, y = round(scene_pos.x()), round(scene_pos.y())
        print(f"Frame2 point selected: ({x:.1f}, {y:.1f})")
        self.selected_frame2_point = (int(round(scene_pos.x())), int(round(scene_pos.y())))
        self.annotations.append((self.selected_frame1_point, self.selected_frame2_point))
        self.colors.append(QColor(*[random.randint(0, 255) for _ in range(3)]))

        self.selected_frame1_point = None
        self.selected_frame2_point = None
        self.update_frames(self.frame_index)

    def undo_annotation(self):
        if self.annotations:
            last_pair = self.annotations[-1]
            self.annotations.pop()
            self.colors.pop()

            self.selected_frame1_point = None
            self.selected_frame2_point = None
            print(
                f"Undid last annotation: Frame 1 point {last_pair[0]} and Frame 2 point {last_pair[1]}")
            self.update_frames(self.frame_index)

    def update_frame_from_timestamp(self):
        timestamp = self.timestamp_input.text()
        if ':' not in timestamp:
            return
        minutes, seconds = map(int, timestamp.split(':'))
        frame_time = minutes * 60 + seconds
        frame_index = int(frame_time * self.cap.get(cv2.CAP_PROP_FPS))
        self.slider.setValue(min(frame_index, self.total_frames - 1))

    def go_prev(self):
        new_index = max(0, self.frame_index - 1)
        self.slider.setValue(new_index)

    def go_next(self):
        new_index = min(self.total_frames - self.offset - 1, self.frame_index + 1)
        self.slider.setValue(new_index)

    # Export the annotation to kitti format 
    def export_to_kitti(self):
        if not self.annotations:
            print("No annotations to export.")
            return

        export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not export_dir:
            return

        os.makedirs(os.path.join(export_dir, "flow_occ"), exist_ok=True)
        os.makedirs(os.path.join(export_dir, "image_2"), exist_ok=True)

        # Save the current image pair and flow
        img1 = self.get_frame(self.frame_index)
        img2 = self.get_frame(self.frame_index + self.offset)
    
        img1_rgb = qimage_to_rgb(img1)
        img2_rgb = qimage_to_rgb(img2)

        idx = f"{self.frame_index:06d}"

        # Save images as KITTI-compatible
        cv2.imwrite(os.path.join(export_dir, "image_2", f"{idx}_10.png"), cv2.cvtColor(img1_rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(os.path.join(export_dir, "image_2", f"{idx}_11.png"), cv2.cvtColor(img2_rgb, cv2.COLOR_RGB2BGR))

        # Save flow
        flow_h = img1.height()
        flow_w = img1.width()
        flow_img = np.zeros((flow_h, flow_w, 3), dtype=np.uint16)

        for ((x1, y1), (x2, y2)) in self.annotations:
            x1_int, y1_int = int(round(x1)), int(round(y1))
            dx = x2 - x1
            dy = y2 - y1

            # stores float flow values in 16-bit unsigned integers
            fx = int((dx * 64.0) + 2**15)
            fy = int((dy * 64.0) + 2**15)

            if 0 <= y1_int < flow_h and 0 <= x1_int < flow_w:
                flow_img[y1_int, x1_int, 0] = fx
                flow_img[y1_int, x1_int, 1] = fy
                flow_img[y1_int, x1_int, 2] = 1

        cv2.imwrite(os.path.join(export_dir, "flow_occ", f"{idx}_10.png"), flow_img)
        print(f"Saved frame {idx} pair and flow to: {export_dir}")



# Run the app
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoFrameComparer()
    window.show()
    sys.exit(app.exec_())
