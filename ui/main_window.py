import math
import random
import cv2
import numpy as np
from scipy.spatial import ConvexHull
from scipy.interpolate import griddata
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QImage
from ui.zoom_pan_graphics_view import ZoomPanGraphicsView
from exporters.kitti_exporter import KITTIExporter

class VideoFrameComparer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Frame Comparer")
        self.setMinimumSize(1900,1000)

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
        self.export_dir=""

        self.convex_hull_pairs = []
        self.is_convex_hull_mode = False

        # TODO: Make a drop-down that allows us to set an output format when we need it.
        self.exporter = KITTIExporter()

        self.init_ui()

    def init_ui(self):
        QApplication.setStyle("fusion")

        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        self.video_path_label = QLabel("No video loaded")

        self.export_path_button = QPushButton("Set export path")
        self.export_path_button.clicked.connect(self.set_export_path)
        self.export_path_label = QLabel("Not set")

        self.mode_group = QButtonGroup(self)
        self.point_mode_radio = QRadioButton("Point Mode")
        self.convex_hull_mode_radio = QRadioButton("Convex Hull Mode")
        self.point_mode_radio.setChecked(True)
        self.mode_group.addButton(self.point_mode_radio)
        self.mode_group.addButton(self.convex_hull_mode_radio)
        self.point_mode_radio.toggled.connect(self.on_mode_changed)
        self.convex_hull_mode_radio.toggled.connect(self.on_mode_changed)

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

        self.label1 = QLabel("Frame: -")
        self.label2 = QLabel("Frame: -")

        self.image_view1 = ZoomPanGraphicsView()
        self.image_view2 = ZoomPanGraphicsView()
        self.image_view1.leftClick.connect(self.handle_click_frame1)
        self.image_view2.leftClick.connect(self.handle_click_frame2)

        self.image_view1.sync_with(self.image_view2)

        self.save_button = QPushButton("Save Annotation")
        self.save_button.clicked.connect(self.export_annotations)

        main_layout = QVBoxLayout()

        load_layout = QHBoxLayout()
        load_layout.addWidget(self.load_button)
        load_layout.addWidget(self.video_path_label)
        main_layout.addLayout(load_layout)

        export_layout = QHBoxLayout()
        export_layout.addWidget(self.export_path_button)
        export_layout.addWidget(self.export_path_label)
        main_layout.addLayout(export_layout)

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
        control_layout.addWidget(self.point_mode_radio)
        control_layout.addWidget(self.convex_hull_mode_radio)
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

    def set_export_path(self):
        self.export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if self.export_dir:
            self.export_path_label.setText(self.export_dir)
        else:
            self.export_path_label.setText("Not set")

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

    def draw_annotations(self, qimage, frame):
        image = qimage.copy()
        painter = QPainter(image)
        cross_size = 6
        for i, (p1, p2) in enumerate(self.annotations):
            color = self.colors[i]
            pen = QPen(color, 1)
            painter.setPen(pen)

            p1 = QPointF(p1[0], p1[1])
            p2 = QPointF(p2[0], p2[1])

            if frame == 1:
                painter.drawLine(QPointF(p1.x() - cross_size, p1.y()), QPointF(p1.x() + cross_size, p1.y()))
                painter.drawLine(QPointF(p1.x(), p1.y() - cross_size), QPointF(p1.x(), p1.y() + cross_size))
            elif frame == 2:
                painter.drawLine(QPointF(p2.x() - cross_size, p2.y()), QPointF(p2.x() + cross_size, p2.y()))
                painter.drawLine(QPointF(p2.x(), p2.y() - cross_size), QPointF(p2.x(), p2.y() + cross_size))

        if self.is_convex_hull_mode and self.convex_hull_pairs:
            pen = QPen(QColor("cyan"), 1)
            painter.setPen(pen)
            
            # Draw point annotation markers
            points = []
            for p1, p2 in self.convex_hull_pairs:
                point = p1 if frame == 1 else p2
                points.append(point)
                p = QPointF(point[0], point[1])
                painter.drawLine(QPointF(p.x() - cross_size, p.y()), QPointF(p.x() + cross_size, p.y()))
                painter.drawLine(QPointF(p.x(), p.y() - cross_size), QPointF(p.x(), p.y() + cross_size))

            qpoints = []            
            if len(points) >= 3:
                hull = ConvexHull(points)
                qpoints = [QPointF(p[0],p[1]) for p in hull.points[hull.vertices]]
            else:
                qpoints = [QPointF(p[0],p[1]) for p in points]
            
            # Draw convex hull outlint
            for p1, p2 in zip(qpoints, qpoints[1:] + [qpoints[0]]):
                painter.drawLine(p1, p2)

        if frame == 1 and self.selected_frame1_point:
            pen = QPen(QColor("yellow"), 1)
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
        if self.cap is None:
            QMessageBox.warning(self, "Error", "No video loaded.")
            return

        if len(self.annotations) >= self.max_pairs or self.selected_frame1_point is not None:
            return
        pos = event.pos()
        scene_pos = self.image_view1.mapToScene(pos)
        x, y = math.floor(scene_pos.x()), math.floor(scene_pos.y())
        print(f"Frame1 point selected: ({x:.1f}, {y:.1f})")
        self.selected_frame1_point = (int(math.floor(scene_pos.x())), int(math.floor(scene_pos.y())))
        self.draw_annotations(self.get_frame(self.frame_index), frame=1)

    def handle_click_frame2(self, event):
        if self.cap is None:
            QMessageBox.warning(self, "Error", "No video loaded.")
            return

        if len(self.annotations) >= self.max_pairs or self.selected_frame1_point is None:
            return
        pos = event.pos()
        scene_pos = self.image_view2.mapToScene(pos)
        x, y = math.floor(scene_pos.x()), math.floor(scene_pos.y())
        print(f"Frame2 point selected: ({x:.1f}, {y:.1f})")
        self.selected_frame2_point = (int(math.floor(scene_pos.x())), int(math.floor(scene_pos.y())))
        self.annotations.append((self.selected_frame1_point, self.selected_frame2_point))
        self.colors.append(QColor(*[random.randint(0, 255) for _ in range(3)]))
        if self.is_convex_hull_mode:
            self.convex_hull_pairs.append((self.selected_frame1_point, self.selected_frame2_point))
        else:
            self.annotations.append((self.selected_frame1_point, self.selected_frame2_point))
            self.colors.append(QColor(*[random.randint(0, 255) for _ in range(3)]))

        self.selected_frame1_point = None
        self.selected_frame2_point = None
        self.update_frames(self.frame_index)

    def undo_annotation(self):
        if self.is_convex_hull_mode:
            if self.convex_hull_pairs:
                self.convex_hull_pairs.pop()
            self.update_frames(self.frame_index)
            return

        if self.annotations:
            last_pair = self.annotations[-1]
            self.annotations.pop()
            self.colors.pop()

            self.selected_frame1_point = None
            self.selected_frame2_point = None
            print(
                f"Undid last annotation: Frame 1 point {last_pair[0]} and Frame 2 point {last_pair[1]}")
            self.update_frames(self.frame_index)

    def clear_annotations(self):
        self.convex_hull_points = []
        self.convex_hull_pairs = []
        self.annotations = []
        self.colors = []
        self.selected_frame1_point = None
        self.selected_frame2_point = None
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

    def on_mode_changed(self, checked):
        if checked:
            self.is_convex_hull_mode = self.convex_hull_mode_radio.isChecked()
            self.update_frames(self.frame_index)

    def export_annotations(self):
        num_convex_hull_pairs = len(self.convex_hull_pairs)
        if not self.annotations and num_convex_hull_pairs == 0:
            QMessageBox.warning(self, "Error", "No annotations to export.")
            return

        if not self.export_dir:
            QMessageBox.warning(self, "Error", "No export directory selected.")
            return

        img1 = self.get_frame(self.frame_index)
        img2 = self.get_frame(self.frame_index + self.offset)

        if img1 is None or img2 is None:
            QMessageBox.warning(self, "Error", "Failed to retrieve frames for export.")
            return
        
        annotations = list(self.annotations)

        if num_convex_hull_pairs > 0 and num_convex_hull_pairs < 3:
            QMessageBox.warning(self, "Error", "Not enough convex hull annotation pairs")
            return

        if num_convex_hull_pairs >= 3:
            flow_w = img1.width()
            flow_h = img1.height()

            points = np.array([p1 for p1, _ in self.convex_hull_pairs], dtype=np.float32)
            flows = np.array([(p2[0] - p1[0], p2[1] - p1[1]) for p1, p2 in self.convex_hull_pairs], dtype=np.float32)

            hull = ConvexHull(points)
            hull_points = points[hull.vertices]

            mask = np.zeros((flow_h, flow_w), dtype=np.uint8)
            cv2.fillPoly(mask, [np.round(hull_points).astype(np.int32)], 1)

            y, x = np.nonzero(mask)
            inside_points = np.column_stack((x, y)).astype(np.float32)

            inside_flows = griddata(points, flows, inside_points, method='linear')
            valid_mask = ~np.isnan(inside_flows).any(axis=1)
            valid_points = inside_points[valid_mask]
            valid_flows = inside_flows[valid_mask]

            for point, flow in zip(valid_points, valid_flows):
                point_a = (int(point[0]), int(point[1]))
                point_b = (int(point[0] + flow[0]), int(point[1] + flow[1]))
                annotations.append((point_a,point_b))

        self.exporter.export(annotations, self.frame_index, img1, img2, self.export_dir)