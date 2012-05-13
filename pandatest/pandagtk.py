
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
#    render.setLight(slnp)
    

def resize_panda_window(widget, request) :
    """ Connected to resize event of the widget Panda is draw on so that the Panda window update its size """
    props = WindowProperties().getDefault()
    props = WindowProperties(base.win.getProperties())
    props.setOrigin(0, 0)
    props.setSize(request.width, request.height)
    props.setParentWindow(get_widget_id(widget))
    base.win.requestProperties(props)

def setup_panda_events(window) :
    """ Setup mouse events in Panda """
    obj = DirectObject()
    obj.accept("mouse1"    , print_info, ["Left press"])
    obj.accept("mouse1-up" , print_info, ["Left release"])
    obj.accept("mouse2"    , print_info, ["Wheel press"])
    obj.accept("mouse2-up" , print_info, ["Wheel release"])
    obj.accept("mouse3"    , print_info, ["Right press"])
    obj.accept("mouse3-up" , print_info, ["Right release"])
    obj.accept("wheel_up"  , print_info, ["Scrolling up"])
    obj.accept("wheel_down", print_info, ["Scrolling down"])
    return obj

# == GTK SETUP == #

def get_widget_id(widget) :
    """ Retrieve gtk widget ID to tell the Panda window to draw on it """
    if platform.system() == "Windows" : return widget.window.handle
    else                              : return widget.window.xid

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

def add_gtk_shortcuts(window, actions) :
    # Create the accel group and add it to the window
    accel_group = gtk.AccelGroup()
    window.add_accel_group(accel_group)
    # Create the action group
    action_group = gtk.ActionGroup('ActionGroup')
    # ==
    # Could give the list of action to add_toggle_actions method all at once and then connect each one
    for action in actions :
        action_group.add_toggle_actions([action])
        gtk_action = action_group.get_action(action[0])
        gtk_action.set_accel_group(accel_group)
        gtk_action.connect_accelerator()
    # ==
    return accel_group, action_group

# == INFO == #

mouse_info = False
def toggle_print_mouse_infos(*args, **kw) :
    global mouse_info
    mouse_info = not mouse_info
    print "\n\n Printing Mouse Infos : %s \n\n" % mouse_info

def mouse_info_task(*args, **kw) :
    global mouse_info
    if mouse_info :
        md = base.win.getPointer(0)
        print "Mouse in window: ", md.getInWindow()
        print "Mouse position : ", md.getX(), md.getY()
    # ==
    return Task.cont

def print_info(message) :
    print message

# == MAIN == #

def main() :
    setup()
    # ==
    import direct.directbase.DirectStart
    # ==
    size                 = (800, 600)
    window, drawing_area = launch_gtk_window(size)
    launch_panda_window(drawing_area, size)
    base.disableMouse()
    # ==
    # Here we create the shortcuts/actions.
    # For more details, see http://www.pygtk.org/pygtk2reference/class-gtkactiongroup.html#method-gtkactiongroup--add-toggle-actions
    #
    # action = (name, stock_id, label, accelerator(=key), tooltip, callback, active_flag (optional)
    shortcuts = [
                 ("move" , None, "move" , "m", "move" , lambda _ : move_pointer(window, drawing_area, (size[0] / 2.0, size[1] / 2.0))),
                 ("print", None, "print", "p", "print", lambda _ : print_info("GTK print shortcut")),
                ]
    accel_group, action_group = add_gtk_shortcuts(window, shortcuts)
    # ==
    direct_object = setup_panda_events(window)
    taskMgr.add(mouse_info_task, "print info")
    # ==
    taskMgr.add(gtk_iteration, "gtk")
    # ==
    run()

if __name__ == '__main__':
    main() 
