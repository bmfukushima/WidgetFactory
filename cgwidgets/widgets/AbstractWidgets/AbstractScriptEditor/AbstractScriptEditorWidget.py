""" The Script Editor acts a place that can hold all of a users scripts neatly.
This organizes the data into a few different item types,
    Directory:
        Directory for holding scripts
    Group:
        Subdirectory for holding additional scripts, this can be deleted/created
        from the UI.
    Script:
        Python script / executable that can be run from the application
    Hotkey:
        Design widget, this creates a 4x4 hotkey design window.  Users can
        drag/drop Scripts/Designs into this window.  When the window is then
        activated it will create a recursive popup menu that the user can
        either click on, or use hotkeys to get through.
    Gesture:
        Design Widget, this creates a 8x1 design window that forms an octagon with
        the users cursor in the center.  Moving the mouse through an option will
        activate that option.  Note... this doesn"t really work all that well... lol

Hierarchy:
AbstractScriptEditorWidget --> (QSplitter)
  |- ScriptTreeWidget --> (QTreeWidget)
  |  |- ScriptDirectoryItem
  |     |- GroupItem --> (AbstractBaseItem)
  |     |- ScriptItem --> (AbstractBaseItem)
  |     |- HotkeyDesignItem --> (AbstractBaseItem)
  |     |- GestureDesignItem --> (AbstractBaseItem)
  |- design_main_widget --> (QWidget)
     |- QVBoxLayout
        |- AbstractDesignWidget --> (QTabWidget)
        |   |- AbstractPythonEditor --> (QWidget)
        |   |   |-vbox
        |   |      |- code_widget --> (AbstractPythonCodeWidget --> QPlainTextEdit)
        |   |* HotkeyDesignEditorWidget --> (AbstractHotkeyDesignWidget --> QWidget, AbstractDesignWidget)
        |   |* GestureDesignEditorWidget--> (AbstractGestureDesignWidget --> QWidget, AbstractDesignWidget)
        |- SaveButton --> (QPushButton)

Data:
    Hotkeys (hotkeys.json):
        {"/path/on/disk/to/file": "QKeySequence().toString()",
        "/home/user/test.json": "Ctrl+Shift+F"}
    Hotkey (design):
        {
            "1" : "filepath", "2": "filepath"...
            "q" : "filepath", ... "r" : "filepath"}
            ...
            "z" "filepath", ... "v" : "filepath"}
        }
    Gesture (design)
        {"1-7" : "filepath"}

    Settings (settings.json):
        {
            setting_name:value,
            locked:bool,
            display_name, str
        }
"""
"""
Todo:
    *   Update StyleSheets
            - QSplitter needs full stylesheet module update...
                entire stylesheet module could use an overhaul
            - QTabWidget
                can be moved to stylesheet module when completed
    *   Bug
            Pressing ESC while the delegate is activated will close the delegate, without
            resetting the active flag... for some reason I can't figure out where this is =/
    *   Dissalow from dropping on itself?
    *   Hotkeys
            - Hotkeys are stored as 
                "hotkey"
                "item name"
            instead of just the hotkey... search for getHotkey
            -Hotkeys are going wonky
                - When there is more than one directory with overlapping hotkeys, it
                    seems to fail.
                - Need to find all, and send a different flag notification...
                - How to handle locked overwrites?  Disallow?
    * Popup Widgets
        - Add forward/backwards menu options

WISH LIST
    - Add support for modifiers on HotkeyDesigns
    
    - Multi Gesture...
        Always reset display to center of the screen
            - Will this work on tablets?W
"""

import os
import math
import shutil
import json
from qtpy import API_NAME

from qtpy.QtWidgets import (
    QHeaderView,
    QVBoxLayout,
    QLabel,
    QWidget,
    QSplitter,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QItemDelegate,
    QTabWidget,
    QPlainTextEdit,
    QMenu

)
""" QVariants don't exist in PySide2, so will need to not import"""
try:
    from qtpy.QtCore import QVariant, Qt
except ImportError:
    from qtpy.QtCore import Qt
from qtpy.QtGui import QCursor, QKeySequence

from cgwidgets.utils import getWidgetAncestor, showWarningDialogue, getJSONData, replaceLast
from cgwidgets.widgets.AbstractWidgets.AbstractBaseInputWidgets import AbstractLabelWidget, AbstractButtonInputWidget
from cgwidgets.settings import iColor, stylesheets

from .AbstractScriptEditorUtils import Utils as Locals
from .AbstractScriptEditorWidgets import (HotkeyDesignEditorWidget, GestureDesignEditorWidget)


class AbstractPythonCodeWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super(AbstractPythonCodeWidget, self).__init__(parent)

        self.setStyleSheet("""
        background-color: rgba{rgba_background_00};
        color: rgba{rgba_text};
        """.format(**iColor.style_sheet_args))

    def getScript(self):
        return self.toPlainText()

    def setScript(self, script):
        self.setPlainText(script)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Return:
                exec(compile(self.toPlainText(), "script", "exec"))
        return QPlainTextEdit.keyPressEvent(self, event)


class AbstractPythonEditor(QWidget):
    """ Default Python editor widget

    For each DCC this will need to be subclassed.  Where the codeWidget()
    will need to return access to the QPlainTextEdit, or w/e widget holds
    the user input portion of the editor"""
    def __init__(self, parent=None, python_ide=AbstractPythonCodeWidget):
        super(AbstractPythonEditor, self).__init__(parent)

        layout = QVBoxLayout(self)
        self._code_widget = python_ide(self)
        self._save_button = SaveButton(parent=self)

        layout.addWidget(self._code_widget)
        layout.addWidget(self._save_button)

        self.layout().setStretch(0, 1)
        self.layout().setStretch(1, 0)

    def saveButton(self):
        return self._save_button

    def codeWidget(self):
        return self._code_widget


