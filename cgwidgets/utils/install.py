from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *

from .position import Magnitude


""" COMPLETER POPUP """
def installCompleterPopup(completer):
    """
    Adds the custom style completer popup (QListView) to the
    completer provided

    Args:
        completer (QCompleter): Completer to have the custom styled
            popup installed on
    Returns (QListView): of the pop
    """
    from cgwidgets.views import CompleterPopup
    popup = CompleterPopup()
    completer.setPopup(popup)
    delegate = QStyledItemDelegate()
    completer.popup().setItemDelegate(delegate)
    return popup


""" INVISIBLE CURSOR"""
def installInvisibleCursorEvent(widget):
    """
    Installs an event filter on the widget that makes it so that when the
    user click/drags, it will turn the cursor invisible, and all the cursor
    to move an infinite distance.  On release, it will return the cursor
    back to the starting position

    Args:
        widget (QWidget): Widget to install the invisible drag event on

    Returns:
        (InvisibleCursorEvent): QWidget which holds the event
            filter for the invisible drag event
    """
    from cgwidgets.events import InvisibleCursorEvent
    invis_drag_filter = InvisibleCursorEvent(parent=widget)
    widget.installEventFilter(invis_drag_filter)

    return invis_drag_filter


""" INVISIBLE WIDGET"""
def installInvisibleWidgetEvent(hide_widget, activation_widget=None):
    """
    Installs an event filter on the widget that makes it so that when the
    user click/drags, it will turn the cursor invisible, and all the cursor
    to move an infinite distance.  On release, it will return the cursor
    back to the starting position

    Args:
        activation_widget (QWidget): Widget when clicked to hide the hide_widget.
            If none is provided, the parent widget will be used
        hide_widget (QWidget): widget to be hidden, if none is provided,
            the parent widget will be used
    Returns:
    """
    from cgwidgets.events import InvisibleWidgetEvent

    # set up default widgets
    parent = hide_widget.parent()
    if not parent:
        parent = hide_widget

    if activation_widget is None:
        activation_widget = hide_widget

    invisible_widget_data = {
        'parent' : parent,
        'hide_widget' : hide_widget,
        'activation_widget' : activation_widget}

    # create filter
    invisible_widget_filter = InvisibleWidgetEvent(
        parent=parent
    )

    # setup attrs / install event filter
    hide_widget._hide_widget_filter_INVISIBLE = False
    for key in invisible_widget_data:
        widget = invisible_widget_data[key]
        widget._invisible_widget_data = invisible_widget_data

        # install event filter
        widget.installEventFilter(invisible_widget_filter)

    return invisible_widget_filter


""" RESIZE TIMER """
def installResizeEventFinishedEvent(widget, time_delay, resize_finished_event, timer_name, *args, **kwargs):
    """
    Runs a function after a certain amount of time since the last resize

    Args:
        widget (QWidget): to install timer on
        time_delay (int): number of milliseconds to wait before running the resize_finished_event
        resize_finished_event (function): to be run after the time delay has finished
            note:
                *args, **kwargs any additional args/kwargs provided to installResizeFinishedEvent
                are sent directly to this function
        timer_name (string): name of timer, store as an attr on the object provided

    Note:
        This should be called INSIDE of the resizeEvent of the widget provided.  I would override it in here...
        but resizeEvent is a virtual protected method (I know what that means because I'm smrtaf, and not a stoopid).

    """
    def cleanupResizeFinishedEvent():
        delattr(widget, timer_name)
        resize_finished_event(*args, **kwargs)

    def runTimer():
        # stop existing timer
        if hasattr(widget, timer_name):
            timer = getattr(widget, timer_name)
            timer.stop()

        # create new timer
        new_timer = QTimer()
        new_timer.timeout.connect(cleanupResizeFinishedEvent)
        new_timer.start(time_delay)

        # store timer on widget
        setattr(widget, timer_name, new_timer)

    runTimer()


""" SLIDE"""
def installSlideDelegate(
        widget,
        sliderPosMethod,
        breed=None,
        display_widget=None
    ):
    """
    Args:
        widget (QWidget): the PyQt widget to install this delegate on to.
        getSliderPos (method): returns the position of the slider
            as a percentage (0-1)
            Returns:
                (float): 0-1
    Kwargs:
        breed (cgwidgets.delegate.SliderDelegate.breed): what type
            of slide display to show to the user.  Appropriate values are
            Unit, Hue, Sat, Val
    Returns:
        SlideDelegate
    """
    from cgwidgets.delegates import SlideDelegate
    # set up default slide display type
    if breed is None:
        breed = 0

    slide_delegate = SlideDelegate(
        parent=widget,
        getSliderPos=sliderPosMethod,
        breed=breed,
        display_widget=display_widget
    )
    widget._dragging = False
    widget._slider_pos = 0.0
    widget.installEventFilter(slide_delegate)
    return slide_delegate


def removeSlideDelegate(item, slide_delegate):
    item.removeEventFilter(slide_delegate)


