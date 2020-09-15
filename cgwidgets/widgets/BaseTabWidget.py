"""
TODO:
    - Default sizes
    - set up colors
    - set up handle widths

"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QBoxLayout, QStackedLayout, QVBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt


from cgwidgets.utils import getWidgetAncestor

try:
    from cgwidgets.BaseSplitterWidget import BaseSplitterWidget
except ImportError:
    from BaseSplitterWidget import BaseSplitterWidget


class BaseTabWidget(BaseSplitterWidget):
    """
    This is the designing portion of this editor.  This is where the TD
    will design a custom UI/hooks/handlers for the tool for the end user,
    which will be displayed in the ViewWidget

    Args:
        direction (BaseTabWidget.DIRECTION): Determines where the tab
            bar should be placed.  The default value is NORTH
        type (BaseTabWidget.TYPE): What type of tab widget this should be,
            options are STACKED | DYNAMIC | MULTI
            see class attrs for more info...
        selected_labels_list (list): list of labels that are currently selected by the user
    Class Attrs:
        TYPE
            STACKED: Will operate like a normal tab, where widgets
                will be stacked on top of each other)
            DYNAMIC: There will be one widget that is dynamically
                updated based off of the labels args
            MULTI: Similair to stacked, but instead of having one
                display at a time, multi tabs can be displayed next
                to each other.
    Essentially this is a custom tab widget.  Where the name
        label: refers to the small part at the top for selecting selctions
        bar: refers to the bar at the top containing all of the afformentioned tabs
        widget: refers to the area that displays the GUI for each tab

    Widgets:
        |-- QBoxLayout
                |-- TabLabelBarWidget
                        |-- QBoxLayout
                                |-* TabLabelWidget
                |-- main_layout
                        This needs to be changed...
                        This is the control for dynamic vs stacked...
                        and it essentially swaps the layouts
                        - move to abstractSplitterWidget
                        - SplitterStackedWidget
                            - get index
                            - set index

    """
    NORTH = 'north'
    SOUTH = 'south'
    EAST = 'east'
    WEST = 'west'
    OUTLINE_COLOR = (200, 100, 0, 255)
    OUTLINE_WIDTH = 1
    SELECTED_COLOR = (200, 100, 0, 255)
    STACKED = 'stacked'
    DYNAMIC = 'dynamic'
    MULTI = False
    TYPE = STACKED

    def __init__(self, parent=None, direction=NORTH):
        super(BaseTabWidget, self).__init__(parent)
        # set up splitter
        self.setHandleWidth(0)
        style_sheet = """
            QSplitter::handle {
                border: None;
            }
        """
        self.setStyleSheet(style_sheet)

        # create widgets
        self.tab_label_bar_widget = TabLabelBarWidget(self)
        self.main_widget = BaseSplitterWidget(self)

        self.addWidget(self.tab_label_bar_widget)
        self.addWidget(self.main_widget)

        # set default attrs
        self.setType(BaseTabWidget.TYPE)
        # self.tab_width = 100
        # self.tab_height = 35

        # set direction
        self.setTabPosition(direction)

        # set multi
        self.setMultiSelect(BaseTabWidget.MULTI)

        self._selected_labels_list = []

    """ UTILS """
    def setTabPosition(self, direction):
        """
        Sets the orientation of the tab bar relative to the main widget.
        This is done by setting the direction on this widget, and then
        setting the layout direction on the tab label bar widget

        Args:
            direction (QVBoxLayout.DIRECTION): The direction that this widget
                should be layed out in.  Where the tab label bar will always be
                the first widget added
        """
        self.tab_direction = direction

        if direction == BaseTabWidget.NORTH:
            self.setDirection(QBoxLayout.TopToBottom)
            self.tab_label_bar_widget.layout().setDirection(QBoxLayout.LeftToRight)
        elif direction == BaseTabWidget.SOUTH:
            self.setDirection(QBoxLayout.BottomToTop)
            self.tab_label_bar_widget.layout().setDirection(QBoxLayout.LeftToRight)
        elif direction == BaseTabWidget.EAST:
            self.setDirection(QBoxLayout.RightToLeft)
            self.tab_label_bar_widget.layout().setDirection(QBoxLayout.TopToBottom)
        elif direction == BaseTabWidget.WEST:
            self.setDirection(QBoxLayout.LeftToRight)
            self.tab_label_bar_widget.layout().setDirection(QBoxLayout.TopToBottom)
        self.tab_label_bar_widget.updateStyleSheets()

    def getDirection(self):
        return self._direction

    def setDirection(self, direction):
        """
        Sets the current direction this widget.  This is the orientation of
        where the tab labels will be vs where the main widget will be, where
        the tab labels bar will always be the first widget.
        """
        self._direction = direction
        self.main_widget.setParent(None)
        self.tab_label_bar_widget.setParent(None)
        if direction == QBoxLayout.LeftToRight:
            self.addWidget(self.tab_label_bar_widget)
            self.addWidget(self.main_widget)
            self.setOrientation(Qt.Horizontal)
        elif direction == QBoxLayout.RightToLeft:
            self.addWidget(self.main_widget)
            self.addWidget(self.tab_label_bar_widget)
            self.setOrientation(Qt.Horizontal)
        elif direction == QBoxLayout.TopToBottom:
            self.addWidget(self.tab_label_bar_widget)
            self.addWidget(self.main_widget)
            self.setOrientation(Qt.Vertical)
        elif direction == QBoxLayout.BottomToTop:
            self.addWidget(self.main_widget)
            self.addWidget(self.tab_label_bar_widget)
            self.setOrientation(Qt.Vertical)

    def insertTab(self, index, widget, name, tab_label=None):
        """
        Creates a new tab at  the specified index

        Args:
            index (int): index to insert widget at
            widget (QWidget): widget to be displayed at that index
            name (str): name of widget
            tab_label (widget): If provided this will use the widget
                provided as a label, as opposed to the default one.
        """

        if self.getType() == BaseTabWidget.STACKED:
            # insert tab widget
            self.main_widget.insertWidget(index, widget)
        # widget.setStyleSheet("""border: 1px solid rgba(0,0,0,255)""")
        # create tab label widget
        if not tab_label:
            tab_label = TabLabelWidget(self, name, index)
        tab_label.tab_widget = widget

        self.tab_label_bar_widget.insertWidget(index, tab_label)

        # update all label index
        self.__updateAllTabLabelIndexes()

    def removeTab(self, index):
        self.tab_label_bar_widget.itemAt(index).widget().setParent(None)
        self.tab_widget_layout.itemAt(index).widget().setParent(None)
        self.__updateAllTabLabelIndexes()

    def __updateAllTabLabelIndexes(self):
        """
        Sets the tab labels index to properly update to its current
        position in the Tab Widget.
        """
        for index, label in enumerate(self.tab_label_bar_widget.getAllLabels()):
            label.index = index

    """ DYNAMIC WIDGET """
    def createNewDynamicWidget(self):
        dynamic_widget_class = self.getDynamicWidgetBaseClass()
        new_widget = dynamic_widget_class()
        return new_widget

    def getDynamicMainWidget(self):
        return self._dynamic_widget

    def __dynamicWidgetFunction(self):
        pass

    def setDynamicUpdateFunction(self, function):
        self.__dynamicWidgetFunction = function

    def setDynamicWidgetBaseClass(self, widget):
        """
        Sets the constructor for the dynamic widget.  Everytime
        a new dynamic widget is created. It will use this base class
        """
        self._dynamic_widget_base_class = widget

    def getDynamicWidgetBaseClass(self):
        return self._dynamic_widget_base_class

    def updateDynamicWidget(self, widget, label, *args, **kwargs):
        """
        Updates the dynamic widget

        Args:
            widget (DynamicWidget) The dynamic widget that should be updated
            label (TabLabelWidget): The tab label that should be updated
        """
        # needs to pick which to update...
        self.__dynamicWidgetFunction(widget, label, *args, **kwargs)

    """ EVENTS """
    def showEvent(self, event):
        # super(BaseTabWidget, self).showEvent(event)
        # direction = self.getDirection()
        # all_labels = self.tab_label_bar_widget.getAllLabels()
        #
        # # horizontal
        # if direction in [QBoxLayout.LeftToRight, QBoxLayout.RightToLeft]:
        #     for label in all_labels:
        #         label.setFixedHeight(self.tab_width)
        #     pass
        # # vertical
        # elif direction in [QBoxLayout.TopToBottom, QBoxLayout.BottomToTop]:
        #     for label in all_labels:
        #         label.setFixedWidth(self.tab_height)
        return BaseSplitterWidget.showEvent(self, event)

    """ PROPERTIES """
    def setMultiSelect(self, enabled):
        self._multi_select = enabled

    def getMultiSelect(self):
        return self._multi_select

    def setMultiSelectDirection(self, orientation):
        """
        Sets the orientation of the multi select mode.

        orientation (Qt.ORIENTATION): ie Qt.Vertical or Qt.Horizontal
        """
        pass
        self.main_widget.setOrientation(orientation)

    def getMultiSelectDirection(self):
        return self.main_widget.orientation()

    def setType(self, value, dynamic_widget=None, dynamic_function=None):
        """
        Sets the type of this widget.  This will reset the entire layout to a blank
        state.

        Args:
            value (BaseTabWidget.TYPE): The type of tab menu that this
                widget should be set to
            dynamic_widget (QWidget): The dynamic widget to be displayed.
            dynamic_function (function): The function to be run when a label
                is selected.
        """
        # reset tab label bar
        if hasattr(self, 'tab_label_bar_widget'):
            self.tab_label_bar_widget.setParent(None)
        self.tab_label_bar_widget = TabLabelBarWidget(self)
        self.insertWidget(0, self.tab_label_bar_widget)

        # clear layout
        self.main_widget.clear()

        # update layout
        if value == BaseTabWidget.STACKED:
            pass
        elif value == BaseTabWidget.DYNAMIC:
            # preflight check
            if not dynamic_widget:
                print ("provide a widget to use...")
                return
            if not dynamic_function:
                print ("provide a function to use...")
                return
            self.setDynamicWidgetBaseClass(dynamic_widget)
            self.setDynamicUpdateFunction(dynamic_function)

            self.dynamic_widget = self.createNewDynamicWidget()
            self.main_widget.addWidget(self.dynamic_widget)

        # update attr
        self._type = value

    def getType(self):
        return self._type

    def setSelectedLabelsList(self, selected_labels_list):
        self._selected_labels_list = selected_labels_list

    def getSelectedLabelsList(self):
        return self._selected_labels_list

    def appendLabelToList(self, label):
        self.getSelectedLabelsList().append(label)

    def removeLabelFromList(self, label):
        self.getSelectedLabelsList().remove(label)

    @property
    def tab_direction(self):
        return self._tab_direction

    @tab_direction.setter
    def tab_direction(self, tab_direction):
        self._tab_direction = tab_direction

    @property
    def tab_width(self):
        return self._tab_width

    @tab_width.setter
    def tab_width(self, tab_width):
        self._tab_width = tab_width

    @property
    def tab_height(self):
        return self._tab_height

    @tab_height.setter
    def tab_height(self, tab_height):
        self._tab_height = tab_height


class TabLabelBarWidget(QWidget):
    """
    The top bar of the Two Faced Design Widget containing all of the tabs
    """
    def __init__(self, parent=None):
        super(TabLabelBarWidget, self).__init__(parent)
        QBoxLayout(QBoxLayout.LeftToRight, self)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def insertWidget(self, index, widget):
        self.layout().insertWidget(index, widget)

    def clearSelectedTabs(self):
        """
        Removes the current tab from being selected
        """
        for index in range(self.layout().count()):
            tab_label = self.layout().itemAt(index).widget()
            tab_label.is_selected = False

    def getAllLabels(self):
        """
        Gets all of the Tab Labels in this bar

        returns (list): of TabLabelWidget
        """
        _all_labels = []
        for index in range(self.layout().count()):
            label = self.layout().itemAt(index).widget()
            _all_labels.append(label)

        return _all_labels

    def updateStyleSheets(self):
        labels = self.getAllLabels()
        for label in labels:
            label.setupStyleSheet()


class TabLabelWidget(QLabel):
    """
    This is the tab's tab.

    Attributes:
        is_selected (bool): Determines if this label is currently selected
        tab_widget (widget): The widget that this label correlates to.

    TODO:
        *   Update Font Size dynamically:
                if prefKey == PrefNames.APPLICATION_FONTSIZE
                prefChanged
                self.setFixedHeight(self.height() * 2)
    """
    def __init__(self, parent, text, index):
        super(TabLabelWidget, self).__init__(parent)
        # set up attrs
        self.setText(text)
        self.index = index

        # set up display
        self.setAlignment(Qt.AlignCenter)
        self.is_selected = False
        TabLabelWidget.setupStyleSheet(self)
        self.setMinimumSize(35, 35)

    @staticmethod
    def setupStyleSheet(item):
        """
        Sets the style sheet for the outline based off of the direction of the parent.

        """
        tab_widget = getWidgetAncestor(item, BaseTabWidget)
        direction = tab_widget.tab_direction
        style_sheet_args = [
            repr(BaseTabWidget.OUTLINE_COLOR),
            repr(BaseTabWidget.SELECTED_COLOR),
            BaseTabWidget.OUTLINE_WIDTH
        ]
        if direction == BaseTabWidget.NORTH:
            style_sheet = """
            QLabel:hover{{color: rgba{0}}}
            QLabel[is_selected=false]{{
                border: {2}px solid rgba{0};
                border-top: None;
                border-left: None;
            }}
            QLabel[is_selected=true]{{
                border: {2}px solid rgba{0} ;
                border-left: None;
                border-bottom: None;
                color: rgba{1};
            }}
            """.format(*style_sheet_args)
        elif direction == BaseTabWidget.SOUTH:
            style_sheet = """
            QLabel:hover{{color: rgba{0}}}
            QLabel[is_selected=false]{{
                border: {2}px solid rgba{0};
                border-left: None;
                border-bottom: None;
            }}
            QLabel[is_selected=true]{{
                border: {2}px solid rgba{0} ;
                border-left: None;
                border-top: None;
                color: rgba{1};
            }}
            """.format(*style_sheet_args)
        elif direction == BaseTabWidget.EAST:
            style_sheet = """
            QLabel:hover{{color: rgba{0}}}
            QLabel[is_selected=false]{{
                border: {2}px solid rgba{0};
                border-top: None;
                border-right: None;
            }}
            QLabel[is_selected=true]{{
                border: {2}px solid rgba{0} ;
                border-top: None;
                border-left: None;
                color: rgba{1};
            }}
            """.format(*style_sheet_args)
        elif direction == BaseTabWidget.WEST:
            style_sheet = """
            QLabel:hover{{color: rgba{0}}}
            QLabel[is_selected=false]{{
                border: {2}px solid rgba{0};
                border-top: None;
                border-left: None;
            }}
            QLabel[is_selected=true]{{
                border: {2}px solid rgba{0} ;
                border-top: None;
                border-right: None;
                color: rgba{1};
            }}
            """.format(*style_sheet_args)
        item.setStyleSheet(style_sheet)

    def mousePressEvent(self, event):
        # get attrs
        top_level_widget = getWidgetAncestor(self, BaseTabWidget)
        is_multi_select = top_level_widget.getMultiSelect()
        modifiers = event.modifiers()

        # set up multi select
        if is_multi_select is True:
            # toggle
            if modifiers == Qt.ControlModifier:
                labels_list = top_level_widget.getSelectedLabelsList()
                if self in labels_list:
                    self.is_selected = False
                    top_level_widget.removeLabelFromList(self)
                else:
                    self.is_selected = True
                    top_level_widget.appendLabelToList(self)
            # reset list
            else:
                TabLabelWidget.__setExclusiveSelect(self)
        # set up single select
        else:
            TabLabelWidget.__setExclusiveSelect(self)

    @staticmethod
    def __setExclusiveSelect(item):
        """
        Sets this to be the ONLY tab selected by the user
        """

        top_level_widget = getWidgetAncestor(item, BaseTabWidget)
        item.parent().clearSelectedTabs()
        item.is_selected = True

        # isolate widget
        if top_level_widget.getType() == BaseTabWidget.STACKED:
            top_level_widget.main_widget.isolateWidgets([item.tab_widget])

        elif top_level_widget.getType() == BaseTabWidget.DYNAMIC:
            top_level_widget.main_widget.clear(exclusion_list=[top_level_widget.dynamic_widget])
            top_level_widget.updateDynamicWidget(top_level_widget.dynamic_widget, item)

        # append to selection list
        top_level_widget.setSelectedLabelsList([item])

    @staticmethod
    def updateDisplay(item):
        """
        Determines whether or not an items tab_widget should be
        displayed/updated/destroyed.
        """
        # update display
        if not hasattr(item, 'tab_widget'): return

        top_level_widget = getWidgetAncestor(item, BaseTabWidget)

        # update static widgets
        if top_level_widget.getType() == BaseTabWidget.STACKED:
            if item.is_selected:
                item.tab_widget.show()
            else:
                item.tab_widget.hide()

        # update dynamic widgets
        if top_level_widget.getType() == BaseTabWidget.DYNAMIC:
            if item.is_selected:
                # create new dynamic widget...
                new_dynamic_widget = top_level_widget.createNewDynamicWidget()
                top_level_widget.main_widget.addWidget(new_dynamic_widget)
                item.tab_widget = new_dynamic_widget
                top_level_widget.updateDynamicWidget(new_dynamic_widget, item)
            else:
                # destroy widget
                item.tab_widget.setParent(None)

    """ PROPERTIES """
    @property
    def is_selected(self):
        return self._is_selected

    @is_selected.setter
    def is_selected(self, is_selected):
        self.setProperty('is_selected', is_selected)
        self._is_selected = is_selected
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

        TabLabelWidget.updateDisplay(self)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self._index = index

    @property
    def tab_widget(self):
        return self._tab_widget

    @tab_widget.setter
    def tab_widget(self, tab_widget):
        self._tab_widget = tab_widget


class DynamicTabWidget(BaseTabWidget):
    def __init__(self, parent=None):
        super(DynamicTabWidget, self).__init__(parent)


class TabDynamicWidgetExample(QWidget):
    def __init__(self, parent=None):
        super(TabDynamicWidgetExample, self).__init__(parent)
        QVBoxLayout(self)
        self.label = QLabel('init')
        self.layout().addWidget(self.label)

    @staticmethod
    def updateGUI(widget, label):
        if label:
            widget.label.setText(label.text())


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QCursor
    app = QApplication(sys.argv)

    w = BaseTabWidget()

    # stacked widget example
    w.setType(BaseTabWidget.STACKED)
    w.setTabPosition(BaseTabWidget.NORTH)
    w.setMultiSelect(True)
    w.setMultiSelectDirection(Qt.Horizontal)
    #
    # for x in range(3):
    #     nw = QLabel(str(x))
    #     w.insertTab(0, nw, str(x))

    # # dynamic widget example
    #dw = TabDynamicWidgetExample
    w.setType(BaseTabWidget.DYNAMIC, dynamic_widget=TabDynamicWidgetExample, dynamic_function=TabDynamicWidgetExample.updateGUI)

    for x in range(3):
        nw = QLabel(str(x))
        w.insertTab(0, nw, str(x))

    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())