class AbstractScriptEditorWidget(QSplitter):
    """ Script Editors main widget

    Attributes:
        currentItem (item):
        filepath (str):
        python_editor (QWidget): to be displayed when editing Python Scripts
        scripts_variable (str): Environment Variable that will hold all of the locations
            that the scripts will be located in"""
    def __init__(self, parent=None, python_editor=AbstractPythonEditor, scripts_variable="CGWscripts"):
        super(AbstractScriptEditorWidget, self).__init__(parent)
        self._scripts_variable = scripts_variable

        # create all directories
        for scripts_directory in self.scriptsDirectories():
            AbstractScriptEditorWidget.createScriptDirectories(scripts_directory)

        # create main gui
        self.__setupGUI(python_editor)

        style_sheet = """
        QSplitter{{
            background-color:rgba{RGBA_BACKGROUND};
        }}
        QSplitter::handle{{
            border: 2px dotted rgba{RGBA_HANDLE};
            /*background-color: rgba{RGBA_HANDLE};*/
            margin: 2px;
        }}
        QSplitter::handle:hover{{
            border: 2px dotted rgba{RGBA_HANDLE_HOVER};
        }}""".format(
            RGBA_BACKGROUND=iColor["rgba_background_00"],
            RGBA_HANDLE=iColor["rgba_outline"],
            RGBA_HANDLE_HOVER=iColor["rgba_selected_hover_2"]
        )
        self.setStyleSheet(style_sheet)

    # @staticmethod
    # def updateAllDesignFiles(filepath, old_path, new_path):
    #     """ Recursively searches"""
    #     for file in os.listdir(filepath):
    #         full_path = f"{filepath}/{file}"
    #         if os.path.isdir(full_path):
    #             AbstractScriptEditorWidget.updateAllDesigns(full_path, old_path, new_path)
    #         elif full_path.endswith(".json"):
    #             with open(full_path, "r") as current_file:
    #                 data = json.load(current_file)
    #                 for key in data.keys():
    #                     if data[key]:
    #                         if old_path in data[key]:
    #                             data[key] = data[key].replace(old_path, new_path)
    #
    #             with open(full_path, "w") as current_file:
    #                 json.dump(data, current_file)

    @staticmethod
    def createScriptDirectories(scripts_directory, locked=False, display_name=None):
        """ Creates all of the directories for the script directories if they don"t exist

        Args:
            locked (bool): if the directory is locked or not
            display_name (str): Name to display to the user
            scripts_directory (str): path on disk"""
        if not os.path.exists(scripts_directory):
            os.mkdir(scripts_directory)
        for item in ["hotkeys", "settings"]:
            if not os.path.exists(scripts_directory + "/{item}.json".format(item=item)):
                data_dict = {}
                if item == "settings":
                    if not display_name:
                        display_name = os.path.basename(scripts_directory)
                    data_dict = {"locked": locked, "display_name": display_name}
                with open(scripts_directory + "/{item}.json".format(item=item), "w") as f:
                    json.dump(data_dict, f)

    def __setupGUI(self, python_editor):
        """ Sets up the main GUI"""

        # CREATE WIDGETS
        self._script_widget = ScriptTreeWidget(parent=self)
        self._design_tab_widget = DesignTab(parent=self, python_editor=python_editor)

        self._design_main_widget = QWidget()
        design_vbox = QVBoxLayout()
        design_vbox.setContentsMargins(0, 0, 0, 0)
        self._design_main_widget.setLayout(design_vbox)
        design_vbox.addWidget(self._design_tab_widget)

        # ADD WIDGETS TO SPLITTER
        self.addWidget(self._script_widget)
        self.addWidget(self._design_main_widget)

    def __name__(self):
        return "AbstractScriptEditorWidget"

    """ WIDGETS """
    def designMainWidget(self):
        return self._design_main_widget

    def designTabWidget(self):
        return self._design_tab_widget

    def pythonWidget(self):
        return self.designTabWidget().pythonEditorWidget()

    def scriptWidget(self):
        return self._script_widget

    """ PROPERTIES """
    def currentItem(self):
        return self.scriptWidget().currentItem()

    def setCurrentItem(self, item):
        self.scriptWidget().setCurrentItem(item)

    def scriptsVariable(self):
        return self._scripts_variable

    def setScriptsVariable(self, variable):
        self._scripts_variable = variable

    def scriptsDirectories(self):
        return os.environ[self.scriptsVariable()].split(";")

    """ UTILS """
    @staticmethod
    def sortedFiles(file_dir):
        """ Returns a list of the sorted files in the directory provided

        Args:
            file_dir (str): path on disk to return files from"""
        files = os.listdir(file_dir)
        try:
            # python 3.3+
            files.sort(key=lambda x:x.split(".")[1].casefold())
        except AttributeError:
            # python 2.7
            files.sort(key=lambda x:x.split(".")[1].lower())
        return files

    """ EVENTS """
    def resizeEvent(self, event, *args, **kwargs):
        design_tab = self.designTabWidget()
        design_tab.updateAllGestureDesignsGeometry()
        return QSplitter.resizeEvent(self, event, *args, **kwargs)


class SaveButton(AbstractButtonInputWidget):
    """ Save button at the bottom of the Designer portion.

    This is used to save designs/scripts.
    """
    def __init__(self, parent=None):
        super(SaveButton, self).__init__(parent, title="Save")
        self.setUserClickedEvent(self.saveScript)

    def __name__(self):
        return "__save_button__"

    def saveScript(self, widget):
        """Saves the current script to disk"""
        script_editor_widget = getWidgetAncestor(self, AbstractScriptEditorWidget)
        current_item = script_editor_widget.currentItem()
        if current_item.getItemType() == AbstractBaseItem.SCRIPT:
            text = script_editor_widget.designTabWidget().codeWidget().getScript()
            #text = text_block.toPlainText()
            with open(current_item.filepath(), "w") as file:
                file.write(text)


