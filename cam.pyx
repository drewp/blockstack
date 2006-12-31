# this runs the cmdline camgrab:
#cdef extern int camgrab_main(int argc, char *argv[])
#camgrab_main(0, NULL)

cdef extern from "Python.h":
    object PyBuffer_New(int size)
    int PyObject_AsWriteBuffer(object obj, void **buffer,
                               int *buffer_len) except -1
    object PyString_FromStringAndSize(char *v, int len)
    char* PyString_AsString(object string)
    
cdef extern from "pythread.h":
     ctypedef struct PyThreadState
     PyThreadState *PyEval_SaveThread()
     void PyEval_RestoreThread(PyThreadState *_save)

cdef extern from "sys/ioctl.h":
    int ioctl(int d, int request, ...)

#cdef extern from "X11/X.h":
#    pass

cdef extern from "linux/videodev.h":
    cdef struct video_mmap:
        unsigned int frame  # /* Frame (0 - n) for double buffer */
        int height,width    #
        unsigned int format # /* should be VIDEO_PALETTE_* */
    cdef int VIDIOCMCAPTURE, VIDIOCSYNC, VIDIOCGPICT, VIDIOCSPICT
    ctypedef unsigned short __u16
    cdef struct video_picture:
        __u16   brightness
        __u16   hue
        __u16   colour
        __u16   contrast

cdef extern void c_grab_init "grab_init" (char *grab_device)
cdef extern int grab_fd
cdef extern video_mmap grab_buf
cdef extern int grab_size
cdef extern unsigned char *grab_data

def grab_init(devname="/dev/video0"):
    c_grab_init(devname)

def grab_frame():
    cdef int i
    i = 0
    
    if grab_fd == -1:
        raise ValueError("Error in grab_one - not initialized")

    cdef PyThreadState *_save
    _save = PyEval_SaveThread()
     
    if ioctl(grab_fd, VIDIOCMCAPTURE, &grab_buf) == -1:
        PyEval_RestoreThread(_save)
        raise ValueError("ioctl VIDIOCMCAPTURE")

    if ioctl(grab_fd, VIDIOCSYNC, &i) == -1:
        PyEval_RestoreThread(_save)
        raise ValueError("ioctl VIDIOCSYNC")

    PyEval_RestoreThread(_save)

    # red/blue switch in-place on the mmap buffer
    i = 0
    while i < 352 * 288 * 3:
        grab_data[i], grab_data[i+2] = grab_data[i+2], grab_data[i]
        i = i + 3

     
    return PyString_FromStringAndSize(<char *>grab_data, grab_size)


def set_pict(contrast=None, brightness=None, hue=None, color=None):
    """input values from 0 to 1"""
    cdef video_picture cam_pic

    if ioctl(grab_fd, VIDIOCGPICT, &cam_pic) < 0:
        raise ValueError("getting pic info")
    if contrast is not None:
        cam_pic.contrast = 65535 * contrast
    if brightness is not None:
        cam_pic.brightness = 65535 * brightness
    if hue is not None:
        cam_pic.hue = 65535 * hue
    if color is not None:
        cam_pic.colour = 65535 * color
    if ioctl(grab_fd, VIDIOCSPICT, &cam_pic) < 0:
        raise ValueError("setting cam pic")
