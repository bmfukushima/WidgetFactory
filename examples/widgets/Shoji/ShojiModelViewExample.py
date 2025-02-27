"""
The ShojiModelViewWidget ( which needs a better name, potentially "Shoji Widget" )
is essentially a Tab Widget which replaces the header with either a ListView, or a
TreeView containing its own internal model.  When the user selects an item in the view, the Delegate, will be updated
with a widget provided by one of two modes.
    Stacked (ezmode):
        All widgets are created upon construction, and they are hidden/shown
        as the user clicks on different items
    Dynamic (notasezmode)
        Widgets are constructed on demand.  These widgets can either be provided
        as one widget to rule them all, or can be provided per item, so that
        sets of items can utilize the same constructors.

Header (ModelViewWidget):
    The header is what is what is usually called the "View" on the ModelView system.
    However, due to how the ShojiModelViewWidget works, header is a better term.  This
    header will display the View for the model, along with its own internal delegate
    system that will allow you to register widgets that will popup on Modifier+Key Combos.
    These delegates can be used for multiple purposes, such as setting up filtering of the
    view, item creation, etc.TREE

Delegate (ShojiLayout):
    This is the area that displays the widgets when the user selects different items in the
    header.  If multi select is enabled, AND the user selects multiple items, the delegate
    will display ALL of the widgets to the user.  Any widget can become full screen by pressing
    the ~ key (note that this key can also be set using ShojiLayout.FULLSCREEN_HOTKEY class attr),
    and can leave full screen by pressing the ESC key.  Pressing the ESC key harder will earn you
    epeen points for how awesome you are.  The recommended approach is to use both hands and slam
    them down on the ESC key for maximum effect.  Bonus points are earned if the key board is lifted
    off the desk, and/or keys fly off the keyboard, and/or people stare at you as you yell FUUCCKKKKKK
    as you display your alpha status.  For those of you to dense to get it, this was a joke, if you
    didn't get that this was a joke, please feel free to take a moment here to do one of the following
    so that you feel like you fit in with everyone else:
        LOL | ROFL | LMAO | HAHAHA

Hierachy
    ShojiModelViewWidget --> (QSplitter, iShojiDynamicWidget):
        |-- QBoxLayout
            | -- headerWidget --> ModelViewWidget --> QSplitter
                    |-- view --> (AbstractDragDropListView | AbstractDragDropTreeView) --> QSplitter
                        |-- model --> AbstractDragDropModel
                            |-* AbstractDragDropModelItems
                    |* delegate --> QWidget

            | -- Scroll Area
                |-- DelegateWidget (ShojiMainDelegateWidget --> ShojiLayout)
                        | -- _temp_proxy_widget (QWidget)
                        | -* ShojiModelDelegateWidget (AbstractGroupBox)
                                | -- Stacked/Dynamic Widget (main_widget)

"""
import sys, os
# os.environ['QT_API'] = 'pyside2'
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QLabel, QLineEdit, QWidget, QVBoxLayout
from qtpy.QtGui import QCursor

from cgwidgets.widgets import (
    ShojiModelViewWidget,
    ShojiModelItem,
    ShojiModel,
    ModelViewWidget,
    FloatInputWidget,
    LabelledInputWidget,
    StringInputWidget,
    IntInputWidget,
    BooleanInputWidget,
    ListInputWidget,
    PlainTextInputWidget,
    FrameInputWidgetContainer
)
from cgwidgets.views import AbstractDragDropListView, AbstractDragDropTreeView, AbstractDragDropModelDelegate
from cgwidgets.widgets import ShojiLayout
from cgwidgets.settings import attrs, icons
from cgwidgets.utils import centerWidgetOnCursor

if __name__ == "__main__":
    app = QApplication(sys.argv)


# CREATE MAIN WIDGET
shoji_widget = ShojiModelViewWidget()

# SUBCLASS
class SubclassShojiModelViewWidget(ShojiModelViewWidget):
    def __init__(self, parent=None, direction=attrs.NORTH):
        super(SubclassShojiModelViewWidget, self).__init__(parent, direction=direction)

# SETUP VIEW
"""
Choose between a Tree, List, or Custom view.
By default this will be a LIST_VIEW
"""
def setupCustomView():
    class CustomView(AbstractDragDropListView):
        """
        Can also inherit from
            <AbstractDragDropTreeView>
        """
        def __init__(self):
            super(CustomView, self).__init__()
            pass
    view = CustomView()
    shoji_widget.setHeaderViewWidget(view)

shoji_widget.setHeaderViewType(ModelViewWidget.TREE_VIEW)
# shoji_widget.setHeaderViewType(ModelViewWidget.LIST_VIEW)
# setupCustomView()


