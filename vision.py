from __future__ import division
import gtk, gst, goocanvas, numpy, cv2,  time
from timing import logTime
from louie import dispatcher
from play import colorPairs

def labeledScale(name, config):
    row = gtk.VBox()
    row.pack_start(gtk.Label(name))
    adj = gtk.Adjustment(lower=config['minimum'],
                         upper=config['maximum'],
                         step_incr=config['step'],
                         value=config['value'])

    scl = gtk.HScale(adj)
    scl.set_digits(2)
    scl.set_property('value-pos', gtk.POS_LEFT)
    row.pack_start(scl)
    return row, adj

class BlockHues(object):
    """sliders for picking the center hue of each block color"""
    def __init__(self, parent):
        self.colors = ['yellow', 'green', 'blue', 'purple']
        self.adjs = {}
        for color in self.colors:

            row, adj = labeledScale(
                color,
                dict(minimum=0, maximum=1, step=.01,
                     # i could take a pic of all the blocks and
                     # cluster the hues to get these
                     value=0))
            self.adjs[color] = adj
            parent.pack_start(row)
        parent.show_all()

    def getHue(self, color):
        return self.adjs[color].get_value()
    
    def previewColor(self, color):
        dot = numpy.array([[[self.getHue(color) * 255, 255, 255]]],
                          dtype=numpy.uint8)
        # opencv's hues are a little fishy- h=180/255 is the same red
        # as h=0/255, but at least I'm consistent with the image xform
        conv = cv2.cvtColor(dot, cv2.COLOR_HSV2RGB)
        return conv[0][0] / 255.

