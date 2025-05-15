import random
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QImage
from ui.zoom_pan_graphics_view import ZoomPanGraphicsView
from exporters.kitti_exporter import KITTIExporter
import numpy as np

class VideoFrameComparer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Frame Comparer")
        self.setFixedSize(1850, 700)

        self.cap = None
        self.total_frames = 0
        self.frame_index = 0
        self.offset = 1
        self.video_path = ""
        self.mode = "Manual"  # or "Homography"
        self.helper_annotations = []
        self.annotations = []
        self.selected_frame1_point = None
        self.selected_frame2_point = None
        self.predicted_point = None
        self.max_pairs = 10
        self.colors = []

        # TODO: Make a drop-down that allows us to set an output format when we need it.
        self.exporter = KITTIExporter()

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

        self.clear_all_annotations_button = QPushButton("Clear all")
        self.clear_all_annotations_button.clicked.connect(self.clear_annotations)

        self.mode_label = QLabel("Mode: Manual")
        self.mode_label.setStyleSheet("font-weight: bold; color: green")
        self.mode_toggle = QPushButton("Toggle Mode")
        self.mode_toggle.clicked.connect(self.toggle_mode)

        self.suggest_button = QPushButton("Suggest Match")
        self.suggest_button.clicked.connect(self.suggest_match)

        self.label1 = QLabel("Frame: -")
        self.label2 = QLabel("Frame: -")

        self.image_view1 = ZoomPanGraphicsView()
        self.image_view2 = ZoomPanGraphicsView()
        self.image_view1.mousePressEvent = self.handle_click_frame1
        self.image_view2.mousePressEvent = self.handle_click_frame2

        self.save_button = QPushButton("Save Annotation")
        self.save_button.clicked.connect(self.export_annotations)

        main_layout = QVBoxLayout()

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
        control_layout.addWidget(self.clear_all_annotations_button)
        control_layout.addWidget(self.suggest_button)
        control_layout.addWidget(self.mode_label)
        control_layout.addWidget(self.mode_toggle)
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
            QMessageBox.warning(self, "Error", "No video file selected.")
            return

        self.cap = cv2.VideoCapture(file_name)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Error", "Failed to open video file.")
            return

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
            QMessageBox.warning(self, "Error", "Failed to retrieve frame.")
            return None
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        return QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

    def update_frames(self, value):
        if self.cap is None:
            QMessageBox.warning(self, "Error", "No video loaded.")
            return

        self.frame_index = value
        frame1 = self.get_frame(value)
        frame2 = self.get_frame(value + self.offset)

        if frame1:
            self.label1.setText(f"Frame: {value}")
            self.draw_annotations(frame1, frame=1)
        if frame2:
            self.label2.setText(f"Frame: {value + self.offset}")
            self.draw_annotations(frame2, frame=2)

        seconds = int(self.frame_index / self.cap.get(cv2.CAP_PROP_FPS))
        minutes = seconds // 60
        seconds = seconds % 60
        self.timestamp_input.setText(f"{minutes:02}:{seconds:02}")

    def toggle_mode(self):
        if self.mode == "Manual":
            self.mode = "Homography"
            self.mode_label.setText("Mode: Homography")
            self.mode_label.setStyleSheet("font-weight: bold; color: orange")
        else:
            self.mode = "Manual"
            self.mode_label.setText("Mode: Manual")
            self.mode_label.setStyleSheet("font-weight: bold; color: green")

    def draw_annotations(self, qimage, frame):
        image = qimage.copy()
        painter = QPainter(image)
        cross_size = 6

        if self.mode == "Manual":
            for i, (p1, p2) in enumerate(self.annotations):
                color = self.colors[i]
                pen = QPen(color, 1)
                painter.setPen(pen)

                p = QPointF(*(p1 if frame == 1 else p2))
                painter.drawLine(QPointF(p.x() - cross_size, p.y()), QPointF(p.x() + cross_size, p.y()))
                painter.drawLine(QPointF(p.x(), p.y() - cross_size), QPointF(p.x(), p.y() + cross_size))
        elif self.mode == "Homography":
            for i, (p1, p2) in enumerate(self.helper_annotations):
                color = self.colors[i]
                pen = QPen(color, 1)
                painter.setPen(pen)

                p = QPointF(*(p1 if frame == 1 else p2))
                painter.drawLine(QPointF(p.x() - cross_size, p.y()), QPointF(p.x() + cross_size, p.y()))
                painter.drawLine(QPointF(p.x(), p.y() - cross_size), QPointF(p.x(), p.y() + cross_size))

        # Draw KITTI crop rectangle
        full_h, full_w = image.height(), image.width()
        crop_w, crop_h = 1242, 375
        crop_x1 = (full_w - crop_w) // 2
        crop_y1 = (full_h - crop_h) // 2

        pen = QPen(QColor(255, 0, 0), 1, Qt.DashLine)  # Red dashed line
        painter.setPen(pen)
        painter.drawRect(crop_x1, crop_y1, crop_w, crop_h)

        if frame == 1 and self.selected_frame1_point:
            pen = QPen(QColor("yellow"), 1)
            painter.setPen(pen)
            point = QPointF(*self.selected_frame1_point)
            painter.drawLine(QPointF(point.x() - cross_size, point.y()), QPointF(point.x() + cross_size, point.y()))
            painter.drawLine(QPointF(point.x(), point.y() - cross_size), QPointF(point.x(), point.y() + cross_size))

        # Draw predicted point
        if frame == 2 and self.mode=="Homography" and self.predicted_point:
            pen = QPen(QColor("cyan"), 1)
            painter.setPen(pen)
            px, py = self.predicted_point
            painter.drawLine(QPointF(px - cross_size, py), QPointF(px + cross_size, py))
            painter.drawLine(QPointF(px, py - cross_size), QPointF(px, py + cross_size))

        painter.end()

        if frame == 1:
            self.image_view1.set_image(image, reset_view=False)
        else:
            self.image_view2.set_image(image, reset_view=False)

    def suggest_match(self):
        if self.selected_frame1_point is None or len(self.helper_annotations) < 4:
            QMessageBox.information(self, "Info",
                                    "Need at least four existing annotations and a selected Frame 1 point.")
            return

        src_pts = np.array([p1 for p1, _ in self.helper_annotations], dtype=np.float32)
        dst_pts = np.array([p2 for _, p2 in self.helper_annotations], dtype=np.float32)

        if len(src_pts) < 4:
            QMessageBox.warning(self, "Not enough points", "Need at least 4 point pairs to compute homography.")
            return

        H, status = cv2.findHomography(src_pts, dst_pts, method=0)
        if H is None:
            QMessageBox.warning(self, "Homography failed", "Could not compute homography.")
            self.predicted_point = None
            return

        selected_pt = np.array([[self.selected_frame1_point]], dtype=np.float32)
        pred_pt = cv2.perspectiveTransform(selected_pt, H)

        self.predicted_point = tuple(map(int, pred_pt[0][0]))
        print(f"Predicted Frame2 point: {self.predicted_point}")

        self.annotations.append((self.selected_frame1_point, self.predicted_point))
        self.draw_annotations(self.get_frame(self.frame_index + self.offset), frame=2)

        self.colors.append(QColor(*[random.randint(0, 255) for _ in range(3)]))
        print(self.annotations)
        print(self.helper_annotations)
        self.update_frames(self.frame_index)
        self.selected_frame1_point = None
        self.predicted_point = None

    def handle_click_frame1(self, event):
        if self.cap is None:
            QMessageBox.warning(self, "Error", "No video loaded.")
            return

        if self.mode == "Manual" and (
                len(self.annotations) >= self.max_pairs or self.selected_frame1_point is not None):
            return
        if self.mode == "Homography" and self.selected_frame1_point is not None:
            return

        pos = event.pos()
        scene_pos = self.image_view1.mapToScene(pos)
        x, y = scene_pos.x(), scene_pos.y()

        frame_rgb = self.get_frame(self.frame_index)

        ptr = frame_rgb.bits()
        ptr.setsize(frame_rgb.byteCount())
        arr = np.array(ptr).reshape((frame_rgb.height(), frame_rgb.width(), 3))
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        point = np.array([[[x, y]]], dtype=np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
        refined = cv2.cornerSubPix(gray, point, winSize=(5, 5), zeroZone=(-1, -1), criteria=criteria)

        rx, ry = float(refined[0][0][0]), float(refined[0][0][1])
        self.selected_frame1_point = (int(round(rx)), int(round(ry)))
        print(f"Refined point: ({rx:.2f}, {ry:.2f})")

        self.update_frames(self.frame_index)

    def handle_click_frame2(self, event):
        if self.cap is None:
            QMessageBox.warning(self, "Error", "No video loaded.")
            return

        if self.mode == "Manual" and len(self.annotations) >= self.max_pairs:
            return


        pos = event.pos()
        scene_pos = self.image_view2.mapToScene(pos)
        x, y = scene_pos.x(), scene_pos.y()

        frame_rgb = self.get_frame(self.frame_index)
        ptr = frame_rgb.bits()
        ptr.setsize(frame_rgb.byteCount())
        arr = np.array(ptr).reshape((frame_rgb.height(), frame_rgb.width(), 3))
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        point = np.array([[[x, y]]], dtype=np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
        refined = cv2.cornerSubPix(gray, point, winSize=(5, 5), zeroZone=(-1, -1), criteria=criteria)

        rx, ry = float(refined[0][0][0]), float(refined[0][0][1])
        self.selected_frame2_point = (int(round(rx)), int(round(ry)))
        print(f"Refined point: ({rx:.2f}, {ry:.2f})")

        if self.mode == "Manual":
            if len(self.annotations) < self.max_pairs:
                if self.selected_frame1_point is not None and self.selected_frame2_point is not None:
                    self.annotations.append((self.selected_frame1_point, self.selected_frame2_point))
                    self.colors.append(QColor(*[random.randint(0, 255) for _ in range(3)]))
            else:
                pass

        if self.mode == "Homography":
            if self.selected_frame1_point is not None and self.selected_frame2_point is not None:
                self.helper_annotations.append((self.selected_frame1_point, self.selected_frame2_point))
                self.colors.append(QColor(*[random.randint(0, 255) for _ in range(3)]))

        self.selected_frame1_point = None
        self.selected_frame2_point = None
        self.update_frames(self.frame_index)

    def qimage_to_mat(self, qimage):
        """Convert QImage to OpenCV BGR image."""
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        arr = np.array(ptr).reshape((height, width, 3))
        return arr.copy()

    def undo_annotation(self):
        if self.mode == "Homography":
            if self.helper_annotations:
                removed = self.helper_annotations.pop()
                print(f"Undid helper point: Frame 1 point {removed[0]}")
                print(self.helper_annotations)
        else:
            if self.annotations:
                removed = self.annotations.pop()
                self.colors.pop()
                print(f"Undid manual annotation: {removed}")
                print(self.annotations)

        self.selected_frame1_point = None
        self.selected_frame2_point = None
        self.predicted_point = None
        self.update_frames(self.frame_index)

    def clear_annotations(self):
        self.annotations = []
        self.helper_annotations = []
        self.colors = []
        self.selected_frame1_point = None
        self.selected_frame2_point = None
        self.predicted_point = None
        self.update_frames(self.frame_index)
        print("Cleared all annotations for a new pair of frames.")

    def update_frame_from_timestamp(self):
        timestamp = self.timestamp_input.text()
        if ':' not in timestamp:
            return
        minutes, seconds = map(int, timestamp.split(':'))
        frame_time = minutes * 60 + seconds
        frame_index = int(frame_time * self.cap.get(cv2.CAP_PROP_FPS))
        self.slider.setValue(min(frame_index, self.total_frames - 1))

    def go_prev(self):
        if self.cap is None:
            QMessageBox.warning(self, "Error", "No video loaded.")
            return
        new_index = max(0, self.frame_index - 1)
        self.slider.setValue(new_index)

    def go_next(self):
        if self.cap is None:
            QMessageBox.warning(self, "Error", "No video loaded.")
            return
        new_index = min(self.total_frames - self.offset - 1, self.frame_index + 1)
        self.slider.setValue(new_index)


    def export_annotations(self):
        if not self.annotations:
            QMessageBox.warning(self, "Error", "No annotations to export.")
            return

        export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not export_dir:
            QMessageBox.warning(self, "Error", "No export directory selected.")
            return

        img1 = self.get_frame(self.frame_index)
        img2 = self.get_frame(self.frame_index + self.offset)

        if img1 is None or img2 is None:
            QMessageBox.warning(self, "Error", "Failed to retrieve frames for export.")
            return

        self.exporter.export(self.annotations, self.frame_index, img1, img2, export_dir)