# SETUP CUSTOM MODEL
def setupCustomModel():
    class CustomModel(ShojiModel):
        def __init__(self, parent=None, root_item=None):
            super(CustomModel, self).__init__(parent, root_item=root_item)

    class CustomModelItem(ShojiModelItem):
        def __init__(self, parent=None):
            super(CustomModelItem, self).__init__(parent)

    model = ShojiModel()
    item_type = CustomModelItem
    model.setItemType(item_type)
    shoji_widget.setModel(model)

#setupCustomModel()


# Set column names
"""
note:
    when providing column data, the key in the dict with the 0th
    index is required, and is the text displayed to the user by default
"""
shoji_widget.setHeaderData(['name', 'SINE.', "woowoo"])

# SETUP CUSTOM DELEGATE
# todo: Note this will error when setting column 1, as the column data doesn't exist to be set.
class CustomDelegate(AbstractDragDropModelDelegate):
    """ The delegate for the main view.  This will open/close all of the different views
    that the user can open by double clicking on an item/column.

    Attributes:
        current_item (DragDropModelItem): currently being manipulated"""

    def __init__(self, parent=None):
        super(CustomDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        """ Creates the editor widget.

        This is needed to set a different delegate for different columns"""
        if index.column() == 0:
            item = index.internalPointer()
            return AbstractDragDropModelDelegate.createEditor(self, parent, option, index)

        elif index.column() == 1:
            delegate = QLabel("test delegate", parent)
            return delegate
        pass

    # def paint(self, painter, option, index):
    #     """ Custom paint event to override the existing handler for this style
    #
    #     This is needed as StyleSheets/Data won't mix, and the stylesheet will
    #     automatically overwrite the data() set on the model
    #
    #     https://stackoverflow.com/questions/39995688/set-different-color-to-specifc-items-in-qlistwidget
    #     """
    #     if index.column() == 1:
    #         painter.save()
    #
    #         # draw BG
    #         try:
    #             color = index.internalPointer().getArg("color")[1:-1].split(", ")
    #             color = [int(c) for c in color]
    #         except:
    #             color = iColor["rgba_background_01"]
    #         bg_color = QColor(*color)
    #         painter.setBrush(bg_color)
    #         painter.drawRect(option.rect)
    #
    #         # draw selection border
    #         if option.state & QStyle.State_Selected:
    #             # If the item is selected, always draw background red
    #             color = iColor["rgba_selected"]
    #         else:
    #             color = iColor["rgba_black"]
    #
    #         painter.setPen(QPen(QColor(*color)))
    #         painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
    #         painter.drawLine(option.rect.topLeft(), option.rect.topRight())
    #         painter.drawLine(option.rect.topRight(), option.rect.bottomRight())
    #
    #         # draw text color
    #         int_color = math.fabs(int(128 - bg_color.value()))
    #         text_color = [int_color, int_color, int_color, 255]
    #
    #         painter.setPen(QColor(*text_color))
    #         text = index.data(Qt.DisplayRole)
    #         option.rect.setLeft(option.rect.left()+5)
    #         painter.drawText(option.rect, (Qt.AlignLeft | Qt.AlignVCenter), text)
    #
    #         painter.restore()
    #     else:
    #         super(NodeColorItemDelegate, self).paint(painter, option, index)
    #     return

delegate = CustomDelegate(shoji_widget)
shoji_widget.headerViewWidget().setItemDelegate(delegate)


# CREATE ITEMS / TABS
def setupAsStacked():
    # insert tabs
    shoji_widget.setDelegateType(ShojiModelViewWidget.STACKED)
    shoji_widget.insertShojiWidget(0, column_data={'name': 'hello'},
                                   widget=LabelledInputWidget(name='hello', delegate_widget=FloatInputWidget()))

    ##############################################
    # create overlay input widget
    image_path = icons["path_branch_closed"]

    def frameUserEvent(widget, value):
        print("user input...", widget, value)

    frame_input_widget_container = FrameInputWidgetContainer(title='Frame Input Widgets', direction=Qt.Vertical)

    # set header editable / Display
    frame_input_widget_container.setIsHeaderEditable(True)
    frame_input_widget_container.setIsHeaderShown(True)

    # Add widgets
    label_widgets = {
        "float": FloatInputWidget,
        "int": IntInputWidget,
        "bool": BooleanInputWidget,
        "str": StringInputWidget,
        "list": ListInputWidget,
        "text": PlainTextInputWidget
    }

    for arg in label_widgets:
        # create widget
        widget_type = label_widgets[arg]
        input_widget = LabelledInputWidget(name=arg, delegate_constructor=widget_type)
        input_widget.setDefaultLabelLength(200)
        # set widget orientation
        input_widget.setDirection(Qt.Horizontal)

        # add to group layout
        frame_input_widget_container.addInputWidget(input_widget, finished_editing_function=frameUserEvent)

        # test
        test = QLabel("-")
        # test.setFixedWidth(25)
        # input_widget.mainWidget().setSizes([100,200,25])
        input_widget.mainWidget().addWidget(test)

        # list override
        if arg == "list":
            list_of_crap = [
                ['a', (0, 0, 0, 255)], ['b', (0, 0, 0, 255)], ['c', (0, 0, 0, 255)], ['d', (0, 0, 0, 255)],
                ['e', (0, 0, 0, 255)],
                ['aa', (255, 0, 0, 255)], ['bb', (0, 255, 0, 255)], ['cc', (0, 0, 255, 255)], ['dd'], ['ee'],
                ['aba'], ['bcb'], ['cdc'], ['ded'], ['efe']
            ]
            input_widget.delegateWidget().populate(list_of_crap)
            input_widget.delegateWidget().display_item_colors = True

    shoji_widget.insertShojiWidget(
        0,
        column_data={'name': 'world'},
        widget=frame_input_widget_container,
        display_overlay=True,
        image_path=image_path,
        text_color=(128, 128, 255, 255),
        display_delegate_title=False)

    ##############################################
    # CREATE SHOJI MVW WIDGET
    # shoji model view widget
    shoji_widget2 = ShojiModelViewWidget()
    shoji_widget2.setMultiSelect(True)
    for char in "SINE.":
        shoji_widget2.insertShojiWidget(
            0, column_data={'name': char},
            widget=LabelledInputWidget(name=char, delegate_widget=FloatInputWidget()))
    shoji_widget.insertShojiWidget(0, column_data={'name':'Widget'}, widget=shoji_widget2)

    # shoji layout
    shoji_layout = ShojiLayout()
    for char in 'SINE.':
        shoji_layout.addWidget(StringInputWidget(char))

    shoji_delegate_item = shoji_widget.insertShojiWidget(0, column_data={'name': 'Layout'}, widget=shoji_layout)

    # insert child tabs
    # insert child widgets
    for y in range(0, 2):
        widget = StringInputWidget(str("SINE."))
        shoji_widget.insertShojiWidget(y, column_data={'name': str(y), 'one': 'datttaaa'}, widget=widget, parent=shoji_delegate_item)

def setupAsDynamic():
    class DynamicWidgetExample(QWidget):
        """
        Dynamic widget to be used for the ShojiModelViewWidget.  This widget will be shown
        everytime an item is selected in the ShojiModelViewWidget, and the updateGUI function
        will be run, every time an item is selected.

        Simple name of overloaded class to be used as a dynamic widget for
        the ShojiModelViewWidget.
        """

        def __init__(self, parent=None):
            super(DynamicWidgetExample, self).__init__(parent)
            QVBoxLayout(self)
            self.label = QLabel('init')
            self.layout().addWidget(self.label)

        @staticmethod
        def updateGUI(parent, widget, item):
            """
            parent (ShojiModelViewWidget)
            widget (ShojiModelDelegateWidget)
            item (ShojiModelItem)
            self --> widget.getMainWidget()
            """
            print ("=================== UPDATE GUI =================")
            print("---- DYNAMIC WIDGET ----")
            print(parent, widget, item)

            name = parent.model().getItemName(item)
            widget.setTitle(name)
            widget.getMainWidget().label.setText(name)

    class DynamicItemExample(StringInputWidget):
        """
        Custom widget which has overloaded functions/widget to be
        displayed in the Shoji
        """
        def __init__(self, parent=None):
            super(DynamicItemExample, self).__init__(parent)

        @staticmethod
        def updateGUI(parent, widget, item):
            """
            parent (ShojiModelViewWidget)
            widget (ShojiModelDelegateWidget)
            item (ShojiModelItem)
            self --> widget.getMainWidget()
            """
            print("---- DYNAMIC ITEM ----")
            print(parent, widget, item)
            this = widget.getMainWidget()
            this.setText('whatup')

    # set all items to use this widget
    shoji_widget.setDelegateType(
        ShojiModelViewWidget.DYNAMIC,
        dynamic_widget=DynamicWidgetExample,
        dynamic_function=DynamicWidgetExample.updateGUI
    )

    # create items
    for x in range(3):
        name = 'title {}'.format(str(x))
        shoji_widget.insertShojiWidget(x, column_data={'name': name})

    # insert child tabs
    # insert child widgets
    parent_item = shoji_widget.insertShojiWidget(0, column_data={'name': "PARENT"})
    for y in range(0, 2):
        shoji_widget.insertShojiWidget(y, column_data={'name': str(y), 'one': 'datttaaa'}, parent=parent_item)

    # custom item
    custom_index = shoji_widget.insertShojiWidget(0, column_data={'name': 'Custom Item Widget'})
    custom_index.internalPointer().setDynamicWidgetBaseClass(DynamicItemExample)
    custom_index.internalPointer().setDynamicUpdateFunction(DynamicItemExample.updateGUI)

def setupAsDoubleDynamic():
    class DynamicWidgetExample(QWidget):
        """
        Dynamic widget to be used for the ShojiModelViewWidget.  This widget will be shown
        everytime an item is selected in the ShojiModelViewWidget, and the updateGUI function
        will be run, every time an item is selected.

        Simple name of overloaded class to be used as a dynamic widget for
        the ShojiModelViewWidget.
        """

        def __init__(self, parent=None):
            super(DynamicWidgetExample, self).__init__(parent)
            QVBoxLayout(self)
            self.label = QLabel('init')
            self.layout().addWidget(self.label)

        @staticmethod
        def updateGUI(parent, widget, item):
            """
            parent (ShojiModelViewWidget)
            widget (ShojiModelDelegateWidget)
            item (ShojiModelItem)
            self --> widget.getMainWidget()
            """
            if item:
                print("---- DYNAMIC WIDGET ----")
                print(parent, widget, item)
                name = parent.model().getItemName(item)
                widget.setTitle(name)
                widget.getMainWidget().label.setText(name)

    class DynamicItemExample(ShojiModelViewWidget):
        """
        Custom widget which has overloaded functions/widget to be
        displayed in the Shoji
        """
        def __init__(self, parent=None):
            super(DynamicItemExample, self).__init__(parent)

            self.setDelegateType(
                ShojiModelViewWidget.DYNAMIC,
                dynamic_widget=DynamicItemInputWidget,
                dynamic_function=DynamicItemInputWidget.updateGUI
            )
            for x in range(3):
                name = 'title {}'.format(str(x))
                self.insertShojiWidget(x, column_data={'name': name})

            self.setMultiSelect(True)

        @staticmethod
        def updateGUI(parent, widget, item):
            """
            parent (ShojiModelViewWidget)
            widget (ShojiModelDelegateWidget)
            item (ShojiModelItem)
            self --> widget.getMainWidget()
            """
            if item:
                print("---- DOUBLE DYNAMIC WIDGET ----")
                print(parent, widget, item)
                name = parent.model().getItemName(item)
                widget.setTitle(name)
                # widget.getMainWidget().label.setText(name)

    class DynamicItemInputWidget(FloatInputWidget):
        def __init__(self, parent=None):
            super(DynamicItemInputWidget, self).__init__(parent)

        @staticmethod
        def updateGUI(parent, widget, item):
            """
            parent (ShojiModelViewWidget)
            widget (ShojiModelDelegateWidget)
            item (ShojiModelItem)
            self --> widget.getMainWidget()
            """
            print("---- DYNAMIC ITEM ----")
            print(parent, widget, item)
            this = widget.getMainWidget()
            this.setText('whatup')

    # set all items to use this widget
    shoji_widget.setDelegateType(
        ShojiModelViewWidget.DYNAMIC,
        dynamic_widget=DynamicWidgetExample,
        dynamic_function=DynamicWidgetExample.updateGUI
    )

    # create items
    for x in range(3):
        name = 'title {}'.format(str(x))
        shoji_widget.insertShojiWidget(x, column_data={'name': name})

    # insert child tabs
    # insert child widgets
    parent_item = shoji_widget.insertShojiWidget(0, column_data={'name': "PARENT"})
    for y in range(0, 2):
        shoji_widget.insertShojiWidget(y, column_data={'name': str(y), 'one': 'datttaaa'}, parent=parent_item)

    # custom item
    custom_index = shoji_widget.insertShojiWidget(0, column_data={'name': 'Custom Item Widget'})
    custom_index.internalPointer().setDynamicWidgetBaseClass(DynamicItemExample)
    custom_index.internalPointer().setDynamicUpdateFunction(DynamicItemExample.updateGUI)


setupAsStacked()
#setupAsDynamic()
#setupAsDoubleDynamic()

# SET FLAGS
#shoji_widget.setMultiSelect(True)

shoji_widget.delegateWidget().setHandleLength(100)
shoji_widget.setHeaderPosition(attrs.WEST, attrs.SOUTH)
shoji_widget.setMultiSelectDirection(Qt.Vertical)
shoji_widget.setDelegateTitleIsShown(True)

#####################################################
# SET EVENT FLAGS
#####################################################
shoji_widget.setHeaderItemIsDroppable(True)
shoji_widget.setHeaderItemIsDraggable(True)
shoji_widget.setHeaderItemIsEditable(True)
shoji_widget.setHeaderItemIsEnableable(True)
shoji_widget.setHeaderItemIsDeletable(True)
#select
#toggle
#####################################################
# Setup Virtual Events
#####################################################
def testDrag(items, model):
    """
    Initialized when the drag has started.  This triggers in the mimeData portion
    of the model.

    Args:
        items (list): of ShojiModelItems
        model (ShojiModel)
    """
    print("---- DRAG EVENT ----")
    print(items, model)

def testDrop(data, items, model, row, parent):
    print("""
DROPPING -->
    data --> {data}
    row --> {row}
    items --> {items}
    model --> {model}
    parent --> {parent}
        """.format(data=data, row=row, model=model, items=items, parent=parent)
          )

def testEdit(item, old_value, new_value, column=None):
    print("---- EDIT EVENT ----")
    print(item, old_value, new_value)
    #updateDelegateDisplay

def testEnable(item, enabled):
    print('---- ENABLE EVENT ----')
    print(item.columnData()['name'], enabled)

def testDelete(item):
    """

    Args:
        item:
    """
    print('---- DELETE EVENT ----')
    print(item.columnData()['name'])

def testDelegateToggle(event, widget, enabled):
    """

    Args:
        event (QEvent.KeyPress):
        widget (QWidget): widget currently being toggled
        enabled (bool):

    Returns:

    """
    print('---- TOGGLE EVENT ----')
    print (event, widget, enabled)

def testSelect(item, enabled):
    """
    Handler that is run when the user selects an item in the view.

    Note that this will run for each column in that row.  So in order
    to have this only register once, have it register to the 0 column
    Args:
        item:
        enabled:
        column:
    """
    #if column == 0:
    print('---- SELECT EVENT ----')
    print(item.columnData(), enabled)


shoji_widget.setHeaderItemEnabledEvent(testEnable)
shoji_widget.setHeaderItemDeleteEvent(testDelete)
shoji_widget.setHeaderDelegateToggleEvent(testDelegateToggle)
shoji_widget.setHeaderItemDragStartEvent(testDrag)
shoji_widget.setHeaderItemDropEvent(testDrop)
shoji_widget.setHeaderItemTextChangedEvent(testEdit)
shoji_widget.setHeaderItemSelectedEvent(testSelect)

# Header Delegates
"""
In the Tree/List view this is a widget that will pop up when
the user presses a specific key/modifier combination
"""
delegate_widget = QLabel("Q")
shoji_widget.addHeaderDelegateWidget([Qt.Key_Q], delegate_widget, modifier=Qt.NoModifier, focus=False)

# add context menu
def contextMenu(index, selected_indexes):
    print(index, selected_indexes)
    print(index.internalPointer())

shoji_widget.addContextMenuEvent('test', contextMenu)


# select index on show
indexes = shoji_widget.model().findItems("hello", Qt.MatchExactly)
for index in indexes:
    shoji_widget.setIndexSelected(index, True)

# get selected indexes
print(shoji_widget.getAllSelectedIndexes())
print(shoji_widget.getAllIndexes())

# shoji_widget.setHeaderItemIsCopyable(True)
# display widget

# single
# shoji_widget.resize(500,500)
# shoji_widget.show()
# centerWidgetOnCursor(shoji_widget)

# double

shoji_layout = ShojiLayout()
shoji_widget3 = ShojiModelViewWidget(direction=attrs.EAST)
shoji_widget.setMultiSelect(True)
shoji_widget3.setMultiSelect(True)

# shoji layout
shoji_layout3 = ShojiLayout()
for char in 'SINE.':
    shoji_layout3.addWidget(StringInputWidget(char))
shoji_widget3.insertShojiWidget(0, column_data={'name': 'Layout'}, widget=shoji_layout3)

# insert child tabs
# insert child widgets
for y in range(0, 2):
    widget = StringInputWidget(str("SINE."))
    shoji_widget3.insertShojiWidget(y, column_data={'name': str(y), 'one': 'datttaaa'}, widget=widget)


shoji_layout.addWidget(shoji_widget)
#shoji_layout.addWidget(shoji_widget3)
shoji_layout.show()
shoji_layout.resize(960, 540)

centerWidgetOnCursor(shoji_layout)
if __name__ == "__main__":
    sys.exit(app.exec_())