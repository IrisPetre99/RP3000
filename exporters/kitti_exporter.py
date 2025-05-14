import os
import re
import cv2
import numpy as np
from exporters.exporter import Exporter
from utils.image_utils import qimage_to_rgb

class KITTIExporter(Exporter):
    def export(self, annotations, frame_index, img1, img2, export_dir):
        img1_rgb = qimage_to_rgb(img1)
        img2_rgb = qimage_to_rgb(img2)

        files = os.listdir(os.path.join(export_dir, "image_2"))
        largest_index = 0
        pattern=re.compile(r'^(\d{6})_\d{2}\.png$')
        for filename in files:
            match = pattern.match(filename)
            if match:
                index = int(match.group(1))
                largest_index = max(largest_index, index)

        idx = f"{largest_index+1:06d}"

        os.makedirs(os.path.join(export_dir, "flow_occ"), exist_ok=True)
        os.makedirs(os.path.join(export_dir, "image_2"), exist_ok=True)

        cv2.imwrite(os.path.join(export_dir, "image_2", f"{idx}_10.png"), cv2.cvtColor(img1_rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(os.path.join(export_dir, "image_2", f"{idx}_11.png"), cv2.cvtColor(img2_rgb, cv2.COLOR_RGB2BGR))

        flow_h = img1.height()
        flow_w = img1.width()
        flow_img = np.zeros((flow_h, flow_w, 3), dtype=np.uint16)

        for ((x1, y1), (x2, y2)) in annotations:
            x1_int, y1_int = int(round(x1)), int(round(y1))
            dx = x2 - x1
            dy = y2 - y1

            fx = int((dx * 64.0) + 2**15)
            fy = int((dy * 64.0) + 2**15)

            if 0 <= y1_int < flow_h and 0 <= x1_int < flow_w:
                flow_img[y1_int, x1_int, 0] = 1
                flow_img[y1_int, x1_int, 1] = fx
                flow_img[y1_int, x1_int, 2] = fy

        cv2.imwrite(os.path.join(export_dir, "flow_occ", f"{idx}_10.png"), flow_img)
        print(f"Saved frame {idx} pair and flow to: {export_dir}")