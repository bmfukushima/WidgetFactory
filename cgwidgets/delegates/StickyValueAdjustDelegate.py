"""
Function to run?
Get original value...
set value...
"""

import math
import sys
import logging

from qtpy.QtCore import QEvent, Qt, QPoint, QRectF
from qtpy.QtWidgets import (
    QWidget, QApplication, QLabel, QDesktopWidget, QGraphicsItem
)
from qtpy.QtGui import QCursor

from cgwidgets.utils import getMagnitude


class iStickyValueAdjustDelegate(object):
    """
    Registers a click/drag even for the user.  By default this will
    automatically update the widget provided.  However custom functionality
    can be added by using the "setUserUpdateFunction" which will install a function
    to run during each mouse move event.

    By default this is setup to work with sticky drag.  Also there is no other option
    so... get used to it.  You're welcome.

    Attributes:
        pixels_per_tick (int): number of pixels the cursor must travel to register 1 tick
        value_per_tick (float): how much the original value should be modified per
            tick.
        orig_value (str): original value provided by the widget
        _drag_STICKY (bool): if the user is current in a click/drag event
        widget (QWidget): Widget to adjust.

    Notes:
        widget/item provided needs setValue method that will set the text/value
        mousePressEvents on widget...
            in order to do mouse press events on teh widget, you'll need to use the
                mousePressEventOverride()
    """
    input_events = [
        QEvent.MouseButtonPress,
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

    def __init__(self, widget=None):
        #super(iStickyValueAdjustDelegate, self).__init__(parent)
        self._pixels_per_tick = 100
        self._value_per_tick = 0.1
        self._updating = False
        self.widget = widget

    """ PROPERTIES """
    def widget(self):
        return self._widget

    def setWidget(self, widget):
        self._widget = widget

    def valuePerTick(self):
        return self._value_per_tick

    def setValuePerTick(self, _value_per_tick):
        self._value_per_tick = _value_per_tick

    def pixelsPerTick(self):
        return self._pixels_per_tick

    def setPixelsPerTick(self, _pixels_per_tick):
        self._pixels_per_tick = _pixels_per_tick

    def getOrigValue(self):
        """
        Returns the current value as a string.  This should be run when a
        click drag event is started
        """
        try:
            orig_value = self.widget.getInput()
        except AttributeError:
            try:
                orig_value = self.widget.getValue()
            except AttributeError:
                orig_value = self.widget.text()
        return float(orig_value)

    # def origValue(self):
    #     return self._orig_value
    #
    # def setOrigValue(self, orig_value):
    #     self._orig_value = orig_value

    """ VALUE UPDATERS / SETTERS"""
    def __setValue(self, obj):
        """
        This function is run to update the value on the parent widget.
        This will update the value on the widget, and then run
        the userUpdateFunction
        """
        current_pos = QCursor.pos()
        magnitude = getMagnitude(obj._calc_pos, current_pos)
        obj._slider_pos, obj._num_ticks = math.modf(magnitude / self.pixelsPerTick())

        # update values
        self.userUpdateFunction(obj)
        self.updateValue(obj)

    def updateValue(self, obj):
        """
        Sets the current value on the widget/item provided
        to the new value based off of how far the cursor has moved
        """
        new_value = obj._num_ticks * self.valuePerTick()
        new_value += float(obj._orig_value)
        logging.debug(new_value)
        self.widget.setValue(new_value)

    def __userUpdateFunction(self, obj, original_value, slider_pos, num_ticks):
        """
        original_value (float)
        slider_pos (float)
        num_ticks (int)
        """
        pass
        #self.widget.setText(str(num_ticks))

    def userUpdateFunction(self, obj):
        return self.__userUpdateFunction(obj, obj._orig_value, obj._slider_pos, obj._num_ticks)

    def setUserUpdateFunction(self, userUpdateFunction):
        """
        This takes one function which should be run when ever the value
        is changed during a slide event.

        This function will be required to take 3 args
            original_value, slider_pos, num_ticks
        """
        self.__userUpdateFunction = userUpdateFunction

    def penDownEvent(self, obj):
        """
        This should be run every time the user clicks.

        Args:
            obj (QWidget / QItem): Object to install all of the extra attrs on
        """
        obj._calc_pos = QCursor.pos()
        obj._cursor_pos = QCursor.pos()
        obj._drag_STICKY = not obj._drag_STICKY
        obj._num_ticks = 0
        obj._orig_value = self.getOrigValue()

        # toggle cursor display
        if obj._drag_STICKY:
            # TODO blank cursor
            obj.setCursor(Qt.BlankCursor)
        else:
            obj.unsetCursor()

    def stickyEventFilter(self, obj, event, *args, **kwargs):
        """
        _drag_STICKY (bool): Determines if a drag event is currently active
        _calc_pos (QPoint): Position to calculate magnitude from
        _cursor_pos (QPoint): Original cursor click point
        _num_ticks (int): the number of ticks
            value_mult * _num_ticks = value_offset
        """
        # pen down
        if event.type() in iStickyValueAdjustDelegate.input_events:
            self.penDownEvent(obj)

        # pen move
        if event.type() in iStickyValueAdjustDelegate.move_events:
            if obj._drag_STICKY:
                self.__setValue(obj)

        # exit event
        if event.type() in iStickyValueAdjustDelegate.exit_events:
            # force this widget to never loser focus on drag
            if obj._drag_STICKY:
                # update maths
                current_pos = QCursor.pos()
                offset = (current_pos - obj._cursor_pos)
                obj._calc_pos = obj._calc_pos - offset

                # update value
                self.__setValue(obj)

                # reset cursor position back to initial click position
                QCursor.setPos(obj._cursor_pos)

        # cancel event with escape key
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                obj.unsetCursor()
                obj._drag_STICKY = False


class StickyValueAdjustWidgetDelegate(QWidget, iStickyValueAdjustDelegate):
    def __init__(self, parent=None, widget=None):
        super(StickyValueAdjustWidgetDelegate, self).__init__(parent)
        if not widget:
            widget = parent

        iStickyValueAdjustDelegate.__init__(self, widget=widget)

    def eventFilter(self, obj, event, *args, **kwargs):
        # preflight
        if event.type() in self.input_events:
            if self._updating is True:
                return False

        # get widgets
        drag_widget = obj._sticky_widget_data['drag_widget']
        active_widget = obj._sticky_widget_data['active_widget']

        if obj == active_widget:
            # activated by clicking on the activation widget
            if event.type() in iStickyValueAdjustDelegate.input_events:
                self._updating = True
                self.penDownEvent(drag_widget)
                return False

        if obj == drag_widget:
            # stop activation from drag widget
            if event.type() in iStickyValueAdjustDelegate.input_events:
                if drag_widget._drag_STICKY is False:
                    return False

            # run event
            self.stickyEventFilter(drag_widget, event, *args, **kwargs)

        if event.type() == QEvent.MouseButtonRelease:
            self._updating = False

        return False


class StickyValueAdjustItemDelegate(QGraphicsItem, iStickyValueAdjustDelegate):
    def __init__(self, parent=None, widget=None):
        super(StickyValueAdjustItemDelegate, self).__init__(parent)
        if not widget:
            widget = parent

        iStickyValueAdjustDelegate.__init__(self, widget=widget)

    def boundingRect(self):
        return QRectF(0, 0, 0, 0)

    def paint(self, *args, **kwargs):
        return None

    def sceneEventFilter(self, obj, event, *args, **kwargs):
        """
        TODO clean this up and pass back to main event filter?
            Where am I storing meta data?
        """
        # get event filter args
        item = obj
        obj = obj.scene().views()[0]
        if event.type() in self.input_events:
            if obj._drag_STICKY is False:
                obj._drag_STICKY_updating = True
                self.penDownEvent(obj)
                obj._current_item = item

        return False


class StickyValueAdjustViewDelegate(QWidget, iStickyValueAdjustDelegate):
    def __init__(self, parent=None, widget=None):
        super(StickyValueAdjustViewDelegate, self).__init__(parent)
        if not widget:
            widget = parent
        iStickyValueAdjustDelegate.__init__(self, widget=widget)
        self.setMouseTracking(True)

    def eventFilter(self, obj, event, *args, **kwargs):
        # preflight
        if not hasattr(obj, "_current_item"): return False

        # pen down
        if event.type() == QEvent.MouseButtonPress:
            # Preflight
            if obj._drag_STICKY_updating is True:
                obj._drag_STICKY_updating = False
                return False

            # deactivate
            if obj._drag_STICKY is True:
                obj._drag_STICKY = False
                QCursor.setPos(obj._cursor_pos)
                obj.unsetCursor()
                delattr(obj, '_current_item')
                return False

        # run event filter
        self.stickyEventFilter(obj, event, *args, **kwargs)

        return QWidget.eventFilter(self, obj, event, *args, **kwargs)

    """ OVERLOADED FUNCTIONS"""
    def getOrigValue(self):
        """
        Returns the current value as a string.  This should be run when a
        click drag event is started
        """
        try:
            orig_value = self.widget._current_item.getInput()
        except AttributeError:
            try:
                orig_value = self.widget._current_item.getValue()
            except AttributeError:
                try:
                    orig_value = self.widget._current_item.text()
                except AttributeError:
                    logging.WARNING("cannot find a default value, returning 1.0")
                    orig_value = 1.0
        return float(orig_value)

    def updateValue(self, obj):
        """
        Sets the current value on the widget/item provided
        to the new value based off of how far the cursor has moved

        Note:
            This overloads the default behavior from the interface
        """
        new_value = obj._num_ticks * self.valuePerTick()
        new_value += float(obj._orig_value)
        logging.debug(new_value)
        self.widget._current_item.setValue(new_value)


""" TESTING """
from qtpy.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsLineItem,
QGraphicsEllipseItem
)
from qtpy.QtGui import QColor, QBrush


