import numpy as np

def qimage_to_rgb(qimage):
    ptr = qimage.bits()
    ptr.setsize(qimage.byteCount())
    arr = np.array(ptr).reshape(qimage.height(), qimage.width(), 3)
    return arr