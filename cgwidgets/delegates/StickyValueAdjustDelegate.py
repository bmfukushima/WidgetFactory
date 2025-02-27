"""
Hierarchy
    iStickyValueAdjustDelegate, iStickyActivationDelegate
        |- StickyValueAdjustWidgetDelegate --> QWidget
        |- StickyValueAdjustItemDelegate --> QGraphicsItem
    iStickyValueAdjustDelegate
        |- StickyDragWindowWidget


"""
import decimal
import logging
import math

from qtpy.QtCore import QEvent, Qt, QPoint, QRectF
from qtpy.QtWidgets import (QApplication, QGraphicsItem, QWidget)
from qtpy.QtGui import QCursor

from cgwidgets.utils import (getMagnitude, Magnitude, setAsTransparent, setAsTool, getGlobalPos, setAsAlwaysOnTop)

class iStickyValueAdjustDelegate(object):
    """
    The interface for all of the sticky drag delegates, by default they will
    registers a click/drag event for the user and will
    automatically update the widget provided.  However custom functionality
    can be added by using the "setValueUpdateEvent" which will install a function
    to run during each mouse move event.

    Attributes:
        pixels_per_tick (int): number of pixels the cursor must travel to register 1 tick
        value_per_tick (float): how much the original value should be modified per
            tick.
        orig_value (str): original value provided by the widget
        _drag_STICKY (bool): if the user is current in a click/drag event
        widget (QWidget): Widget to adjust.

    Virtual Functions:
        activationEvent ( active_object, drag_widget, event ): will run every time
            the activation object is clicked on
        setValueUpdateEvent (function): which takes
            obj, original_value, slider_pos, num_ticks
    Notes:
        - widget/item provided needs setValue method that will set the text/value
        - if you want the live update to work on InputWidgets, you'll need to toggle the
            _updating attr on the input widget.
        - Interface for the activation objects

    """
    input_events = [
        QEvent.MouseButtonPress,
        QEvent.KeyPress,
        QEvent.KeyRelease,
        QEvent.GraphicsSceneMousePress
    ]

    move_events = [
        QEvent.MouseMove,
        QEvent.GraphicsSceneMouseMove
    ]

    exit_events = [
        QEvent.Leave,
        QEvent.GraphicsSceneHoverLeave,
        QEvent.DragLeave
    ]

    def __init__(self):
        self._pixels_per_tick = 200
        self._value_per_tick = 0.1
        self._updating = False

    """ PROPERTIES """
    def valuePerTick(self):
        return self._value_per_tick

    def setValuePerTick(self, _value_per_tick):
        self._value_per_tick = _value_per_tick

    def pixelsPerTick(self):
        return self._pixels_per_tick

    def setPixelsPerTick(self, _pixels_per_tick):
        self._pixels_per_tick = _pixels_per_tick

    """ VIRTUAL EVENTS """
    def __valueUpdateEvent(self, obj, original_value, slider_pos, num_ticks, magnitude):
        """
        obj (QWidget): the widget that should have its values manipulated
        original_value (float)
        slider_pos (float)
        num_ticks (int)
        magnitude (Utils.Magnitude)
        """
        pass

    def setValueUpdateEvent(self, valueUpdateEvent):
        """
        This takes one function which should be run when ever the value
        is changed during a slide event.

        This function will be required to take 3 args
            original_value, slider_pos, num_ticks
        """
        self.__valueUpdateEvent = valueUpdateEvent

    def __activationEvent(self, active_object, drag_widget, event):
        """
        obj (QWidget): the widget that should have its values manipulated
        original_value (float)
        slider_pos (float)
        num_ticks (int)
        """
        pass

    def activationEvent(self, active_object, drag_widget, event):
        return self.__activationEvent(active_object, drag_widget, event)

    def setActivationEvent(self, activationEvent):
        """
        This takes one function which should be run when ever the value
        is changed during a slide event.

        This function will be required to take 3 args
            original_value, slider_pos, num_ticks
        """
        self.__activationEvent = activationEvent

    """ VIRTUAL EVENTS >> DRAG WIDGET """
    def __deactivationEvent(self, active_object, activation_widget, event):
        """
        obj (QWidget): the widget that should have its values manipulated
        original_value (float)
        slider_pos (float)
        num_ticks (int)
        """
        pass

    def setDeactivationEvent(self, deactivationEvent):
        """
        This takes one function which should be run when ever the value
        is changed during a slide event.

        This function will be required to take 3 args
            original_value, slider_pos, num_ticks
        """
        self.__deactivationEvent = deactivationEvent

    """ EVENTS """
    def penDownEvent(self, activation_obj, event):
        """
        Event to be run when the user clicks on the activation widget.
        This will enable the activation of the sticky drag.

        Args:
            obj (QWidget): Activation Widget
        """
        # get widgets
        drag_widget = activation_obj._sticky_widget_data['drag_widget']
        active_object = activation_obj._sticky_widget_data['active_object']

        # setup drag attrs
        drag_widget.setActiveObject(active_object)
        drag_widget.setActivationObject(activation_obj)

        # activate sticky drag
        self.__activateStickyDrag(drag_widget)

        # show invisible widget ( yeah I know how it sounds )
        drag_widget.setParent(None)
        # setAsTool(drag_widget)

        setAsAlwaysOnTop(drag_widget)
        drag_widget.show()
        QApplication.processEvents()
        drag_widget.raise_()
        drag_widget.activateWindow()
        drag_widget.setFocus()

        # user activation event
        # todo set deactivation function on drag widget
        drag_widget.setValueUpdateEvent(self.__valueUpdateEvent)
        drag_widget.setDeactivationEvent(self.__deactivationEvent)
        self.activationEvent(active_object, drag_widget, event)

    def __activateStickyDrag(self, obj):
        """
        This should be run every time the user clicks.

        Args:
            obj (QWidget / QItem --> DragWidget): Object to install all of the extra attrs on
        """
        obj._cursor_pos = QCursor.pos()

        # set up drag time attrs
        obj.updateOrigValue()
        obj._calc_pos = QCursor.pos()
        obj._drag_STICKY = not obj._drag_STICKY
        obj._num_ticks = 0
        obj._previous_num_ticks = 0
        obj._pixels_per_tick = self.pixelsPerTick()
        obj._value_per_tick = self.valuePerTick()

        # toggle cursor display
        if obj._drag_STICKY:
            obj.setCursor(Qt.BlankCursor)