class TestWidget(QLabel):
    def __init__(self, parent=None):
        super(TestWidget, self).__init__(parent)
        self.setText('0')
    def setValue(self, value):
        self.setText(str(value))


class TestWidgetItem(QGraphicsView):
    def __init__(self, parent=None):
        super(TestWidgetItem, self).__init__(parent)
        scene = QGraphicsScene()
        self.setScene(scene)

        self.line_item = QGraphicsLineItem()
        self.line_item.setLine(0, 0, 10, 10)

        self.circle_item = CenterManipulatorItem()
        self.circle_item.setRect(10, 10, 50, 50)

        self.scene().addItem(self.circle_item)
        self.scene().addItem(self.line_item)

        self.scene().setSceneRect(0,0,100,100)


        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        event.ignore()
        QGraphicsView.mouseMoveEvent(self, event)


class CenterManipulatorItem(QGraphicsEllipseItem):
    def __init__(self, parent=None):
        super(CenterManipulatorItem, self).__init__(parent)
        # pen = self.pen()
        # pen.setStyle(Qt.NoPen)
        # pen.setWidth(0)
        # self.setPen(pen)
        self.value = 1

    def setColor(self, color=QColor(255, 0, 0)):
        self.setBrush(QBrush(color))

    def setValue(self, value):
        self.value = value

    def getValue(self):
        return self.value


