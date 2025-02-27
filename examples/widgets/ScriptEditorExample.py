
import sys, os
os.environ['QT_API'] = 'pyside2'
from qtpy import API_NAME, PYSIDE_VERSION
from qtpy.QtWidgets import QApplication
from cgwidgets.widgets import ScriptEditorWidget, PopupHotkeyMenu, PopupGestureMenu, GestureDesignPopupWidget
from cgwidgets.utils import centerWidgetOnScreen, getDefaultSavePath, setAsAlwaysOnTop, setAsTransparent
if not QApplication.instance():
    app = QApplication(sys.argv)
else:
    app = QApplication.instance()

print(API_NAME, PYSIDE_VERSION)
os.environ["CGWscripts"] = ";".join([
    getDefaultSavePath() + "/.scripts",
    getDefaultSavePath() + "/.scripts2",
    #"/media/ssd01/dev/katana/KatanaResources_old/ScriptsTest"
])

print(os.environ["CGWscripts"])
# print(os.environ["CGWscripts"])
main_widget = ScriptEditorWidget()
setAsAlwaysOnTop(main_widget)
main_widget.show()
main_widget.resize(960, 540)
centerWidgetOnScreen(main_widget)

# # # popup hotkey example
# hotkey_file_path = "/home/brian/.cgwidgets/.scripts/1377191011911108608.HotkeyDesign.json"
# popup_widget = PopupHotkeyMenu(file_path=hotkey_file_path)
# popup_widget.show()

# popup gesture example
# gesture_file_path = "/home/brian/.cgwidgets/.scripts/7561119950682766336.gestureTest/2258396054567534080.GestureDesign1.json"
# gesture_widget = PopupGestureMenu(file_path=gesture_file_path, display_size=300)
# gesture_widget.show()


sys.exit(app.exec_())
# main()