class StickyValueAdjustWidgetDelegate(QWidget, iStickyValueAdjustDelegate):
    def __init__(self, parent=None):
        super(StickyValueAdjustWidgetDelegate, self).__init__(parent)
        iStickyValueAdjustDelegate.__init__(self)

    def eventFilter(self, activation_obj, event, *args, **kwargs):
        # todo key press events
        modifiers = QApplication.keyboardModifiers()
        if modifiers == self.modifiers:
            if event.type() in self.input_events:
                if event.type() == QEvent.MouseButtonPress:
                    if event.button() in self.input_buttons:
                        self.penDownEvent(activation_obj, event)
                        return False
                # if event.type() == QEvent.KeyPress:
                #     if event.key() == self.input_buttons:
                #         self.penDownEvent(activation_obj, event)
        return False

        # # activate
        # if event.type() in iStickyValueAdjustDelegate.input_events:
        #     self.penDownEvent(activation_obj, event)
        #     return False
        #
        # return False


class StickyValueAdjustItemDelegate(QGraphicsItem, iStickyValueAdjustDelegate):
    def __init__(self, parent=None):
        super(StickyValueAdjustItemDelegate, self).__init__(parent)
        iStickyValueAdjustDelegate.__init__(self)

    def boundingRect(self):
        return QRectF(0, 0, 0, 0)

    def paint(self, *args, **kwargs):
        return None

    def sceneEventFilter(self, activation_obj, event, *args, **kwargs):
        # todo key press events
        # get widgets
        modifiers = QApplication.keyboardModifiers()
        if modifiers == self.modifiers:
            if event.type() in self.input_events:
                if event.type() == QEvent.GraphicsSceneMousePress:
                    if event.button() in self.input_buttons:
                        self.penDownEvent(activation_obj, event)
                        return False
                # if event.type() == QEvent.KeyPress:
                #     if event.key() == self.input_buttons:
                #         self.penDownEvent(activation_obj, event)
                return False
        return False

        # if event.type() in iStickyValueAdjustDelegate.input_events:
        #     self.penDownEvent(activation_obj, event)
        #     return False
        #
        # return False