class LineItem(QGraphicsLineItem):
    def __init__(self, parent=None):
        super(CenterManipulatorItem, self).__init__(parent)
        self.setLine(0,0, 25,25)
        self.value = 1

    def setColor(self, color=QColor(255, 0, 0)):
        self.setBrush(QBrush(color))

    def setValue(self, value):
        self.value = value

    def getValue(self):
        return self.value


if __name__ == '__main__':
    from qtpy.QtWidgets import QVBoxLayout
    from cgwidgets.utils import installInvisibleWidgetEvent
    from cgwidgets.utils import installStickyValueAdjustItemDelegate, installStickyValueAdjustWidgetDelegate
    app = QApplication(sys.argv)

    logging.basicConfig(level=logging.DEBUG)

    # w = TestWidgetItem()
    # ef = installStickyValueAdjustItemDelegate(w.circle_item)

    def testUpdate(obj, original_value, slider_pos, num_ticks):
        print('obj == %s'%obj)
        print('original_value == %s'%original_value)
        print('slider pos == %s'%slider_pos)
        print('num_ticks == %s'%num_ticks)

    w = QWidget()
    l = QVBoxLayout(w)
    w2 = TestWidget()
    l.addWidget(w2)
    l.addWidget(QLabel("test"))

    installInvisibleWidgetEvent(w2)
    ef = installStickyValueAdjustWidgetDelegate(w2, drag_widget=w)

    #ef.setUserUpdateFunction(testUpdate)

    # ef.setValuePerTick(.001)
    # ef.setPixelsPerTick(50)

    w.show()
    w.move(QCursor.pos())
    w.resize(100, 100)

    sys.exit(app.exec_())