""" LADDER"""
def installLadderDelegate(
    widget,
    user_input=QEvent.MouseButtonRelease,
    value_list=None,
    range_min=None,
    range_max=None,
    allow_negative_values=True,
    allow_zero_value=True
):
    """
    Args:
        widget: <QLineEdit> or <QLabel>
            widget to install ladder delegate onto.  Note this currently
            works for QLineEdit and QLabel.  Other widgets will need
            to implement a 'setValue(value)' method on which sets the
            widgets value.
    Kwargs:
        user_input: <QEvent>
            user event that triggers the popup of the Ladder Delegate
        value_list: <list> of <float>
            list of values for the user to be able to adjust by, usually this
            is set to .01, .1, 1, 10, etc
        display_widget (QWidget): optional argument.  If entered, the display
            will show up over that widget rather than over the main display.
    Returns:
        LadderDelegate
    """
    if value_list is None:
        value_list = [0.001, 0.01, 0.1, 1, 10, 100, 1000]
    from cgwidgets.delegates import LadderDelegate

    ladder = LadderDelegate(
        parent=widget,
        value_list=value_list,
        user_input=user_input,
        range_min=range_min,
        range_max=range_max,
        allow_negative_values=allow_negative_values,
        allow_zero_value=allow_zero_value,
    )
    widget.installEventFilter(ladder)
    return ladder


""" STICKY VALUE DRAG"""
def getObjectType(active_object):
    object_type = 'widget'
    for c in type(active_object).__mro__:
        if c == QGraphicsItem:
            object_type = 'item'

    return object_type

def installStickyAdjustDelegate(
        active_object,
        activation_event=None,
        activation_object=None,
        deactivation_event=None,
        input_buttons=[Qt.LeftButton],
        input_modifier=Qt.NoModifier,
        pixels_per_tick=200,
        value_per_tick=0.01,
        value_update_event=None,
        range_min=None,
        range_max=None
    ):
    """
    Args:
        active_object (QWidget | QGraphicsItem): widget to set the value on.
        activation_event (function): run every time the activation object is clicked
            active_object, drag_widget, event
        activation_object (QWidget | QGraphicsItem): widget when clicked on will start this delegate
        deactivation_event (function): run when the sticky adjust is deactivated
            active_object, activation_widget, event
        input_buttons (list): of mouse button / key presses that should be used to initialize the sticky drag
            Qt.KEY | Qt.CLICK
        input_modifier (Qt.Modifiers): determines what modifiers should be used
        magnitude_type (Magnitude.TYPE): determines what value should be used as the offset.
            x | y | m
        pixels_per_tick (int):
        value_per_tick (float):
        value_update_event (function): runs every time the sticky value sends a
            obj, original_value, slider_pos, num_ticks
    todo:
        widget --> object
            this file...
            sticky value delegate files
    """

    from cgwidgets.delegates import (
        StickyValueAdjustWidgetDelegate,
        StickyValueAdjustItemDelegate,
        StickyDragWindowWidget
    )

    from cgwidgets.utils import setAsTool

    # get object type
    object_type = getObjectType(active_object)

    # SET UP // Drag Widget
    # get the drag widget
    if object_type == 'widget':
        main_application_widget = active_object.window()
    elif object_type == 'item':
        main_application_widget = active_object.scene().views()[0].window()

    # create invisible drag window
    if not hasattr(main_application_widget, '_sticky_drag_window_widget'):
        main_application_widget._sticky_drag_window_widget = StickyDragWindowWidget(main_application_widget)

    drag_widget = main_application_widget._sticky_drag_window_widget
    # drag_widget._magnitude_type = magnitude_type

    drag_widget.setRange(range_min, range_max)
    # check activation widget
    if not activation_object:
        activation_object = active_object

    # SET UP // Activation Widget
    # create filter
    if object_type == 'widget':
        sticky_widget_filter = StickyValueAdjustWidgetDelegate(active_object)
    elif object_type == 'item':
        sticky_widget_filter = StickyValueAdjustItemDelegate(active_object)

    active_object._sticky_widget_filter = sticky_widget_filter

    sticky_widget_filter.setPixelsPerTick(pixels_per_tick)
    sticky_widget_filter.setValuePerTick(value_per_tick)

    sticky_widget_filter.modifiers = input_modifier
    sticky_widget_filter.input_buttons = input_buttons

    # set attrs
    sticky_widget_data = {
        'drag_widget': drag_widget,
        'active_object': active_object,
        'activation_object': activation_object
    }
    activation_object._sticky_widget_data = sticky_widget_data

    # install filter
    if object_type == 'widget':
        activation_object.installEventFilter(sticky_widget_filter)
    elif object_type == 'item':
        activation_object.installSceneEventFilter(sticky_widget_filter)

    # install custom events
    if activation_event:
        sticky_widget_filter.setActivationEvent(activation_event)
    if deactivation_event:
        sticky_widget_filter.setDeactivationEvent(deactivation_event)
    if value_update_event:
        sticky_widget_filter.setValueUpdateEvent(value_update_event)

    # return
    drag_widget.hide()
    return sticky_widget_filter


def removeStickyAdjustDelegate(active_object):
    object_type = getObjectType(active_object)

    # SET UP // Drag Widget
    # get the drag widget
    if object_type == 'widget':
        active_object.removeEventFilter(active_object._sticky_widget_filter)
    elif object_type == 'item':
        active_object.removeSceneEventFilter(active_object._sticky_widget_filter)

    active_object._sticky_widget_filter.setParent(None)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    w = QLabel('1.0')
    installStickyAdjustDelegate(w)
    w.show()
    w.move(QCursor.pos())
    w.resize(100, 100)

    sys.exit(app.exec_())