class StickyDragWindowWidget(QWidget, iStickyValueAdjustDelegate):
    """
    Main window that is shown when the user enters a sticky drag event...
    This will be invisible to the user.
    """
    def __init__(self, parent=None):
        super(StickyDragWindowWidget, self).__init__(parent)
        # setup default attrs
        self._orig_value = 0
        self._updating = False
        self._drag_STICKY = False
        self.setMouseTracking(True)

        # range attrs
        self._range_min = 0.0
        self._range_max = 1.0
        self._direction = 0
        self._is_passed_range = False

        # setup display attrs
        self.hide()
        setAsTool(self)
        setAsTransparent(self)
        # self.setWindowOpacity(0.5)
        self.setValueUpdateEvent(self.valueUpdateEvent)

    """ PROPERTIES """
    def activeObject(self):
        return self._active_object

    def setActiveObject(self, _active_object):
        self._active_object = _active_object

    def activationObject(self):
        return self._activation_object

    def setActivationObject(self, _activation_object):
        self._activation_object = _activation_object

    def origValue(self):
        return self._orig_value

    def updateOrigValue(self):
        """
        Returns the current value as a string.  This should be run when a
        click drag event is started
        """
        try:
            orig_value = self.activeObject().getInput()
        except AttributeError:
            try:
                orig_value = self.activeObject().getValue()
            except AttributeError:
                orig_value = self.activeObject().text()

        self._orig_value = decimal.Decimal(str(orig_value))

    """ UTILS """
    def __deactivateStickyDrag(self):
        self._drag_STICKY = False
        self.unsetCursor()
        self.hide()

        # gets overwritten because of the leave event...
        self.__placeCursorAtActiveItem()

        self.releaseMouse()

    def __placeCursorAtActiveItem(self):
        """
        Gets the current active items position in world space
        and places the cursor in the center of that.
        """
        try:
            object_pos = getGlobalPos(self.activeObject())
            cursor_display_pos = QPoint(
                object_pos.x() + (self.activeObject().width() * 0.5),
                object_pos.y() + (self.activeObject().height() * 0.5)
            )

        except AttributeError:
            view = self.activeObject().scene().views()[0]
            view_pos = view.mapFromScene(self.activeObject().scenePos())
            cursor_display_pos = view.viewport().mapToGlobal(view_pos)

        QCursor.setPos(cursor_display_pos)

    """ RANGE """
    def setRange(self, range_min=None, range_max=None):
        """
        Determines if this widget has a specified range.  Going over this
        range will clip values into that range
        """
        self._range_min = range_min
        self._range_max = range_max

    def direction(self):
        return self._direction

    def setDirection(self, direction):
        self._direction = direction

    def updateDirection(self):
        """ Updates the direction.

        Returns (bool): True if the direction has changed, False if otherwise"""

        direction = None
        if self._previous_num_ticks < self._num_ticks:
            direction = Magnitude.POSITIVE
        elif self._num_ticks < self._previous_num_ticks:
            direction = Magnitude.NEGATIVE

        direction_changed = False
        if direction:
            if direction != self.direction():
                direction_changed = True
                self.setDirection(direction)

        return direction_changed

    """ VALUE UPDATERS / SETTERS"""
    def updateMousePosAttrs(self):
        """ Will update the attributes associated with a mouse move
        slider_pos, num_ticks, previous_num_ticks

        """
        _magnitude = getMagnitude(self._calc_pos, QCursor.pos())
        self._magnitude = _magnitude.xoffset() + _magnitude.yoffset()
        self._previous_num_ticks = self._num_ticks
        self._slider_pos, self._num_ticks = math.modf(self._magnitude / self.pixelsPerTick())

    def __setValue(self):
        """
        This function is run to update the value on the parent widget.
        This will update the value on the widget, and then run
        the valueUpdateEvent
        """

        self.updateMousePosAttrs()

        if self._previous_num_ticks != self._num_ticks:
            # if self._num_ticks != self._previous_num_ticks:
            direction_changed = self.updateDirection()

            # update values
            self.valueUpdateEvent()
            self.__updateValue(direction_changed=direction_changed)

        return

    def __updateValue(self, direction_changed=False):
        """
        Sets the current value on the widget/item provided
        to the new value based off of how far the cursor has moved
        """

        offset_value = decimal.Decimal(str(self._num_ticks)) * decimal.Decimal(str(self.valuePerTick()))
        new_value = self._orig_value + offset_value

        logging.debug(str(new_value))
        self.activeObject().setValue(new_value)

        # enable range
        """ 
            goes under/over range, set position.
            When hits a tick in the opposite direction
            restores that position
            
            Issue when starting/stopping on the end of a range
            Seems that the direction changed or range passed is being set
        """
        if self._is_passed_range:
            # get the current direction of the cursor
            if direction_changed:
                # restore attributes when cursor starts moving the other direction

                self._calc_pos = self._passed_range_calc_pos
                self._previous_num_ticks = self._num_ticks
                if self.direction() == Magnitude.POSITIVE:
                    QCursor.setPos(self._passed_range_pos.x() + 10, self._passed_range_pos.y() + 10)
                if self.direction() == Magnitude.NEGATIVE:
                    QCursor.setPos(self._passed_range_pos.x() - 10, self._passed_range_pos.y() - 10)

                # update num ticks
                self.updateMousePosAttrs()
                self._previous_num_ticks = self._num_ticks
                self._is_passed_range = False

        elif not self._is_passed_range:
            # value passes range
            if self._range_min or self._range_max:
                if self._range_min:
                    if new_value < self._range_min:
                        self._is_passed_range = True
                        self._passed_range_pos = QCursor.pos()
                        self._passed_range_calc_pos = self._calc_pos
                if self._range_max:
                    if self._range_max < new_value:
                        self._is_passed_range = True
                        self._passed_range_pos = QCursor.pos()
                        self._passed_range_calc_pos = self._calc_pos

    """ VIRTUAL FUNCTIONS"""
    def __valueUpdateEvent(self, obj, original_value, slider_pos, num_ticks, magnitude):
        # todo why does this not inherit from iStickyValueAdjustDelegate
        pass

    def valueUpdateEvent(self):
        obj = self.activeObject()
        return self.__valueUpdateEvent(obj, self._orig_value, self._slider_pos, self._num_ticks, self._magnitude)

    def setValueUpdateEvent(self, valueUpdateEvent):
        """
        This takes one function which should be run when ever the value
        is changed during a slide event.

        This function will be required to take 3 args
            original_value, slider_pos, num_ticks
        """
        self.__valueUpdateEvent = valueUpdateEvent

    def __deactivationEvent(self, active_object, activation_widget, event):
        """
        obj (QWidget): the widget that should have its values manipulated
        original_value (float)
        slider_pos (float)
        num_ticks (int)
        """
        pass

    def deactivationEvent(self, active_object, activation_widget, event):
        return self.__deactivationEvent(active_object, activation_widget, event)

    def setDeactivationEvent(self, deactivationEvent):
        """
        This takes one function which should be run when ever the value
        is changed during a slide event.

        This function will be required to take 3 args
            original_value, slider_pos, num_ticks
        """
        self.__deactivationEvent = deactivationEvent

    """ EVENTS """
    def leaveEvent(self, event, *args, **kwargs):
        """
        When the cursor leaves the invisible display area,
        this will return it back to the original point that it
        was set at.  It will then update the positions to accomdate this
        so that one drag seems seemless.
        """
        if not self._drag_STICKY: return

        current_pos = QCursor.pos()
        offset = (current_pos - self._cursor_pos)
        _old_calc_pos = self._calc_pos
        self._calc_pos = self._calc_pos - offset

        # reset cursor
        QCursor.setPos(self._cursor_pos)

        # update value
        self.__setValue()
        return QWidget.leaveEvent(self, event, *args, **kwargs)

    def mouseMoveEvent(self, event, *args, **kwargs):
        self.__setValue()
        QWidget.mouseMoveEvent(self, event, *args, **kwargs)

    def mouseReleaseEvent(self, event):
        if self._is_initializing:
            self._is_initializing = False
        else:
            self.__deactivateStickyDrag()
            self.deactivationEvent(self.activeObject(), self.activationObject(), event)

    def showEvent(self, event):
        offset = 5
        screen_resolution = QApplication.desktop().screenGeometry()
        width, height = screen_resolution.width() - (offset*2), screen_resolution.height() - (offset*2)
        self.setFixedSize(width, height)
        self.move(offset, offset)

        # reset attrs
        self._is_passed_range = False

        self.grabMouse()
        self._is_initializing = True
        return QWidget.showEvent(self, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.__deactivateStickyDrag()
            self.deactivationEvent(self.activeObject(), self.activationObject(), event)


