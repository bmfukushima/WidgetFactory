"""
# -------------------------------------------------------------------------- Bugs
    * First tick does not register

    * Houdini
        Traceback (most recent call last):
          File "/media/ssd01/Scripts/WidgetFactory/cgwidgets/delegates/SlideDelegate/SlideDelegate.py", line 540, in eventFilter
            self.getAlignment(), widget=self._display_widget
          File "/media/ssd01/Scripts/WidgetFactory/cgwidgets/delegates/SlideDelegate/SlideDelegate.py", line 172, in setWidgetPosition
            self.alignToWidget(alignment, widget)
          File "/media/ssd01/Scripts/WidgetFactory/cgwidgets/delegates/SlideDelegate/SlideDelegate.py", line 224, in alignToWidget
            screen_pos = getGlobalPos(widget)
          File "/media/ssd01/Scripts/WidgetFactory/cgwidgets/utils.py", line 231, in getGlobalPos
            title_bar_height = top_level_widget.style().pixelMetric(QStyle.PM_TitleBarHeight)
        RuntimeError: Internal C++ object (PySide2.QtWidgets.QStyle) already deleted.

# ----------------------------------------------------------------------- Feature Enhancement
    *** need to figure out how to make eventFilter more robust...
        ie support CTRL+ALT+CLICK / RMB, etc
            rather than just a QEvent.Type
    *** Detect if close to edge...
        - Detect center point function
        - only needs to handle y pos

    * Horizontal Delegate?
        installStickyAdjustDelegate, will need to set the magnitude?

"""
"""
Ladder Item has the StickyDrag delegate installed on it
The values are updated by...
    LadderItem.setValue()
    LadderDelegate.setValue()
        -> LadderFloatMiddleItem.setValue()
        -> inputWidget.setText() or inputWidget.setValue()
"""
import math
from decimal import Decimal, getcontext

from qtpy import API_NAME
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *

from cgwidgets.utils import (
    checkNegative,
    checkIfValueInRange,
    getGlobalPos,
    installInvisibleCursorEvent,
    installInvisibleWidgetEvent,
    installStickyAdjustDelegate,
    installSlideDelegate,
    removeSlideDelegate,
    updateStyleSheet
)

from cgwidgets.delegates import SlideDelegate

from cgwidgets.settings.colors import (iColor)
from cgwidgets.settings import attrs

from cgwidgets.widgets import AbstractFloatInputWidget, AbstractIntInputWidget, IntInputWidget