class VideoPipeline(object):
    """
    gstreamer pipeline from input video to display

    check out frei0r-filter-k-means-clustering too!
    """
    def __init__(self, videoDevice, rawVideoWidget, hueWidget, hueMatchVideo,
                 blobBox,
                 adjGet, blockHues,
                 onFrame,
                 cameraArea,
                 pipelineSection,
                 ):
        self.videoDevice = videoDevice
        self.adjGet = adjGet
        self.blockHues = blockHues
        self.hueWidget = hueWidget
        self.hueMatchVideo = hueMatchVideo
        self.pipelineSection = pipelineSection
        
        source = "v4l2src device=%(videoDevice)s name=src ! " % vars()
        if 0:
            source = "videotestsrc is-live=true name=src ! "
        pipe = (source +
                "videorate name=vidrate ! "
                "video/x-raw-rgb,framerate=30/1,width=640,height=480 ! "
                "queue ! videoflip method=4 ! "
                "tee name=t ! "
                "queue ! ffmpegcolorspace ! xvimagesink name=previewSink t. ! "
                "queue ! videoscale ! video/x-raw-rgb,width=160,height=120 ! "
                "gdkpixbufsink name=sink"
                )
        self.pipeline = gst.parse_launch(pipe)

        previewSink = self.pipeline.get_by_name("previewSink")
        previewSink.set_xwindow_id(cameraArea.window.xid)

        sink = self.pipeline.get_by_name("sink")

        pixbufTimes = []
        def onMsg(bus, msg):
            if msg.src == sink and msg.structure.get_name() == 'pixbuf':

                now = time.time()
                pixbufTimes[:] = [t for t in pixbufTimes if t > now - 5] + [now]
                dispatcher.send("videoStats",
                                txt="fps = %.1f" % (len(pixbufTimes) / 5.))

                pb = msg.structure['pixbuf']
                self.previewEnabled = self.pipelineSection.get_property(
                    "expanded")
                if self.previewEnabled:
                    rawVideoWidget.set_from_pixbuf(pb)
                hue, mask = self.updateHuePic(pb)
                matches = self.updateHueMatchPic(hue, mask)
                centers = self.updateBlobPic(matches)
                onFrame(centers)
            return True

        bus = self.pipeline.get_bus()
        bus.add_watch(onMsg)
        
        self.pipeline.set_state(gst.STATE_PLAYING)

        self.blobCanvas = goocanvas.Canvas()
        self.blobCanvas.set_size_request(160, 120)
        blobBox.pack_start(self.blobCanvas)
        self.blobCanvas.show()
        self.blobCanvasGroup = None

        self.recentCenters = []

    def updateHuePic(self, pixbuf):
        a = pixbuf.get_pixels_array().astype(numpy.uint8)
        hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV)
        hue255 = hsv[:,:,0]
        mask = (
            (hsv[:,:,2] > (255 * self.adjGet("minValue"))) *
            (hsv[:,:,1] > (255 * self.adjGet("minSaturation")))).reshape(hue255.shape[:2])
        if self.previewEnabled:
            self.previewHue(hue255, mask)
        return hue255 / 255, mask

    def previewHue(self, hue255, mask):
        hsv = numpy.dstack([hue255,
                            numpy.ones(hue255.shape) * 255,
                            mask * 255]).astype(numpy.uint8)
        hsv = hsv.copy('C') # opencv would try to transpose this to 'fix' it
        pic = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        self.hueWidget.set_from_pixbuf(
            gtk.gdk.pixbuf_new_from_array(pic, gtk.gdk.COLORSPACE_RGB, 8))

    def updateHueMatchPic(self, hue, mask):
        matches = {}
        for color in self.blockHues.colors:
            center = self.blockHues.getHue(color)
            diff = abs(hue - center)
            matches[color] = mask * (diff < self.adjGet("hueDistance"))
        if self.previewEnabled:
            self.previewHueMatch(hue, matches)
        return matches

    def previewHueMatch(self, hue, matches):
        out = numpy.zeros(hue.shape + (3,))
        for color in self.blockHues.colors:
            out = numpy.choose(matches[color].reshape(hue.shape+(1,)),
                               [out, self.blockHues.previewColor(color)])
            
        self.hueMatchVideo.set_from_pixbuf(
            gtk.gdk.pixbuf_new_from_array((out * 255).astype(numpy.uint8),
                                          gtk.gdk.COLORSPACE_RGB, 8))
        
    def updateBlobPic(self, matches):
        centers = {}  # color: (x,y,coverage)
        for color, hits in matches.items():
            coords = numpy.transpose(numpy.nonzero(hits))
            if coords.shape[0]:
                center = numpy.average(coords, axis=0)
                coverage = coords.shape[0] / (hits.shape[0] * hits.shape[1])
                if coverage > self.adjGet("minCoverage"):
                    centers[color] = (center[1], center[0], coverage)

        rf = int(self.adjGet("recentFrames"))
        if rf == 0:
            self.recentCenters = [centers]
        else:
            self.recentCenters = self.recentCenters[-rf:] + [centers]

        avgCenters = {}
        for color in centers:
            x, y = numpy.average([c[color][:2] for c in self.recentCenters
                                  if color in c], axis=0)
            avgCenters[color] = (x,y)
        if self.previewEnabled:
            self.previewCanvas(avgCenters)
        return avgCenters
    
    def previewCanvas(self, centers):
                
        root = self.blobCanvas.get_root_item()
        if self.blobCanvasGroup is not None:
            self.blobCanvasGroup.remove()
        self.blobCanvasGroup = goocanvas.Group(parent=root)
        toDraw = {}
        for color, (x,y) in centers.items():
            fill = "#%02X%02X%02X" % tuple(c*255 for c in
                                           self.blockHues.previewColor(color))

            toDraw[color] = (x, y, fill)

        for color, (x, y, fill) in toDraw.items():
            r = 10
            goocanvas.Rect(parent=self.blobCanvasGroup,
                           x=x-r/2, y=y-r/2, width=r, height=r,
                           line_width=.7,
                           fill_color=fill)

        def line(p1, p2):
            goocanvas.Polyline(parent=self.blobCanvasGroup,
                               points=goocanvas.Points([p1, p2]),
                               line_width=2,
                               stroke_color='black',
                               end_arrow=True)

        # this will be lines like what's used for comparisons, but
        # they might not be exactly the same ones
        for c1, c2 in colorPairs(toDraw.keys()):
            line(toDraw[c1][:2], toDraw[c2][:2])
    
    def __del__(self):
        self.pipeline.set_state(gst.STATE_NULL)
