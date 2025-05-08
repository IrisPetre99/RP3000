from PyQt5.QtGui import QImage
from qimage2ndarray import rgb_view

def qimage_to_rgb(qimage):
    try:
        if qimage.format() != QImage.Format_RGB32:
            qimage = qimage.convertToFormat(QImage.Format_RGB32)
        return rgb_view(qimage)
    except Exception as e:
        raise RuntimeError(f"Failed to convert QImage to RGB: {str(e)}")