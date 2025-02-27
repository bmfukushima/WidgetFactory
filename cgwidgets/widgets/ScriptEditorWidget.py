from cgwidgets.widgets import AbstractScriptEditorWidget, AbstractPythonEditor, AbstractScriptEditorPopupEventFilter

class ScriptEditorWidget(AbstractScriptEditorWidget):
    """ Script Editors main widget

    Attributes:
        currentItem (item):
        filepath (str):
        python_editor (QWidget): to be displayed when editing Python Scripts
        scripts_variable (str): Environment Variable that will hold all of the locations
            that the scripts will be located in"""
    def __init__(self, parent=None, python_editor=AbstractPythonEditor, scripts_variable="CGWscripts"):
        super(ScriptEditorWidget, self).__init__(
            parent=parent, python_editor=python_editor, scripts_variable=scripts_variable)


class ScriptEditorPopupEventFilter(AbstractScriptEditorPopupEventFilter):
    def __init__(self, parent=None, main_window=None, scripts_variable="CGWscripts"):
        super(ScriptEditorPopupEventFilter, self).__init__(parent, main_window=main_window, scripts_variable=scripts_variable)