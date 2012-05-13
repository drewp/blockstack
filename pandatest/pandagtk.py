
import gtk, gtk.glade
import sys
import platform
from functools import partial
# ==
from pandac.PandaModules          import loadPrcFileData, WindowProperties
from direct.task                  import Task
from direct.showbase.DirectObject import DirectObject
from panda3d.core import PointLight,Spotlight, Vec4, Vec3, VBase4, PerspectiveLens, PandaNode
from panda3d.core import AmbientLight,DirectionalLight


# == PANDA SETUP == #


def launch_panda_window(panda_widget, size) :
    """
    Configure and create Panda window
    Connect to the gtk widget resize event
    Load a panda
    """
    props = WindowProperties().getDefault()
    props.setOrigin(0, 0)
    props.setSize(*size)
    props.setParentWindow(panda_widget.window.xid)
    base.openDefaultWindow(props=props)
    # ==
    panda_widget.connect("size_allocate", resize_panda_window)
    # ==
    panda = loader.loadModel("panda")
    panda.reparentTo(render)
    panda.setPos(0, 40, -5)

    pl = render.attachNewNode( PointLight( "redPointLight" ) )
    pl.node().setColor( Vec4( .9, .8, .8, 1 ) )
    render.setLight(pl)
    pl.node().setAttenuation( Vec3( 0, 0, 0.05 ) ) 


    slight = Spotlight('slight')
    slight.setColor(VBase4(1, 1, 1, 1))
    lens = PerspectiveLens()
    slight.setLens(lens)
    slnp = render.attachNewNode(slight)
    slnp.setPos(2, 20, 0)
    mid = PandaNode('mid')
    panda.attachNewNode(mid)
#    slnp.lookAt(mid)
    render.setLight(slnp)
    

def resize_panda_window(widget, request) :
    """ Connected to resize event of the widget Panda is draw on so that the Panda window update its size """
    props = WindowProperties().getDefault()
    props = WindowProperties(base.win.getProperties())
    props.setOrigin(0, 0)
    props.setSize(request.width, request.height)
    props.setParentWindow(widget.window.xid)
    base.win.requestProperties(props)

# == GTK SETUP == #

def gtk_iteration(*args, **kw):
    """ We handle the gtk events in this task added to Panda TaskManager """
    while gtk.events_pending():
        gtk.main_iteration_do(False)
    return Task.cont

def launch_gtk_window(size) :
    """
    Here we create the gtk window and all its content (usually I load it from a gladefile).
    We return the widget where we want the Panda Window to be drawn
    """
    # == Main window
    window = gtk.Window()
    window.resize(*size)
    # == A VBox in which we'll put 2 HBox
    vbox = gtk.VBox()
    window.add(vbox)
    # == First HBox with just a Button in it
    top_hbox = gtk.HBox()
    vbox.pack_start(top_hbox, expand = False)
    # ==
    image = gtk.Image()
    image.set_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON)
    button = gtk.Button()
    button.set_image(image)
    button.connect("clicked", toggle_print_mouse_infos)
    top_hbox.pack_start(button)
    # == Second HBox with some gtk thing on the left and the area for Panda on the right
    bottom_hbox = gtk.HBox()
    vbox.pack_end(bottom_hbox, expand = True)
    # ==
    left_panel = gtk.TreeView()
    left_panel.set_model(gtk.TreeStore(str, object, object))
    column = gtk.TreeViewColumn("Name", gtk.CellRendererText(), text = 0)
    column.set_sort_column_id(0)
    left_panel.append_column(column)
    # ==
    bottom_hbox.pack_start(left_panel, expand = False)
    # ==
    drawing_area = gtk.DrawingArea()
    bottom_hbox.pack_end(drawing_area)
    # ==
    def quit(*args, **kw) :
        window.destroy()
        sys.exit(0)
    # ==
    window.connect("delete-event", quit)
    window.show_all()
    # ==
    gtk_iteration() # Needed to create all the XWindows of the gtk widgets and be able to get the xid/handle
    # ==
    return window, drawing_area

#base = taskMgr = run = render = loader = None # DirectStart is going to replace these
def main() :
    loadPrcFileData("", "window-type none")
    import direct.directbase.DirectStart # this sticks a ton into __builtins__
    size                 = (800, 600)
    window, drawing_area = launch_gtk_window(size)
    launch_panda_window(drawing_area, size)
    base.disableMouse()
    taskMgr.add(gtk_iteration, "gtk")
    run()

if __name__ == '__main__':
    main() 
