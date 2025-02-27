import sys
from qtpy.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSplitter)
from qtpy.QtGui import QCursor
from qtpy.QtCore import Qt

from cgwidgets.settings import iColor

from cgwidgets.widgets import (
    ShojiModelViewWidget,
    ButtonInputWidget,
    FloatInputWidget,
    IntInputWidget,
    StringInputWidget,
    BooleanInputWidget,
    ShojiInputWidgetContainer,
    ListInputWidget,
    LabelledInputWidget,
    FrameInputWidgetContainer,
    OverlayInputWidget,
    PlainTextInputWidget,
    ButtonInputWidgetContainer
)

app = QApplication(sys.argv)

list_of_crap = [
    ['a', (0, 0, 0, 255)], ['b', (0, 0, 0, 255)], ['c', (0, 0, 0, 255)], ['d', (0, 0, 0, 255)], ['e', (0, 0, 0, 255)],
    ['aa', (255, 0, 0, 255)], ['bb', (0, 255, 0, 255)], ['cc', (0, 0, 255, 255)], ['dd'], ['ee'],
    ['aba'], ['bcb'], ['cdc'], ['ded'], ['efe']
]
l2 = [['a', (255, 0, 0, 255)], ['b'], ['c'], ['aa'], ['bb'], ['cc']]

def userEvent(widget, value):
    print("---- user input function ----")
    print('setting value to... ', value)
    print(widget, value)
    #widget.setText(str(value))

""" Shoji Input Widget Container """
shoji_input_widget_container = ShojiInputWidgetContainer(parent=None, name='ShojiInputWidgetContainer')

# add user inputs
shoji_input_widget_container.insertInputWidget(0, BooleanInputWidget, 'Boolean', userEvent)
shoji_input_widget_container.insertInputWidget(0, StringInputWidget, 'String', userEvent)
shoji_input_widget_container.insertInputWidget(0, IntInputWidget, 'Int', userEvent)
shoji_input_widget_container.insertInputWidget(0, FloatInputWidget, 'Float', userEvent)
shoji_input_widget_container.insertInputWidget(0, ListInputWidget, 'List', userEvent, data={'items_list':list_of_crap})
shoji_input_widget_container.insertInputWidget(0, PlainTextInputWidget, 'Text', userEvent)

shoji_input_widget_container.display_background = False


""" BUTTON INPUT WIDGET CONTAINER """
def userEvent(widget):
    print("user input...", widget)

button_input_widget_container = ButtonInputWidgetContainer(orientation=Qt.Vertical)
for flag in range(3):
    if flag == 1:
        button_input_widget_container.addButton("button_" + str(flag), flag, userEvent, True)
    else:
        button_input_widget_container.addButton("button_" + str(flag), flag, userEvent, False)

""" FRAME INPUT WIDGET CONTAINER"""
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
    from qtpy.QtWidgets import QLabel
    test = QLabel("-")
    # test.setFixedWidth(25)
    #input_widget.mainWidget().setSizes([100,200,25])
    input_widget.mainWidget().addWidget(test)

    # list override
    if arg == "list":
        input_widget.delegateWidget().populate(list_of_crap)
        input_widget.delegateWidget().display_item_colors = True


""" Main Widget"""
main_widget = ShojiModelViewWidget()

main_widget.setStyleSheet("""background-color: rgba{rgba_background_00}""".format(**iColor.style_sheet_args))
main_widget.insertShojiWidget(0, column_data={'name':'Shoji Container'}, widget=shoji_input_widget_container)
main_widget.insertShojiWidget(0, column_data={'name':'Button Container'}, widget=button_input_widget_container)
main_widget.insertShojiWidget(0, column_data={'name':'Frame Container'}, widget=frame_input_widget_container)

# from qtpy.QtWidgets import QLabel
# main_widget = QSplitter()
# #main_layout = QVBoxLayout(main_widget)
# main_widget.addWidget(QLabel("test"))
# main_widget.addWidget(shoji_input_widget_container)
main_widget.resize(500, 500)
main_widget.show()
main_widget.move(QCursor.pos())

sys.exit(app.exec_())


