import random
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QImage
from ui.zoom_pan_graphics_view import ZoomPanGraphicsView
from exporters.kitti_exporter import KITTIExporter

class VideoFrameComparer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Frame Comparer")
        self.setFixedSize(1950, 700)

        self.image_mode = False
        self.img1 = None
        self.img2 = None

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

        # TODO: Make a drop-down that allows us to set an output format when we need it.
        self.exporter = KITTIExporter()

        self.init_ui()

    def init_ui(self):
        QApplication.setStyle("fusion")

        self.load_button = QPushButton("Load Video")
        self.load_button.clicked.connect(self.load_video)
        self.load_image_pair_button = QPushButton("Load Image Pair")
        self.load_image_pair_button.clicked.connect(self.load_image_pair)
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
        load_layout.addWidget(self.load_image_pair_button)
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
        if self.image_mode:
            if index == 0:
                img = self.img1
            elif index == 1:
                img = self.img2
            else:
                return None
            h, w, ch = img.shape
            bytes_per_line = ch * w
            return QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)

        if index >= self.total_frames or self.cap is None:
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
        if self.image_mode:
            # Display two loaded images
            if self.img1 is not None:
                self.label1.setText("Image 1")
                qimg1 = self.get_frame(0)
                self.draw_annotations(qimg1, frame=1)

            if self.img2 is not None:
                self.label2.setText("Image 2")
                qimg2 = self.get_frame(1)
                self.draw_annotations(qimg2, frame=2)

            self.timestamp_input.setText("00:00")
            return

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
        if self.cap is None and not self.image_mode:
            QMessageBox.warning(self, "Error", "No video loaded.")
            return

        if len(self.annotations) >= self.max_pairs or self.selected_frame1_point is not None:
            return
        pos = event.pos()
        scene_pos = self.image_view1.mapToScene(pos)
        x, y = round(scene_pos.x()), round(scene_pos.y())
        print(f"Frame1 point selected: ({x:.1f}, {y:.1f})")
        self.selected_frame1_point = (int(round(scene_pos.x())), int(round(scene_pos.y())))
        self.draw_annotations(self.get_frame(self.frame_index), frame=1)

    def handle_click_frame2(self, event):
        if self.cap is None and not self.image_mode:
            QMessageBox.warning(self, "Error", "No video loaded.")
            return

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

    def clear_annotations(self):
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

    def load_image_pair(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, "Open Image Pair", "", "Image Files (*.jpg *.jpeg *.png)")
        if len(file_names) != 2:
            QMessageBox.warning(self, "Error", "Please select exactly 2 image files.")
            return

        try:
            img1 = cv2.imread(file_names[0])
            img2 = cv2.imread(file_names[1])
            if img1 is None or img2 is None:
                raise ValueError("One or both images could not be loaded.")

            # Convert BGR to RGB and store
            self.img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
            self.img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)
            self.image_mode = True

            self.cap = None  # disable video mode
            self.frame_index = 0
            self.total_frames = 2
            self.video_path_label.setText("Loaded image pair")

            # Hide video-specific controls
            self.slider.setVisible(False)
            self.timestamp_input.setVisible(False)
            self.offset_selector.setVisible(False)

            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)

            self.update_frames(0)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