class LadderDelegate(QFrame):
    """
Widget that should be added as a popup during an event.  This should be
installed with the utils.installLadderDelegate(widget).

If you directly install this on a widget.  The widget must have the text/getText
methods (QLineEdit/QLabel).  If they do not, you need to subclass this and
reimplement the setValue() and getValue() methods or add those methods
to the parent widget.


Args:
    **  parent (QLineEdit) or (QLabel): widget to install ladder delegate onto.
            This currently works for QLineEdit and QLabel.  Other widgets will
            need to implement the 'setValue(value)' method to properly parse
            the value from the ladder to the widget.

    **  value_list (list) of (float): list of values for the user to be able
            to adjust by, usually this is set to .01, .1, 1, 10, etc

    **  user_input: (QEvent.Type):
            The action for the user to do to trigger the ladder to be installed
                ie.
            QEvent.MouseButtonRelease

Attributes:
    rgba_bg_slide (rgba int):
            The bg color that is displayed to the user when the use
            starts to click/drag to slide
    rgba_fg_slide (rgba int):
        The bg color that is displayed to the user when the use
        starts to click/drag to slide
    item_height (int): The height of each individual adjustable item.
            The middle item will always have the same geometry as the
            parent widget.
    middle_item (LadderFloatMiddleItem):
    ladder_items (list): of LadderItems
    ladder_type (attrs.TYPE): determines what type of ladder this is, an int, or float
        INTEGER | FLOAT
    middle_item_border_color (rgba int 0-255):
        The border color that is displayed to the user on the middle item
            ( value display widget )
    middle_item_border_width (int): The width of the border
        for the widget that displays the current value
    selection_color (rgba int 0-255):
        The color that is displayed to the user when they are selecting
        which value they wish to adjust
    slide_distance (float): multiplier of how far the user should
        have to drag in order to trigger a value update.  Lower
        values are slower, higher values are faster.
    user_input (QEvent): Event to be used on the widget to allow
        the trigger to popup the ladder delegate
           ie
            QEvent.MouseButtonRelease
Notes:
    -   The setValue, will then need to do the final math to calculate
            the result

--------------------------------------------------------------------------------
    """
    def __init__(
            self,
            parent=None,
            value_list=[0.001, 0.01, 0.1, 1, 10, 100, 1000],
            user_input=QEvent.MouseButtonRelease,
            range_min=None,
            range_max=None,
            allow_negative_values=True,
            allow_zero_value=True,
            ladder_type=attrs.FLOAT,
    ):
        super(LadderDelegate, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # default attrs
        self._slider_pos = 0
        self._updating = False
        self._ladder_items = []
        self.setUserInputTrigger(user_input)
        self.setMiddleItemBorderColor((18, 18, 18))
        self.setMiddleItemBorderWidth(5)
        self.setPixelsPerTick(100)
        self.setItemHeight(50)
        self.range_min = range_min
        self.range_max = range_max
        self._ladder_type = ladder_type

        if isinstance(parent, AbstractFloatInputWidget):
            self.setLadderType(attrs.FLOAT)
        if isinstance(parent, (AbstractIntInputWidget, IntInputWidget)):
            self.setLadderType(attrs.INTEGER)

        # setup default colors
        self._border_width = 3
        self.rgba_selection = iColor["rgba_selected_hover"]
        self.rgba_bg_slide = iColor["rgba_background_00"]
        self.rgba_fg_slide = iColor["rgba_background_01"]

        # create items
        self.middle_item_index = int(len(value_list) * 0.5)
        self.__createItems(value_list)

        # set significant digits
        # self.__setSignificantDigits()

        # set up style
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setWindowFlags(
            self.windowFlags()
            | Qt.FramelessWindowHint
            | Qt.Tool
        )
        self.updateStyleSheet()

        # post flight attr set
        self.middle_item.setRange(range_min, range_max)
        self.setAllowNegative(allow_negative_values)
        self.setAllowZero(allow_zero_value)

    """ API """
    def setAllowZero(self, enabled):
        self._allow_zero = enabled
        self.middle_item.setAllowZero(enabled)

    def setAllowNegative(self, enabled):
        self._allow_negative = enabled
        self.middle_item.setAllowNegative(enabled)

    def setDiscreteDrag(
        self,
        boolean,
        alignment=Qt.AlignRight,
        breed=SlideDelegate.UNIT,
        depth=50,
        display_widget=None
    ):
        """
        Discrete drag is a display mode that happens when
        the user manipulates an item in the ladder ( click + drag +release)

        On pen down, the cursor will dissapear and a visual cue will be added
        based on the alignment kwarg. Pen drag will update the visual cue
        to show the user how close they are to the next tick.

        Args:
            *   boolean (boolean): Whether or not to enable/disable discrete
                    drag mode
            **  depth (int): how wide/tall the widget should be depending
                    on its orientation
            **  alignment (QtCore.Qt.Align): where the widget should be align
                    relative to the display
            **  rgba_bg_slide (rgba int 0-255):
                    The bg color that is displayed to the user when the user
                    starts to click/drag to slide
            **  rgba_fg_slide (rgba int 0-255):
                    The bg color that is displayed to the user when the use
                    starts to click/drag to slide
            **  breed (SlideDelegate.TYPE): What type of visual cue to display.
                    Other options HUE, SATURATION, VALUE
            **  display_widget (QWidget): The widget to display the slide bar on
                    by default this will be the ladders parent
        """
        # delete old slidebar
        self.__setSlideBar(False)

        # set cursor drag mode
        # TODO invisible stuff
        #self.setInvisibleCursor(boolean)
        #self.setInvisibleWidget(boolean)

        # create new slide bar
        if not display_widget:
            self.display_widget = self.parent().parent()

        if boolean is True:
            self.__setSlideBar(
                boolean,
                depth=depth,
                alignment=alignment,
                breed=breed,
                display_widget=self.display_widget
            )

    def setInvisibleCursor(self, boolean):
        """
        When the mouse is click/dragged in each individual
        item, the cursor dissappears from the users view.  When
        the user releases the trigger, it will show the cursor again
        at the original clicking point.
        """
        for item in self.item_list:
            if not isinstance(item, LadderFloatMiddleItem):
                if boolean is True:
                    installInvisibleCursorEvent(item)
                elif boolean is False:
                    self.removeEventFilter(item)

    def setInvisibleWidget(self, boolean):
        """
        When the mouse is click/dragged in each individual
        item, ladder will dissapear from view.
        """

        if boolean is True:
            # installInvisibleWidgetEvent(item, hide_widget=self)
            installInvisibleWidgetEvent(self)
        elif boolean is False:
            self.removeEventFilter()

    def setLadderType(self, ladder_type):
        self._ladder_type = ladder_type

    def getLadderType(self):
        return self._ladder_type

    def getPixelsPerTick(self):
        return self._pixels_per_tick

    def setPixelsPerTick(self, _pixels_per_tick):
        self._pixels_per_tick = _pixels_per_tick

        for item in self.item_list:
            if item != self.middle_item:
                item._filter_STICKY.setPixelsPerTick(_pixels_per_tick)

    def setRange(self, range_min=None, range_max=None):
        """
        Determines if this widget has a specified range.  Going over this
        range will clip values into that range
        """
        self.range_min = range_min
        self.range_max = range_max

        self.middle_item.setRange(range_min, range_max)
        from cgwidgets.utils import removeStickyAdjustDelegate
        for widget in self.ladderItems():
            removeStickyAdjustDelegate(widget)

            installStickyAdjustDelegate(
                widget,
                pixels_per_tick=self.getPixelsPerTick(),
                value_per_tick=widget.valueMult(),
                activation_event=widget.activationEvent,
                deactivation_event=widget.deactivationEvent,
                range_min=self.range_min,
                range_max=self.range_max
            )

    def getUserInputTrigger(self):
        return self._user_input

    def setUserInputTrigger(self, user_input):
        self._user_input = user_input

    def setValue(self, value):
        """
        value (float): Sets the value on the parent widget.
            creating a setValue(value) method on the parent
            widget will run this method last when setting the value
        """
        if value is not None:
            # preflight checks on value
            value = checkNegative(self._allow_negative, value)
            value = checkIfValueInRange(float(value), self.range_min, self.range_max)
            if not self._allow_zero and not value:
                value = self.middle_item.getOrigValue()
            # set value
            self._value = value

            parent = self.parent()

            # update other widgets
            self.middle_item.setValue(str(self._value))

            # self.middle_item.setCursorPosition(0)
            try:
                parent.setText(str(self._value))
            except AttributeError:
                try:
                    self.parent().setValue(self._value)
                except AttributeError:
                    return None

    def getValue(self):
        """
        Returns:
            current parent widgets value. Will attempt to look for the
            default text() attr, however if it is not available, will look for
            the parents getValue() method.
        """
        try:
            if self.getLadderType() == attrs.FLOAT:
                self._value = float(self.parent().text())
            if self.getLadderType() == attrs.INTEGER:
                self._value = int(self.parent().text())
            return self._value
        except AttributeError:
            try:
                return self.parent().getValue()
            except AttributeError:
                return None
        except ValueError:
            return None

    """ COLORS """
    def updateStyleSheet(self):
        style_sheet_args = iColor.style_sheet_args
        update_kwargs = {
            'border_width': self.borderWidth(),
            'selected_color': repr(self.rgba_selection),
            'slider_pos1': self.slider_pos,
            'slider_pos2': self.slider_pos + 0.01,
            'rgba_bg_slide': self.rgba_bg_slide,
            'rgba_fg_slide': self.rgba_fg_slide,
        }

        style_sheet_args.update(update_kwargs)

        #
        style_sheet = """
        LadderDelegate{{
            background-color: rgba{rgba_background_00};
            border: {border_width}px solid rgba{rgba_selected_hover}
        }}
        LadderItem{{
            color: rgba{rgba_text};
            background-color: rgba{rgba_background_00}
        }}
        LadderItem::hover[is_drag_STICKY=false]{{
            background: qradialgradient(
                radius: 0.9,
                cx:0.50, cy:0.50,
                fx:0.5, fy:0.5,
                stop:0.5 rgba{rgba_background_00},
                stop:0.75 rgba{rgba_selected_hover});
        }}
        LadderItem[is_drag_STICKY=true]{{
            background: qradialgradient(
                radius: 0.9,
                cx:0.50, cy:0.50,
                fx:0.5, fy:0.5,
                stop:0.5 rgba{rgba_background_00},
                stop:0.75 rgba{rgba_selected_hover});
        }}
        LadderItem[gradient_on=true]{{background: qlineargradient(
           x1:{slider_pos1} y1:0,
           x2:{slider_pos2} y2:0,
           stop:0 rgba{rgba_bg_slide},
           stop:1 rgba{rgba_fg_slide}
       );
       }}
        """.format(**style_sheet_args)

        self.setStyleSheet(style_sheet)

    @property
    def rgba_bg_slide(self):
        return self._rgba_bg_slide

    @rgba_bg_slide.setter
    def rgba_bg_slide(self, color):
        self._rgba_bg_slide = color

        # update slidebar
        for item in self.item_list:
            if not isinstance(item, LadderFloatMiddleItem):
                item.slidebar.rgba_bg_slide = color

    @property
    def rgba_fg_slide(self):
        return self._rgba_fg_slide

    @rgba_fg_slide.setter
    def rgba_fg_slide(self, rgba_fg_slide):
        self._rgba_fg_slide = rgba_fg_slide

        # update slidebar
        for item in self.item_list:
            if not isinstance(item, LadderFloatMiddleItem):
                    item.slidebar.rgba_fg_slide = rgba_fg_slide

    @property
    def rgba_selection(self):
        return self._rgba_selection

    @rgba_selection.setter
    def rgba_selection(self, rgba_selection):
        self._rgba_selection = rgba_selection

    def getMiddleItemBorderColor(self):
        return self._middle_item_border_color

    def setMiddleItemBorderColor(self, border_color):
        self._middle_item_border_color = border_color

    def getMiddleItemBorderWidth(self):
        return self._middle_item_border_width

    def setMiddleItemBorderWidth(self, border_width):
        self._middle_item_border_width = border_width

    def borderWidth(self):
        return self._border_width

    def setBorderWidth(self, border_width):
        self._border_width = border_width

    """ SIZE """
    def getItemHeight(self):
        return self._item_height

    def setItemHeight(self, item_height):
        self._item_height = item_height

    """ PROPERTIES """
    @property
    def middle_item_index(self):
        """
        middle_item_index (int): Index of the middle item in the item's list.
            This is used to offset the middle item to overlay the widget it was
            used on.
        """
        return self._middle_item_index

    @middle_item_index.setter
    def middle_item_index(self, middle_item_index):
        self._middle_item_index = middle_item_index

    @property
    def current_item(self):
        """
        current_item (LadderItem): The current item that the user is manipulating.
            This property is currently used to determine if this ladder item
            should have its visual appearance changed on interaction.
        """
        return self._current_item

    @current_item.setter
    def current_item(self, current_item):
        self._current_item = current_item

    @property
    def item_list(self):
        """
        item_list (list): list of all of the ladder items
        """
        if not hasattr(self, '_item_list'):
            self._item_list = []
        return self._item_list

    @item_list.setter
    def item_list(self, item_list):
        """
        list of widgets
        """
        self._item_list = item_list

    @property
    def slider_pos(self):
        return self._slider_pos

    @slider_pos.setter
    def slider_pos(self, slider_pos):
        self._slider_pos = slider_pos

    """ UTILS """
    def __createItems(self, value_list):
        """
        Creates all of the item labels/inputs for the ladder.

        Args:
            value_list (list): of floats that will determine the slide
                options available to the user.
        """

        # create widgets
        for value in value_list:
            widget = LadderItem(
                parent=self,
                value_mult=value
            )
            self.layout().addWidget(widget)
            self.item_list.append(widget)

            installStickyAdjustDelegate(
                widget,
                pixels_per_tick=self.getPixelsPerTick(),
                value_per_tick=value,
                activation_event=widget.activationEvent,
                deactivation_event=widget.deactivationEvent,
                range_min=self.range_min,
                range_max=self.range_max
            )
            self.ladderItems().append(widget)

        self.__createMiddleItem()

    def __createMiddleItem(self):
        """
        Creates the middle item which is a AbstractFloatInputWidget for the user.
        """
        # special handler for display widget
        if self.getLadderType() == attrs.INTEGER:
            self.middle_item = LadderIntMiddleItem(
                parent=self,
                value=self.getValue()
            )
        else:
            self.middle_item = LadderFloatMiddleItem(
                parent=self,
                value=self.getValue()
            )
        if hasattr(self.parent(), "userFinishedEditingEvent"):
            self.middle_item.setUserFinishedEditingEvent(self.parent().userFinishedEditingEvent)
        self.layout().insertWidget(self.middle_item_index, self.middle_item)

        # populate item list
        item_list = self.item_list
        item_list.insert(self.middle_item_index, self.middle_item)
        self.item_list = item_list

    def __updateDelegateGeometry(self):
        """ Updates any user inputs using the getter/setter methods.

        This is necessary because we are created this widget on
        demand, so if we do not manually update during the
        show event, it will not update the user set attributes.
        """
        self.__updateItemSize()
        self.__updatePosition()

    def __updateItemSize(self):
        """ Sets each individual item's size's.

        These sizes will correspond to the getItemHeight and parents widgets width

        Note:
            This is also probably where I will be installing a delegate
            for a horizontal ladder layout...
        """
        # set adjustable items
        height = self.getItemHeight()
        width = self.parent().width()

        # update main width
        self.setFixedWidth(width + self.borderWidth() * 2)

        for item in self.item_list:
            item.setFixedSize(width, height)

        # set display item ( middle item)
        self.middle_item.setFixedSize(width, self.parent().height())

    def __updatePosition(self):
        """ sets the position of the delegate relative to the widget that it is adjusting """
        pos = getGlobalPos(self.parentWidget())
        # set position
        offset = self.middle_item_index * self.getItemHeight()
        pos = QPoint(
            pos.x(),
            pos.y() - offset
        )
        self.move(pos)

    def __setSlideBar(
        self,
        enabled,
        alignment=Qt.AlignRight,
        depth=50,
        breed=SlideDelegate.UNIT,
        display_widget=None
    ):
        """
        Creates a visual bar on the screen to show the user
        how close they are to creating the next tick
        """
        for item in self.item_list:
            if not isinstance(item, LadderFloatMiddleItem):
                if enabled is True:
                    slidebar = installSlideDelegate(
                        item,
                        sliderPosMethod=item.getCurrentPos,
                        breed=breed,
                        display_widget=display_widget
                    )
                    slidebar.rgba_bg_slide = self.rgba_bg_slide
                    slidebar.rgba_fg_slide = self.rgba_fg_slide
                    slidebar.setDepth(depth)

                    slidebar.setAlignment(alignment)
                    item.slidebar = slidebar

                elif enabled is False:
                    try:
                        removeSlideDelegate(item, item.slidebar)
                    except AttributeError:
                        pass

    """ WIDGETS """
    def ladderItems(self):
        return self._ladder_items

    def middleItem(self):
        return self.middle_item

    """ EVENTS """
    def leaveEvent(self, event, *args, **kwargs):
        """When the cursor leaves the widget, this will hide the ladder if the
        user is not manipulating the object.

        This will also set the cursor position to the one that is currently selected in the middle item
        """
        if self._updating is True:
            return
        cursor_position = self.middle_item.cursorPosition()
        self.hide()
        self.parent().setCursorPosition(cursor_position)
        return QFrame.leaveEvent(self, event, *args, **kwargs)

    def hideEvent(self, event, *args, **kwargs):
        """
        Resets the cursor on the input widget to 0, so that
        it won't do the awesome wonky alignment
        """
        return QWidget.hideEvent(self, event, *args, **kwargs)

    def showEvent(self, *args, **kwargs):
        self.middle_item.setValue(self.getValue())

        # reset cursor position
        cursor_position = self.parent().cursorPosition()
        self.__updateDelegateGeometry()

        self.raise_()
        self.activateWindow()
        self.middle_item.setFocus()
        self.middle_item.setCursorPosition(cursor_position)

        return QWidget.showEvent(self, *args, **kwargs)

    def mouseMoveEvent(self, event):
        return QFrame.mouseMoveEvent(self, event)

    def enterEvent(self, event):
        # TODO wtf do I do with this escape velocity BS
        # its a mouse polling thing it seems...
        # self._drag_STICKY = False
        # # reset sticky drag
        # for item in self.item_list:
        #     if item != self.middle_item:
        #         item.unsetCursor()
        #         item.setProperty('is_drag_STICKY', self._drag_STICKY)
        #         item.setGradientEnable(False)
        QFrame.enterEvent(self, event)

    def keyPressEvent(self, event, *args, **kwargs):
        if event.key() == Qt.Key_Escape:
            self.hide()
        return QFrame.keyPressEvent(self, event, *args, **kwargs)

    def eventFilter(self, obj, event, *args, **kwargs):
        """
        installed on the parent widget to determine the user input
        for triggering the ladder delegate
        """
        if self.getValue() is None:
            # print('This widgets like numbers. Not whatever you put in here.')
            return QWidget.eventFilter(self, obj, event, *args, **kwargs)

        # TODO: LEGACY PYQT
        # will only need the else clause
        # the rest of it is just a hack to make it work in katana =\
        if hasattr(self.parent(), 'selectionLength'):
            if self.parent().selectionLength() == 0:
                if event.type() == self.getUserInputTrigger():
                    self.show()
        else:
            if event.type() == self.getUserInputTrigger():
                self.show()

        return QFrame.eventFilter(self, obj, event, *args, **kwargs)


# todo move middle items to abstract class
class iMiddleItem(object):
    def mousePressEvent(self, event):
        return self.__class__.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        return self.__class__.mouseReleaseEvent(self, event)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.parent().hide()
        return self.__class__.keyPressEvent(self, event)

    def setMiddleValue(self):
        self.parent().parent().setValue(str(self.text()))

    def setValue(self, value):
        self.setText(str(value))
        self._value = value


class LadderIntMiddleItem(AbstractIntInputWidget, iMiddleItem):
    """
This is the display label to overlayover the current widget.
Due to how awesomely bad transparency is to do in Qt =\
I made this a widget instead of transparency... in hindsite...
I guess I could have done a mask.

Args:
    **  parent (LadderDelegate)
    **  value (float): the default value to display

Attributes:
    value (float): display value that should be the value
        that is returned to the parent widget during user manipulation.
    """
    def __init__(self, parent=None, value=None):
        super(LadderIntMiddleItem, self).__init__(parent)
        if API_NAME == "PySide2":
            iMiddleItem.__init__(self, value)
        self.setValue(value)
        self.editingFinished.connect(self.setMiddleValue)
        self.setAlignment(Qt.AlignCenter | Qt.AlignHCenter)
        self.rgba_background = iColor["rgba_background_01"]
        self.updateStyleSheet()

    def getValue(self):
        return int(self._value)


class LadderFloatMiddleItem(AbstractFloatInputWidget, iMiddleItem):
    """
This is the display label to overlayover the current widget.
Due to how awesomely bad transparency is to do in Qt =\
I made this a widget instead of transparency... in hindsite...
I guess I could have done a mask.

Args:
    **  parent (LadderDelegate)
    **  value (float): the default value to display

Attributes:
    value (float): display value that should be the value
        that is returned to the parent widget during user manipulation.
    """
    def __init__(self, parent=None, value=None):
        super(LadderFloatMiddleItem, self).__init__(parent)
        self.setValue(value)
        self.editingFinished.connect(self.setMiddleValue)
        self.setAlignment(Qt.AlignCenter | Qt.AlignHCenter)
        self.rgba_background = iColor["rgba_background_01"]
        self.updateStyleSheet()

    def getValue(self):
        return float(self._value)


class LadderItem(QLabel):
    """
This represents one item in the ladder that is displayed to the user.
Clicking/Dragging left/right on one of these will update the widget
that is passed to the ladder delegate.

Args:
    **  value_mult (float): how many units the drag should update
    """
    def __init__(
        self,
        parent=None,
        value_mult=''
    ):
        super(LadderItem, self).__init__(parent)

        # set default attrs
        self.setProperty("is_drag_STICKY", False)
        self._value_mult = value_mult
        self.setText(str(value_mult))
        self.setAlignment(Qt.AlignCenter | Qt.AlignHCenter)

    def valueMult(self):
        return self._value_mult

    def setGradientEnable(self, enable):
        """
        Turns the property gradient_on On/Off.  This property will determine if
        the gradient should be shown when sliding.
        """
        item_list = self.parent().item_list
        for index, item in enumerate(item_list):
            if item != self:
                item.setProperty('gradient_on', enable)
                updateStyleSheet(item)

    def getValue(self):
        return self.parent().getValue()

    def setValue(self, value):
        self.parent().setValue(value)

    """ UTILS """
    def __updateGradient(self):
        slider_pos = math.fabs(self._slider_pos)
        self.parent().slider_pos = slider_pos
        self.parent().updateStyleSheet()

    def activationEvent(self, *args):
        input_widget = self.parent().parent()
        input_widget._updating = True
        self.parent()._updating = True
        self.parent().hide()

    def deactivationEvent(self, *args):
        input_widget = self.parent().parent()
        input_widget._updating = False
        self.parent()._updating = False
        self.parent().show()


def main():
    import sys
    app = QApplication(sys.argv)

    from cgwidgets.utils import installLadderDelegate

    class TestWidget(QLineEdit):
        def __init__(self, parent=None, value=0):
            super(TestWidget, self).__init__(parent)
            pos = QCursor().pos()
            self.setGeometry(pos.x(), pos.y(), 200, 100)
            value_list = [0.001, 0.01, 0.1, 1, 10, 100, 1000]
            ladder = installLadderDelegate(
                self,
                user_input=QEvent.MouseButtonRelease,
                value_list=value_list
            )

        def setValue(self, value):
            self.setText(str(value))

    mw = QWidget()

    ml = QVBoxLayout()
    mw.setLayout(ml)

    w2 = QWidget(mw)
    l2 = QVBoxLayout()
    w2.setLayout(l2)
    float_input = AbstractFloatInputWidget()
    float_input.setDoMath(True)
    ladder = installLadderDelegate(float_input, allow_zero_value=False, allow_negative_values=False)
    def editingComplete(widget, value):
        print(widget, value)
    float_input.setUserFinishedEditingEvent(editingComplete)
    float_input.setText('12')
    #ladder.setInvisibleWidget(True)


    #ladder.setDiscreteDrag(True, alignment=Qt.AlignLeft, depth=10, display_widget=w2)
    # ladder.setDiscreteDrag(
    #     True,
    #     alignment=Qt.AlignBottom,
    #     depth=10,
    #     display_widget=w2
    #     )
    # ladder.setMiddleItemBorderColor((255, 0, 255))
    # ladder.setMiddleItemBorderWidth(2)
    # ladder.setItemHeight(50)
    # ladder.rgba_fg_slide = (255, 128, 32, 255)
    # ladder.rgba_bg_slide = (0, 128, 255, 255)

    l2.addWidget(float_input)
    l2.addWidget(QPushButton('BUTTTON'))
    l2.addWidget(QLabel('LABELLLLL'))

    ml.addWidget(w2)
    mw.show()
    mw.move(QCursor.pos())

    sys.exit(app.exec_())


if __name__ == '__main__':

    main()


    #help(LadderDelegate)