class ScriptTreeWidget(QTreeWidget):
    """ The main hierarchical view which holds the scripts/designs

    This tree widget sits on the left side of GUI and holds the list
    of all of the scripts/designs for the user to adjust

    Attributes:
        accept_input (bool): If this item is currently accepting
            KeyPressEvents to determine the hotkey for this item
        item_dict (dict): all of the items... need to fix this...
            {filepath:item}
    """
    def __init__(self, parent=None):
        super(ScriptTreeWidget, self).__init__(parent)

        # set up attributes
        self._item_dict = {}
        self._accept_input = False

        # setup header
        header_widget = QTreeWidgetItem(["Name", "Type", "Hotkey"])
        self.setHeaderItem(header_widget)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.header().resizeSection(0, 300)

        # connect signals
        self.itemChanged.connect(self.updateItemName)
        item_delegate = DataTypeDelegate(self)
        self.setItemDelegate(item_delegate)

        # Populate Items
        for script_directory in self.scriptDirectories():
            display_name = getJSONData(script_directory + "/settings.json")["display_name"]
            # display_name = os.path.basename(script_directory)
            directory_item = ScriptDirectoryItem(
                self,
                text=display_name,
                file_dir=script_directory,

            )
            # Populate Items from Directories
            self.populateDirectory(script_directory, directory_item, script_directory)

        # set flags
        self.setAlternatingRowColors(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        root_item = self.invisibleRootItem()
        root_item.setFlags(root_item.flags() & ~ Qt.ItemIsDropEnabled)

        """ STYLE SHEETS"""
        style_sheet = """
        QTreeView{{
            background-color: rgba{RGBA_BACKGROUND_00};
            alternate-background-color: rgba{RGBA_BACKGROUND_01};
            color: rgba{RGBA_TEXT}
        }}
        QTreeView::item:hover {{
            color: rgba{RGBA_HOVER_TEXT};
        }}
        {SCROLL_BAR_SS}
        """.format(
            RGBA_TEXT=iColor["rgba_text"],
            RGBA_BACKGROUND_00=iColor["rgba_background_00"],
            RGBA_BACKGROUND_01=iColor["rgba_background_01"],
            RGBA_HOVER_TEXT=iColor["rgba_text_hover"],
            SCROLL_BAR_SS=stylesheets.scroll_bar_ss
        )

        header_style_sheet = """
            background-color: rgba{RGBA_BACKGROUND};
            color: rgba{RGBA_TEXT}""".format(
            RGBA_TEXT=iColor["rgba_text"],
            RGBA_BACKGROUND=iColor["rgba_background_00"])

        self.setStyleSheet(style_sheet)
        self.header().setStyleSheet(header_style_sheet)

    def __name__(self):
        return "__script_list__"

    def populateDirectory(self, file_dir, parent_item, orig_dir):
        """ Populates all of the items in the directory provided.

        Args:
            file_dir (str): directory to be populated
            parent_item (AbstractBaseItem): to be parented under
            orig_dir (str): original directory...
                lazy af hack
        """

        for file in AbstractScriptEditorWidget.sortedFiles(file_dir):
            file_path = "{filedir}/{file}".format(filedir=file_dir, file=file)
            # if file_path.startswith("../"):
            #     print(file_path)
            #     file_path = file_path.replace("..", file_dir)
            #     print(file_path)
            # else:
            #     file_path = orig_file_path
            if "." in file:
                if file not in ["hotkeys.json", "settings.json"]:
                    # create directory item
                    if os.path.isdir(file_path):
                        unique_hash, text = file.replace(".py", "").split(".")
                        item = GroupItem(
                            parent_item,
                            text=text,
                            unique_hash=unique_hash,
                            file_dir=file_dir
                        )
                        self.itemDict()[file_path] = item
                        self.populateDirectory(file_path, item, orig_dir)

                    # create design/script item
                    elif os.path.isfile(file_path):
                        if ".pyc" in file:
                            item = None
                        else:
                            file_type = Locals().checkFileType(file_path)
                            # create new item

                            if file_type == AbstractBaseItem.HOTKEY:
                                unique_hash, text = file.replace(".json", "").split(".")
                                item = HotkeyDesignItem(
                                    parent_item,
                                    text=text.replace(".json", ""),
                                    unique_hash=unique_hash,
                                    file_dir=file_dir
                                )

                            elif file_type == AbstractBaseItem.GESTURE:
                                unique_hash, text = file.replace(".json", "").split(".")
                                item = GestureDesignItem(
                                    parent_item,
                                    text=text.replace(".json", ""),
                                    unique_hash=unique_hash,
                                    file_dir=file_dir
                                )

                            elif file_type == AbstractBaseItem.SCRIPT:
                                unique_hash, text = file.replace(".py", "").split(".")
                                item = ScriptItem(
                                    parent_item,
                                    text=text.replace(".py", ""),
                                    unique_hash=unique_hash,
                                    file_dir=file_dir
                                )

                            if item:
                                self.itemDict()[file_path] = item
                            else:
                                print(file_path, "is not valid")

                    # setup item metadata (locked/hotkeys/alignment/etc)
                    if item:
                        # set display hotkey
                        hotkey_dict = getJSONData(orig_dir + "/hotkeys.json")
                        is_locked = self.getSetting("locked", item)
                        if hotkey_dict:
                            # Check here for relative paths
                            keys = [file.replace("..", orig_dir) for file in list(hotkey_dict.keys())]
                            if file_path in keys:
                                try:
                                    item.setText(2, hotkey_dict[file_path])
                                except KeyError:
                                    file_path = file_path.replace(orig_dir, "..")
                                    item.setText(2, hotkey_dict[file_path])
                        if is_locked:
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                        # setup item alignment
                        item.setTextAlignment(1, Qt.AlignCenter)
                        item.setTextAlignment(2, Qt.AlignCenter)

    """ ITEMS """
    def createNewItem(self, current_parent, item_type=None):
        """Creates a new item under the current parent

        Args:
            current_parent (AbstractBaseItem):
            item_type (AbstractBaseItem.TYPE)
        """
        file_dir = current_parent.getFileDir()
        if isinstance(current_parent, GroupItem):
            file_dir = current_parent.filepath()
        if item_type != AbstractBaseItem.GROUP:
            if item_type == AbstractBaseItem.SCRIPT:
                item = ScriptItem(current_parent, file_dir=file_dir)
            elif item_type == AbstractBaseItem.HOTKEY:
                item = HotkeyDesignItem(current_parent, file_dir=file_dir)
            elif item_type == AbstractBaseItem.GESTURE:
                item = GestureDesignItem(current_parent, file_dir=file_dir)
            self.itemDict()[str(item.filepath())] = item
        elif item_type == AbstractBaseItem.GROUP:
            item = GroupItem(current_parent, text="Group", file_dir=file_dir)

        item.setTextAlignment(1, Qt.AlignCenter)
        item.setTextAlignment(2, Qt.AlignCenter)

    def getAllScriptDirectoryItems(self):
        """ Gets all of the script directory items

        Returns (list): of ScriptDirectoryItem"""
        script_directories = []
        for index in range(self.invisibleRootItem().childCount()):
            script_directories.append(self.invisibleRootItem().child(index))

        return script_directories

    def getAllChildren(self, item, child_list=[]):
        """ Get all children/grandchildren of specified item

        # todo make this less garbage recursion lol

        Args:
            item (item): to search from
            child_list (list): list of items to be returned """
        if item.childCount() > 0:
            for index in range(item.childCount()):
                child = item.child(index)
                if child not in child_list:
                    child_list.append(child)
                self.getAllChildren(child, child_list=child_list)
        else:
            if item not in child_list:
                child_list.append(item)

        return child_list

    def getScriptDirectoryItem(self, item):
        """ Gets the ScriptDirectoryItem from the item provided

        This is the items top level item (right below the invisible root)

        Return (ScriptDirectoryItem)"""
        if item:
            if isinstance(item, ScriptDirectoryItem):
                return item
            # not ScriptDirectory, recurse up
            else:
                return self.getScriptDirectoryItem(item.parent())
        # no item found
        else:
            return None

    """ PROPERTIES """
    def itemDict(self):
        return self._item_dict

    def acceptInput(self):
        return self._accept_input

    def setAcceptInput(self, enabled):
        self._accept_input = enabled

    def scriptsVariable(self):
        return getWidgetAncestor(self, AbstractScriptEditorWidget).scriptsVariable()

    def scriptDirectories(self):
        return getWidgetAncestor(self, AbstractScriptEditorWidget).scriptsDirectories()

    """ UPDATE """
    def moveFile(self, old_file_path, new_file_path):
        shutil.move(str(old_file_path), str(new_file_path))

    def updateItemDictDir(self, old_path, new_path):
        """ Updates the current internal itemDict()

        This will replace all instances of the old path with the new path provided.

        Args:
            new_path (str):
            old_path (str):
        """
        for key in list(self.itemDict().keys()):
            if old_path in key:
                new_key = key.replace(old_path, new_path)
                self.itemDict()[new_key] = self.itemDict().pop(key)

    def updateItemFileDir(self, old_file_dir, new_file_dir, current_item):
        """ Updates an items directories.

        This occurs after an item has been drag/dropped under a new group in the hierarchy

        Args:
            current_item (ScriptItem | GroupItem | DesignItem):
            new_file_dir (str): path on disk to NEW directory
            old_file_dir (str): path on disk to OLD directory
        """
        # get attrs
        new_file_path = current_item.filepath().replace(old_file_dir, new_file_dir)
        old_file_path = current_item.filepath()

        # update item
        current_item.setFilepath(new_file_path)
        current_item.setFileDir(new_file_dir)

        # update design files
        self.updateAllDesignPaths(old_file_path, new_file_path)
        self.updateAllButtons(old_file_path)

        # update meta data
        self.updateItemDictDir(old_file_path, new_file_path)

    def updateAllItemsFileDir(self, old_file_dir, new_file_dir, current_item):
        """ Recursively updates all of the descendants file directories

        When a group name is changed, this function changes the file paths
        of all of the children/grand children recursively

        Args:
            current_item (ScriptItem | GroupItem | DesignItem): Item to start updating
                the file paths from.
            new_file_dir (str): path on disk to NEW directory
            old_file_dir (str): path on disk to OLD directory
        """
        for index in range(current_item.childCount()):
            child = current_item.child(index)
            self.updateItemFileDir(old_file_dir, new_file_dir, child)
            if isinstance(child, GroupItem):
                if current_item.childCount() > 0:
                    self.updateAllItemsFileDir(old_file_dir, new_file_dir, child)

    def updateGroupItemFilepath(self, old_file_dir=None, new_file_dir=None, current_item=None):
        """ Updates the filepath of a GroupItem and all of its descendants.

        Args:
            current_item (GroupItem): selected GroupItem
            new_file_dir (str): path on disk to the NEW directory
            old_file_dir (str:) path on disk to the OLD directory
        """
        if not current_item:
            current_item = self.currentItem()
        # compile attrs
        old_file_name = current_item.getFileName()
        old_file_path = current_item.filepath()

        if not old_file_dir:
            old_file_dir = current_item.getFileDir()

        if not new_file_dir:
            new_file_dir = current_item.parent().getFileDir()
            new_file_name = "{hash}.{name}".format(hash=current_item.getHash(), name=current_item.text(0))
            #new_file_path = old_file_path.replace(old_file_name, new_file_name)
            new_file_path = replaceLast(old_file_path, old_file_name, new_file_name)
        else:
            new_file_name = current_item.getFileName()
            #new_file_path = old_file_path.replace(old_file_dir, new_file_dir)
            new_file_path = replaceLast(old_file_path, old_file_dir, new_file_dir)

        # rename file
        if not os.path.exists(new_file_path):
            os.rename(old_file_path, new_file_path)

        # update all items
        """ Note: updateAllItemsFileDir updates the internal itemDict"""
        #self.updateAllDesignPaths(old_file_path, new_file_path)
        self.updateAllDesignPaths(old_file_dir, new_file_dir)
        self.updateAllItemsFileDir(old_file_path, new_file_path, current_item)
        self.updateAllButtons(old_file_path)
        self.updateHotkeyFile(old_file_path, new_file_path)

        # update item attrs
        current_item.setFilepath(new_file_path)
        current_item.setFileName(new_file_name)
        current_item.setFileDir(new_file_dir)

        # update design tab paths
        script_editor_widget = getWidgetAncestor(self, AbstractScriptEditorWidget)
        script_editor_widget.designTabWidget().updateTabFilePath(old_file_path, new_file_path)

    def updateItemFilepath(self, current_item):
        # get attrs
        file_extension = current_item.getFileName().split(".")[-1]
        unique_hash = current_item.getHash()

        new_name = current_item.text(0)
        new_file_name = "%s.%s.%s" % (unique_hash, new_name, file_extension)

        new_file_path = "%s/%s" % (current_item.getFileDir(), new_file_name)
        old_file_path = current_item.filepath()

        # update item filename/path
        current_item.setFileName(new_file_name)
        current_item.setFilepath(new_file_path)

        # rename file
        if not os.path.exists(new_file_path):
            os.rename(old_file_path, new_file_path)

        # update active design items names
        if isinstance(current_item, (HotkeyDesignItem, GestureDesignItem)):
            script_editor_widget = getWidgetAncestor(self, AbstractScriptEditorWidget)
            design_tab = script_editor_widget.designTabWidget()
            tab_bar = design_tab.tabBar()
            for index in range(tab_bar.count()):
                widget = design_tab.widget(index)
                if hasattr(widget, "getItem"):
                    if widget.getItem().getHash() == current_item.getHash():
                        design_tab.setTabText(index, current_item.text(0))
                        widget.setFilepath(new_file_path)

        # update active buttons
        if isinstance(current_item, (ScriptItem, HotkeyDesignItem, GestureDesignItem)):
            self.updateAllButtons(old_file_path)

        # update item dict data
        self.updateItemDictDir(old_file_path, new_file_path)
        self.updateAllDesignPaths(old_file_path, new_file_path)
        self.updateHotkeyFile(old_file_path, new_file_path)
        return

    def updateItemName(self):
        """ Renames an item, and updates all of the metadata associated with it.

        This is triggered when a user renames an item, and triggers all updates
        associated with a rename
            update design paths
            update active buttons.
        """

        # preflight
        if isinstance(self.currentItem(), ScriptDirectoryItem): return
        if not self.currentItem(): return

        # check to see if it is a name change
        old_name = self.currentItem().getFileName()
        old_name = old_name.split(".")[1]
        new_name = self.currentItem().text(0)
        if old_name == new_name: return

        # update items
        if isinstance(self.currentItem(), GroupItem):
            self.updateGroupItemFilepath()
        elif isinstance(self.currentItem(), (ScriptItem, GestureDesignItem, HotkeyDesignItem)):
            self.updateItemFilepath(self.currentItem())

    def updateHotkeyFile(self, old_dir, new_dir):
        """ Updates the current hotkey master file

        Args:
            old_dir (str):
            new_dir (str):
        """

        hotkey_dict = self.hotkeyDict()
        if hotkey_dict:
            for key in list(hotkey_dict.keys()):
                new_key = key.replace(old_dir, new_dir)
                hotkey_dict[new_key] = hotkey_dict.pop(key)

            with open(self.hotkeyFile(), "w") as current_file:
                json.dump(hotkey_dict, current_file)

    def updateAllDesignPaths(self, old_dir, new_dir):
        """ Updates all of the design files in all of the script directories

        Args:
            new_dir (str):  New Path to add and replace old path with
            old_dir (str):  Old path to look for/remove """
        script_editor_widget = getWidgetAncestor(self, AbstractScriptEditorWidget)
        for start_dir in script_editor_widget.scriptsDirectories():
            self.__updateAllDesignPaths(old_dir, new_dir, start_dir)

    def __updateAllDesignPaths(self, old_dir, new_dir, start_dir):
        """ updates all of the design files in the directory specified

        Args:
            start_dir (str): Directory to search and replace from
            new_dir (str):  New Path to add and replace old path with
            old_dir (str):  Old path to look for/remove
        """
        old_dir = str(old_dir)
        new_dir = str(new_dir)

        for file in os.listdir(start_dir):
            file_path = start_dir + "/" + file
            if os.path.isdir(file_path):
                self.__updateAllDesignPaths(old_dir, new_dir, file_path)

            elif os.path.isfile(file_path):
                update_list = [AbstractBaseItem.HOTKEY, AbstractBaseItem.GESTURE]
                if Locals().checkFileType(file_path) in update_list:
                    with open(file_path, "r") as current_file:
                        design_data = json.load(current_file)

                    for key, value in design_data.items():
                        if old_dir in value:
                            new_value = value.replace(old_dir, new_dir)
                            design_data[key] = new_value

                    with open(file_path, "w") as current_file:
                        json.dump(design_data, current_file)

    def updateAllButtons(self, old_file_path, delete=False):
        """Updates the display of all of the buttons in  the Design Tab

        Args:
            old_file_path (str):
            delete (bool): Determines if this is a delete operation
        """
        script_editor_widget = getWidgetAncestor(self, AbstractScriptEditorWidget)
        design_tab = script_editor_widget.designTabWidget()
        design_tab.updateAllHotkeyDesigns(old_file_path, delete=delete)

    """ SETTINGS """
    def settingsFile(self, item=None):
        """ Gets the current items setting files

        Returns (str): path on disk"""
        if not item:
            item = self.currentItem()
        directory_item = self.getScriptDirectoryItem(item)
        return directory_item.getFileDir() + "/settings.json"

    def settingsDict(self, item=None):
        """ Returns all of the data from the settings file"""
        if not item:
            item = self.currentItem()

        directory_item = self.getScriptDirectoryItem(item)
        if directory_item:
            file_path = self.settingsFile(item)
            return getJSONData(file_path)

    def getSetting(self, setting, item=None):
        """ Returns the settings value from the item provided

        Args:
            setting (str): name of setting to query
                locked | display_name
        Returns"""
        if not item:
            item = self.currentItem()
        settings_data = self.settingsDict(item)
        return settings_data[setting]

    def isItemLocked(self, item):
        if item:
            return self.getSetting("locked", item)
        return None

    """ HOTKEYS """
    def addHotkeyToItem(self, item=None, hotkey=None):
        """ Adds a a hotkey to a SCRIPT | DESIGN item

        The global hotkey"s registry is located at the top of each Scripts directory
        as the file "hotkeys.json"

        Args:
            item (ScriptItem | DesignItem): item to have hotkey added to it
            hotkey (str): hotkey to set
                QKeySequence().toString()
        """

        if not item:
            item = self.currentItem()

        hotkey_filepath = self.hotkeyFile()
        hotkey_dict = getJSONData(hotkey_filepath)
        hotkey_dict[item.filepath()] = hotkey
        with open(hotkey_filepath, "w") as f:
            json.dump(hotkey_dict, f)

    def removeHotkeyFromItem(self, item=None):
        """ Removes the item"s hotkey from the global registry

        # todo not sure if this needs item_path...
        should be able to get it from the item provided

        Args:
            item (AbstractBaseItem): item whose hotkey should be removed
                DesignItem | ScriptItem
        """
        if not item:
            item = self.currentItem()

        item.setText(2, "")
        item_path = item.filepath()
        # delete from global file
        hotkeys_filepath = self.hotkeyFile()
        hotkey_dict = getJSONData(hotkeys_filepath)
        if hotkey_dict:
            relative_path = item_path.replace(os.path.dirname(hotkeys_filepath), "..")
            if relative_path in list(hotkey_dict.keys()) or item_path in list(hotkey_dict.keys()):
                try:
                    hotkey_dict.pop(item_path)
                except KeyError:
                    hotkey_dict.pop(relative_path)

                with open(hotkeys_filepath, "w") as f:
                    json.dump(hotkey_dict, f)

    def hotkeyFile(self, item=None):
        """ Returns the path on disk to the current items hotkey.json file

        Returns (str): path on disk"""
        if not item:
            item = self.currentItem()
        directory_item = self.getScriptDirectoryItem(item)
        return directory_item.getFileDir() + "/hotkeys.json"

    def hotkeyDict(self, item=None):
        """ Returns the hotkey dict from the ScriptDirectoryItem for the item provided

        If no item is provided, this will use the currentItem()

        Returns (dict): """
        if not item:
            item = self.currentItem()

        directory_item = self.getScriptDirectoryItem(item)
        if directory_item:
            file_path = self.hotkeyFile(item)
            return getJSONData(file_path)

    def invertedHotkeyDict(self, item=None):
        """ This should then be used to get the file_path for a hotkey from the hotkey registered

        Instead of returning
            {<filepath>:<hotkey>}
        This will return
            {<hotkey>:<filepath>}

        Args:
            item (ScriptItem | DesignItem): item to get hotkey dict from
        """
        if not item:
            item = self.currentItem()

        inverted_hotkey_dict = {}
        hotkey_dict = self.hotkeyDict(item=item)
        if hotkey_dict:
            for file_path in list(hotkey_dict.keys()):
                hotkey = hotkey_dict[file_path]
                inverted_hotkey_dict[hotkey] = file_path
        return inverted_hotkey_dict

    def checkHotkeyExistence(self, hotkey, item=None):
        """ Checks to see if this hotkey already exists

        Args:
            hotkey (str): of QKeySequence
                QtGui.QKeySequence().toString
        """
        if not item:
            item = self.currentItem()

        hotkeys_dict = self.invertedHotkeyDict(item=item)
        if hotkey in list(hotkeys_dict.keys()):
            return True
        else:
            return False

    """ UTILS """
    def loadScript(self):
        """ Loads the script of the current item"""
        script_editor_widget = getWidgetAncestor(self, AbstractScriptEditorWidget)
        current_item = self.currentItem()
        code_tab = script_editor_widget.designTabWidget().codeWidget()
        file_path = current_item.filepath()
        with open(file_path, "r") as current_file:
            text_list = current_file.readlines()
            text = "".join(text_list)
            code_tab.setScript(text)
        script_editor_widget.setCurrentItem(current_item)

    def showTab(self, current_item):
        """sets the tab widget to the current item to be display"""
        script_editor_widget = getWidgetAncestor(self, AbstractScriptEditorWidget)
        design_tab = script_editor_widget.designTabWidget()
        tab_bar = design_tab.tabBar()

        # Hotkey
        if isinstance(current_item, (HotkeyDesignItem, GestureDesignItem)):
            # create/show tab if it exists/doesnt
            for index in range(tab_bar.count()):
                widget = design_tab.widget(index)
                if hasattr(widget, "getItem"):
                    if widget.getItem().getHash() == current_item.getHash():
                        design_tab.setCurrentWidget(widget)
                        return

            if isinstance(current_item, HotkeyDesignItem):
                design_widget = HotkeyDesignEditorWidget(
                    parent=design_tab,
                    item=current_item,
                    file_path=current_item.filepath()
                )

            if isinstance(current_item, GestureDesignItem):
                size = design_tab.getGestureWidgetSize()
                design_widget = GestureDesignEditorWidget(
                    parent=design_tab,
                    item=current_item,
                    file_path=current_item.filepath(),
                    script_list=self,
                    size=size
                )

            # add tab
            tab_name = current_item.text(0)
            tab = design_tab.addTab(design_widget, tab_name)

            # update design widget meta data
            directory_display_name = self.getSetting("display_name", current_item)
            display_name = "{directory_name}/{tab_name}".format(
                directory_name=directory_display_name, tab_name=tab_name)
            design_tab.setTabToolTip(tab, display_name)
            design_widget.setHash(current_item.getHash())
            design_tab.setCurrentWidget(design_widget)

        # Script
        elif isinstance(current_item, ScriptItem):
            self.loadScript()
            widget = design_tab.widget(0)
            design_tab.setCurrentWidget(widget)

    def deleteItem(self, item):
        if item:
            if isinstance(item, GroupItem):
                # has to recursively delete all children?
                # remove hotkeys from children
                # get all children...
                children = self.getAllChildren(item, child_list=[])

                # run through hotkey removal
                for child in children:
                    if isinstance(child, (ScriptItem, GestureDesignItem, HotkeyDesignItem)):
                        self.removeHotkeyFromItem(child)

                # del item
                shutil.rmtree(item.filepath())
                index = item.parent().indexOfChild(item)
                item.parent().takeChild(index)


                # for index in range(item.childCount()):
                #     child = item.child(index)
                #     self.deleteItem(child)

            else:
                script_editor_widget = getWidgetAncestor(self, AbstractScriptEditorWidget)
                file_path = item.filepath()

                # delete disk location
                if os.path.exists(file_path):
                    os.remove(file_path)

                # del tab
                design_tab_widget = script_editor_widget.designTabWidget()
                tab_bar = design_tab_widget.tabBar()
                for index in range(tab_bar.count()):
                    widget = design_tab_widget.widget(index)
                    if (
                            isinstance(widget, HotkeyDesignEditorWidget)
                            or isinstance(widget, GestureDesignEditorWidget)
                    ):
                        if item.getHash() == widget.getHash():
                            design_tab_widget.removeTab(index)

                # needs to update all buttons again?
                self.updateAllButtons(item.filepath(), delete=True)
                self.updateAllDesignPaths(file_path, "")

                # del item
                index = item.parent().indexOfChild(item)
                item.parent().takeChild(index)

                # del key
                del self.itemDict()[str(item.filepath())]

    def closeDelegateEditor(self):
        """ Closes the delegate editor and resets all the flags """
        self.closePersistentEditor(self.currentItem(), 2)
        self.setAcceptInput(False)
        main_window = self.parent().window()
        if hasattr(main_window, "_script_editor_event_filter_widget"):
            event_filter_widget = main_window._script_editor_event_filter_widget
            event_filter_widget.setIsActive(True)

    """ EVENTS """
    def contextMenuEvent(self, event, *args, **kwargs):
        # block if locked
        if self.isItemLocked(self.currentItem()): return

        def actionPicker(action):
            # get parent item
            current_parent = self.currentItem()
            if isinstance(current_parent, (HotkeyDesignItem, GestureDesignItem, ScriptItem)):
                current_parent = self.currentItem().parent()

            if action.text() == "Create Hotkey Design":
                self.createNewItem(current_parent, item_type=AbstractBaseItem.HOTKEY)
            elif action.text() == "Create Gesture Design":
                self.createNewItem(current_parent, item_type=AbstractBaseItem.GESTURE)
            elif action.text() == "Create Script":
                self.createNewItem(current_parent, AbstractBaseItem.SCRIPT)
            elif action.text() == "Create Group":
                self.createNewItem(current_parent, AbstractBaseItem.GROUP)
            elif action.text() == "Get File Path":
                print(self.currentItem().filepath())
        pos = event.globalPos()
        menu = QMenu(self)
        menu.addAction("Create Hotkey Design")
        menu.addAction("Create Gesture Design")
        menu.addAction("Create Script")
        menu.addAction("Create Group")
        menu.addAction("Get File Path")
        menu.popup(pos)
        action = menu.exec_(QCursor.pos())
        if action is not None:
            actionPicker(action)
        return QTreeWidget.contextMenuEvent(self, event, *args, **kwargs)

    def dragEnterEvent(self, *args, **kwargs):
        """ set up flags for drag/drop so that an item cannot be moved out of its top most item"""
        # block if locked
        if self.isItemLocked(self.currentItem()): return

        # enable drop into this directory
        current_script_directory = self.getScriptDirectoryItem(self.currentItem())
        # disable drop into other directories
        for script_directory_item in self.getAllScriptDirectoryItems():
            # disable drop into other directories
            children = self.getAllChildren(script_directory_item, child_list=[])
            if script_directory_item != current_script_directory:
                script_directory_item.setFlags(script_directory_item.flags() & ~Qt.ItemIsDropEnabled)
                for child in children:
                    child.setFlags(child.flags() & ~Qt.ItemIsDropEnabled)

            # enable drop into this directory
            if script_directory_item == current_script_directory:
                script_directory_item.setFlags(script_directory_item.flags() | Qt.ItemIsDropEnabled)
                for child in children:
                    if isinstance(child, GroupItem):
                        child.setFlags(child.flags() | Qt.ItemIsDropEnabled)

        return QTreeWidget.dragEnterEvent(self, *args, **kwargs)

    def dropEvent(self, event, *args, **kwargs):
        """ when an item is dropped, its directory is updated along with all
        meta data relating to tabs/buttons/designs
        get attributes"""
        current_item = self.currentItem()
        old_parent = current_item.parent()

        return_val = super(ScriptTreeWidget, self).dropEvent(event, *args, **kwargs)

        # reselect item after resolve
        self.setCurrentItem(current_item)

        new_parent = current_item.parent()
        item_name = current_item.getFileName()

        old_file_dir = old_parent.filepath()
        if isinstance(old_parent, ScriptDirectoryItem):
            old_file_dir = old_parent.getFileDir()
        old_file_path = old_file_dir + "/" + item_name

        new_file_dir = new_parent.filepath()
        if isinstance(new_parent, ScriptDirectoryItem):
            new_file_dir = new_parent.getFileDir()
        new_file_path = new_file_dir + "/" + item_name

        # move file
        shutil.move(str(old_file_path), str(new_file_path))

        # update
        if isinstance(current_item, GroupItem):
            self.updateGroupItemFilepath(old_file_dir, new_file_dir)

            self.updateHotkeyFile(old_file_dir, new_file_dir)

        elif isinstance(current_item, (ScriptItem, GestureDesignItem, HotkeyDesignItem)):
            self.updateItemFileDir(old_file_dir, new_file_dir, current_item)
            script_editor_widget = getWidgetAncestor(self, AbstractScriptEditorWidget)
            script_editor_widget.designTabWidget().updateTabFilePath(old_file_path, new_file_path)

            self.updateHotkeyFile(old_file_path, new_file_path)
        return return_val

    def mouseReleaseEvent(self, event, *args, **kwargs):
        """on lmb change the design viewed tab/create a new tab"""
        current_item = self.itemAt(event.pos())
        if current_item:
            index = self.currentIndex()
            if self.isItemLocked(current_item): return

            if event.button() == Qt.LeftButton:
                if index.column() != 2:
                    # display tab
                    self.setCurrentItem(current_item)
                    self.showTab(current_item)

            elif event.button() == Qt.MiddleButton:
                # drag / drop
                pass

        return QTreeWidget.mouseReleaseEvent(self, event,  *args, **kwargs)

    def keyPressEvent(self, event, *args, **kwargs):
        # block if locked
        if self.isItemLocked(self.currentItem()): return

        if self.acceptInput() is True:
            if event.text() != "":
                # escape pressed out of delegate editor
                if event.key() == Qt.Key_Escape:
                    self.setAcceptInput(False)
                    main_window = self.parent().window()
                    if hasattr(main_window, "_script_editor_event_filter_widget"):
                        event_filter_widget = main_window._script_editor_event_filter_widget
                        event_filter_widget.setIsActive(True)
                    return QTreeWidget.keyPressEvent(self, event, *args, **kwargs)

                # reset hotkey if user presses backspace/delete
                if event.key() in [Qt.Key_Backspace, Qt.Key_Delete]:
                    self.removeHotkeyFromItem()
                    self.closeDelegateEditor()
                    return QTreeWidget.keyPressEvent(self, event, *args, **kwargs)

                # get key sequence
                hotkey = QKeySequence(int(event.modifiers()) + event.key()).toString()

                # check existence of hotkey, and append the keypath to the hotkeys JSON file
                hotkey_exists = self.checkHotkeyExistence(hotkey)

                if hotkey_exists is True:
                    def acceptOverwriteHotkey(widget):
                        # remove old hotkey
                        # if this fails, then the hotkey.jsons meta data is out of sync
                        old_hotkey_item = self.findItems(hotkey, Qt.MatchRecursive | Qt.MatchExactly, column=2)[0]
                        self.removeHotkeyFromItem(item=old_hotkey_item)

                        # add new hotkey
                        self.currentItem().setText(2, hotkey)
                        self.addHotkeyToItem(item=self.currentItem(), hotkey=hotkey)

                        self.closeDelegateEditor()

                    def cancelOverwriteHotkey(widget):
                        self.currentItem().setText(2, "")
                        self.removeHotkeyFromItem()
                        self.closeDelegateEditor()

                    display_widget = AbstractLabelWidget(text="""
The hotkey \"{hotkey}\" exists.
Would you like to override it and continue?""".format(hotkey=hotkey))
                    showWarningDialogue(self, display_widget, acceptOverwriteHotkey, cancelOverwriteHotkey)
                else:
                    self.closeDelegateEditor()

                    self.currentItem().setText(2, hotkey)
                    self.addHotkeyToItem(item=self.currentItem(), hotkey=hotkey)

                    # disable script running on hotkey press
                    main_window = self.parent().window()
                    if hasattr(main_window, "_script_editor_event_filter_widget"):
                        main_window._script_editor_event_filter_widget.setIsSettingHotkey(True)
                    # # while editing, update the delegates text
                    # try:
                    #     self.itemDelegate().delegateWidget().setText(hotkey)
                    # except RuntimeError:
                    #
                    #     pass

                # need to return here to avoid the QTreeWidget from auto selecting the previous hotkeyed item
                return

        # Delete Item
        else:
            if event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
                if isinstance(self.currentItem(), ScriptDirectoryItem): return
                def deleteItem(widget):
                    item = self.currentItem()
                    self.removeHotkeyFromItem()
                    self.deleteItem(item)
                    # if isinstance(item, GroupItem):
                    #     shutil.rmtree(item.filepath())
                    #     index = item.parent().indexOfChild(item)
                    #     item.parent().takeChild(index)

                def cancel(widget):
                    pass

                display_widget = AbstractLabelWidget(text="Are ya sure matey!?!?? (said like a pirate)")
                showWarningDialogue(self, display_widget, deleteItem, cancel)

        return QTreeWidget.keyPressEvent(self, event, *args, **kwargs)


class DesignTab(QTabWidget):
    """Tab on right where the user does most of the editing

    Args:
        python_editor (QWidget): which should be used as the Python Editor
            note that this will need to have its "codeWidget" overwritten to
            return a QPlainTextEditWidget
        """
    def __init__(self, parent=None, python_editor=AbstractPythonEditor):
        super(DesignTab, self).__init__(parent)
        self.setAcceptDrops(True)

        self._python_editor_widget = python_editor()
        self.addTab(self._python_editor_widget, "Python")

        style_sheet = """
        QTabWidget{{
            border: None;
            color: rgba{RGBA_TEXT};
            background-color: rgba{RGBA_BACKGROUND}
        }}
        QTabBar::tab{{
            border: 2px solid rgba{RGBA_OUTLINE};
            border-bottom-color: rgba{RGBA_BACKGROUND};
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            padding: 5px;
            margin-top: 6px;
            color: rgba{RGBA_TEXT};
            background-color: rgba{RGBA_BACKGROUND}
        }}
        QTabBar::tab::hover{{
            color: rgba{RGBA_TEXT_HOVER};
            background-color: rgba{RGBA_BACKGROUND}
        }}
        QTabBar::tab::!selected{{
            margin-top: 15px;
            margin-left: -1px;
            margin-right: -1px;
        }}
        QTabBar::tab::selected{{
            color: rgba{RGBA_TEXT_SELECT};
            background-color: rgba{RGBA_BACKGROUND}
        }}
        """.format(
            RGBA_TEXT=iColor["rgba_text"],
            RGBA_TEXT_HOVER=iColor["rgba_text_hover"],
            RGBA_TEXT_SELECT=iColor["rgba_text_hover"],
            RGBA_OUTLINE=iColor["rgba_outline"],
            RGBA_BACKGROUND=iColor["rgba_background_00"]
        )
        self.setStyleSheet(style_sheet)

        self.setMinimumWidth(1)

    def __name__(self):
        return "__main_tab__"

    def setPythonEditor(self, editor_widget):
        self._python_editor_widget = editor_widget

    def codeWidget(self):
        return self.pythonEditorWidget().codeWidget()

    def pythonEditorWidget(self):
        return self._python_editor_widget

    """ UTILS """
    def updateTabFilePath(self, old_file_path, new_file_path):
        """

        Args:
            new_file_path (str): after the file path has been changed, this is
                the path to the new one on disk.  Right now this is being used with
                "def groupRename".
            old_file_path (str)
        """
        design_tab = self
        tab_bar = design_tab.tabBar()
        for index in range(tab_bar.count()):
            widget = design_tab.widget(index)
            if hasattr(widget, "file_path"):
                if old_file_path in widget.filepath():
                    file_path = widget.filepath().replace(old_file_path, new_file_path)
                    widget.setFilepath(file_path)

    """ HOTKEYS """
    def updateAllHotkeyDesigns(self, old_file_path, delete=False):
        """ Updates all of the Hotkey/Gesture design buttons

        Args:
            old_file_path (str):
            delete (bool): Determines if this is a delete operation"""
        tab_bar = self.tabBar()
        for index in range(tab_bar.count()):
            widget = self.widget(index)
            if isinstance(widget, (HotkeyDesignEditorWidget, GestureDesignEditorWidget)):
                widget.updateButtons(old_file_path, delete=delete)

    """ GESTURES """
    def getGestureWidgetSize(self):
        """Gets the height of the Gesture Widget, with offsets from child widgets"""
        size = min(self.width(), self.height() - self.tabBar().height())

        return size

    def updateAllGestureDesignsGeometry(self):
        design_tab = self
        tab_bar = design_tab.tabBar()
        for index in range(tab_bar.count()):
            widget = design_tab.widget(index)
            if isinstance(widget, GestureDesignEditorWidget):
                size = self.getGestureWidgetSize()
                widget.updatePolygons(size=size)

    """ EVENTS """
    def mousePressEvent(self, event, *args, **kwargs):
        if event.button() == Qt.MiddleButton:
            tab_bar = self.tabBar()
            current_tab = tab_bar.tabAt(event.pos())
            if current_tab > 0:
                self.removeTab(tab_bar.tabAt(event.pos()))

        return QTabWidget.mousePressEvent(self, event, *args, **kwargs)

    def resizeEvent(self, event, *args, **kwargs):
        self.updateAllGestureDesignsGeometry()
        return QTabWidget.resizeEvent(self, event, *args, **kwargs)


""" ITEMS """
class DataTypeDelegate(QItemDelegate):
    """ Item delegate for the TreeWidget which holds all of the scripts/designs"""
    def __init__(self, parent=None):
        super(DataTypeDelegate, self).__init__(parent)
        self._delegate_widget = None

    def delegateWidget(self):
        return self._delegate_widget

    """ Do I need this"""
    def sizeHint(self, *args, **kwargs):
        return QItemDelegate.sizeHint(self, *args, **kwargs)

    """ Do I need this"""
    def updateEditorGeometry(self, *args, **kwargs):
        return QItemDelegate.updateEditorGeometry(self, *args, **kwargs)

    def createEditor(self, parent, option, index):
        if index.column() == 2:
            current_item = self.parent().currentItem()
            if current_item.getItemType() != AbstractBaseItem.GROUP:
                self.parent().setAcceptInput(True)

                self._delegate_widget = QLabel(parent)
                self._delegate_widget.setAlignment(Qt.AlignCenter)
                # todo update bg color
                self._delegate_widget.setStyleSheet("""
                    background-color: rgba{RGBA_BACKGROUND};
                    border: 2px solid rgba{RGBA_SELECTED};
                    color: rgba{TEXT_COLOR}""".format(
                    TEXT_COLOR=iColor["rgba_text"],
                    RGBA_BACKGROUND=iColor["rgba_background_00"],
                    RGBA_SELECTED=iColor["rgba_selected"])
                )
                self._delegate_widget.setText(current_item.text(2))
                # disable hotkey events
                main_window = self.parent().window()
                if hasattr(main_window, "_script_editor_event_filter_widget"):
                    event_filter_widget = main_window._script_editor_event_filter_widget
                    event_filter_widget.setIsActive(False)
                return self._delegate_widget

        elif index.column() == 1:
            return
        else:
            return QItemDelegate.createEditor(self, parent, option, index)

    def setModelData(self, editor, model, index):
        """ swap out "v" for current value"""
        # reactivate events
        main_window = self.parent().window()
        if hasattr(main_window, "_script_editor_event_filter_widget"):
            event_filter_widget = main_window._script_editor_event_filter_widget
            event_filter_widget.setIsActive(True)

        # get data
        self.parent().setAcceptInput(False)
        new_value = editor.text()
        if new_value == "":
            return

        if API_NAME == "PySide2":
            model.setData(index, str(new_value))
        else:
            model.setData(index, QVariant(new_value))

        return QItemDelegate.setModelData(self, editor, model, index)


class AbstractBaseItem(QTreeWidgetItem):
    """ Abstract item for all of the items in the ScriptTreeWidget

    Attributes:
        file_dir (str): directory file is in
        file_path (str): full path on disk
        file_name (str): name of file
    """
    DIRECTORY = "directory"
    GROUP = "group"
    SCRIPT = "script"
    HOTKEY = "hotkey"
    GESTURE = "gesture"
    MASTER = "master"

    def __init__(self, parent=None, text="", unique_hash=None):
        super(AbstractBaseItem, self).__init__(parent)

    def initialize(
        self,
        parent=None,
        text="Base Item",
        unique_hash=None,
        file_dir=None
    ):
        """
        initialize the default attributes for each item
        @parent: <AbstractBaseItem>
        @text: <str> display name
        @unique_hash: <str> unique hash
        @file_dir: <str> directory of file
        """
        def getFileName(unique_hash, text):
            # todo will this break on gesture/group?
            file_name = "%s.%s" % (unique_hash, text)
            if self.getItemType() == AbstractBaseItem.SCRIPT:
                file_name += ".py"
            elif self.getItemType() == AbstractBaseItem.HOTKEY:
                file_name += ".json"
            return file_name

        # set meta data
        self.setFileDir(file_dir)

        # check hash
        if not unique_hash:
            unique_hash = self.createHash(text, self.getFileDir())
            file_name = getFileName(unique_hash, text)
            self.setFileName(file_name)
            self.setFilepath(self.getFileDir() + "/" + self.getFileName())
            # why am I creating a dir here? for everything?
            self.createData(self.filepath())
        # set up item meta data
        file_name = getFileName(unique_hash, text)
        self.setFileName(file_name)
        self.setFilepath(self.getFileDir() + "/" + self.getFileName())
        self.setHash(unique_hash)

        # set display text
        self.setText(0, str(text))

        # create bits (file / directory)

    """  PROPERTIES """

    def getItemType(self):
        return self.item_type

    def setItemType(self, item_type):
        self.setText(1, item_type)
        self.item_type = item_type

    def getFileName(self):
        return self.file_name

    def setFileName(self, file_name):
        self.file_name = file_name

    def getFileDir(self):
        return self.file_dir

    def setFileDir(self, file_dir):
        self.file_dir = file_dir

    def getHashList(self, location, hash_list=[]):
        """ Returns a list of all of the uniques hashes in the directory"""
        for child in os.listdir(location):
            child_location = "%s/%s" % (location, child)
            if "." in child:
                unique_hash = child.split(".")[0]
                hash_list.append(unique_hash)

            if os.path.isdir(child_location):
                self.getHashList(child_location, hash_list=hash_list)
        return list(set(hash_list))

    def createHash(self, thash, location):
        thash = int(math.fabs(hash(str(thash))))
        if str(thash) in self.getHashList(location):
            thash = int(math.fabs(hash(str(thash))))
            return self.createHash(str(thash), location)
        return thash

    def setHash(self, unique_hash):
        self.hash = unique_hash

    def getHash(self):
        return str(self.hash)

    def setFilepath(self, file_path):
        self._file_path = file_path

    def filepath(self):
        return self._file_path


class AbstractDesignItem(AbstractBaseItem):
    def __init__(
        self,
        parent=None,
        text=AbstractBaseItem.HOTKEY,
        unique_hash=None
    ):
        super(AbstractDesignItem, self).__init__(parent)
        self.setItemType(AbstractBaseItem.HOTKEY)

    def createData(self, file_path):
        """Creates the hotkey design file as a JSON@file_path <str> path to file
        """

        hotkeys = "12345qwertasdfgzxcvb"
        hotkey_dict = {}
        for letter in hotkeys:
            hotkey_dict[letter] = ""
        if file_path:
            # Writing JSON data
            with open(file_path, "w") as f:
                json.dump(hotkey_dict, f)


class ScriptDirectoryItem(AbstractBaseItem):
    def __init__(
        self,
        parent=None,
        text=AbstractBaseItem.GROUP,
        unique_hash=None,
        file_dir=None
    ):
        super(ScriptDirectoryItem, self).__init__(parent)

        self.setFlags(
            self.flags()
            & ~Qt.ItemIsEditable
            & ~Qt.ItemIsDragEnabled
        )

        self.setItemType(AbstractBaseItem.DIRECTORY)

        self.setFileDir(file_dir)
        self.setFilepath(file_dir)
        self.setText(0, text)
        self.setHash(unique_hash)
        self.setItemType(AbstractBaseItem.DIRECTORY)


class GroupItem(AbstractBaseItem):
    def __init__(
        self,
        parent=None,
        text=AbstractBaseItem.GROUP,
        unique_hash=None,
        file_dir=None
    ):
        super(GroupItem, self).__init__(parent)
        self.setFlags(
            self.flags()
            | Qt.ItemIsEditable)

        self.setItemType(AbstractBaseItem.GROUP)

        self.initialize(
            parent=parent,
            text=text,
            unique_hash=unique_hash,
            file_dir=file_dir
        )

    def createData(self, directory):
        if not os.path.exists(directory):
            os.mkdir(directory)


class ScriptItem(AbstractBaseItem):
    def __init__(
            self,
            parent=None,
            text="Script",
            unique_hash=None,
            file_dir=None
    ):

        super(ScriptItem, self).__init__(parent)
        self.setFlags(
            self.flags()
            & ~Qt.ItemIsDropEnabled
            | Qt.ItemIsDragEnabled
            | Qt.ItemIsEditable
        )

        self.setItemType(AbstractBaseItem.SCRIPT)

        self.initialize(
                parent=parent,
                text=text,
                unique_hash=unique_hash,
                file_dir=file_dir
        )

    def createData(self, file_path):
        current_file = open(file_path, "w")
        current_file.write("")
        current_file.close()


class HotkeyDesignItem(AbstractDesignItem):
    def __init__(
        self,
        parent=None,
        text="HotkeyDesign",
        unique_hash=None,
        file_dir=None
    ):
        super(HotkeyDesignItem, self).__init__(parent)
        self.setFlags(
            self.flags()
            & ~Qt.ItemIsDropEnabled
            | Qt.ItemIsDragEnabled
            | Qt.ItemIsEditable
        )

        self.initialize(
            parent=parent,
            text=text,
            unique_hash=unique_hash,
            file_dir=file_dir
        )

        self.setItemType(AbstractBaseItem.HOTKEY)


class GestureDesignItem(AbstractDesignItem):
    def __init__(
        self,
        parent=None,
        text="GestureDesign",
        unique_hash=None,
        file_dir=None
    ):
        super(GestureDesignItem, self).__init__(parent)
        self.setFlags(
            self.flags()
            & ~Qt.ItemIsDropEnabled
            | Qt.ItemIsDragEnabled
            | Qt.ItemIsEditable
        )

        self.initialize(
            parent=parent,
            text=text,
            unique_hash=unique_hash,
            file_dir=file_dir
        )

        self.setItemType(AbstractBaseItem.GESTURE)

    def createData(self, file_path):
        """
        Creates the hotkey design file as a JSON
        @file_path <str> path to file
        """
        hotkeys = "01234567"
        hotkey_dict = {}
        for letter in hotkeys:
            hotkey_dict[letter] = ""
        if file_path:
            # Writing JSON data
            with open(file_path, "w") as f:
                json.dump(hotkey_dict, f)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication
    from cgwidgets.utils import centerWidgetOnScreen, getDefaultSavePath, setAsAlwaysOnTop
    app = QApplication(sys.argv)

    os.environ["CGWscripts"] = ":".join([
        getDefaultSavePath() + "/.scripts",
        getDefaultSavePath() + "/.scripts2",
        #"/media/ssd01/dev/katana/KatanaResources_old/ScriptsTest"
    ])

    main_widget = AbstractScriptEditorWidget()
    setAsAlwaysOnTop(main_widget)
    main_widget.show()
    centerWidgetOnScreen(main_widget)

    sys.exit(app.exec_())
    main()

