# https://doc.qt.io/qt-5/model-view-programming.html#model-view-classes

from collections import OrderedDict

from qtpy.QtWidgets import (QApplication, QWidget)
from qtpy.QtCore import (
    Qt, QModelIndex, QAbstractItemModel, QSortFilterProxyModel,
    QSize, QMimeData, QByteArray)
from qtpy.QtGui import QColor

from cgwidgets.settings import iColor

class AbstractDragDropModelItem(object):
    """

    Attributes:
        delegate_widget (QWidget): Widget to be shown when this item is
            selected
        dynamic_widget_base_class (QWidget): Widget to be shown when this item is
            selected if the Shoji is in DYNAMIC mode.
        column_data (dict): Dictionary of key pair values relating to the column name,
            and the value for the item in that column.  Special column names are
                name
                value
                items_list
    """
    def __init__(self, parent=None):
        #self._data = data
        self._column_data = OrderedDict()
        self._children = []
        self._parent = parent
        self._delegate_widget = None
        self._dynamicWidgetFunction = None

        # flags

        #self._is_selected = False
        self._is_copyable = None
        self._is_deletable = None
        self._delete_on_drop = None
        self._is_draggable = None
        self._is_droppable = None
        self._is_enabled = True
        self._is_enableable = None
        self._is_editable = None
        self._is_expanded = None
        self._is_selectable = None

        # default parent
        if parent is not None:
            parent.addChild(self)

    def addChild(self, child):
        self._children.append(child)

    def insertChild(self, position, child):
        if position < 0 or position > len(self._children):
            return False

        self._children.insert(position, child)
        child._parent = self
        return True

    def removeChild(self, position):
        if position < 0 or position > len(self._children):
            return False

        child = self._children.pop(position)
        child._parent = None

        return True

    def childCount(self):
        return len(self._children)

    def children(self):
        return self._children

    def child(self, row):
        try:
            return self._children[row]
        except:
            return None

    def parent(self):
        return self._parent

    def setParent(self, parent):
        self._parent = parent

    def row(self):
        if self._parent is not None:
            if self in self._parent._children:
                return self._parent._children.index(self)
            else:
                return None

    def log(self, tabLevel=-1):
        output = ""
        tabLevel += 1

        for i in range(tabLevel):
            output += "\t"
        output += "|------" + self._name + "\n"

        for child in self._children:
            output += child.log(tabLevel)

        tabLevel -= 1
        output += "\n"

        return output

    """ ARGS """
    def columnData(self):
        return self._column_data

    def setColumnData(self, _column_data):
        self._column_data = _column_data

    def hasArg(self, arg):
        if arg in self.columnData().keys():
            return True
        return False

    def args(self):
        return self.columnData()

    def setArg(self, arg, value):
        self.columnData()[arg] = value

    def getArg(self, arg):
        try:
            return self.columnData()[arg]
        except KeyError:
            return None

    def getArgsList(self):
        return list(self.columnData().keys())

    def removeArg(self, arg):
        self.columnData().pop(arg, None)

    def clearArgsList(self):
        for key in list(self.columnData().keys()):
            self.columnData().pop(key, None)

    def name(self):
        """ Note: If name is not found, then it will return the first key in the dictionary."""
        try:
            return self.columnData()["name"]
        except KeyError:
            try:
                return self.columnData()[list(self.columnData().keys())[0]]
            except IndexError:
                return None

    def setName(self, name):
        self.columnData()[list(self.columnData().keys())[0]] = name

    """ DRAG / DROP PROPERTIES """
    def deleteOnDrop(self):
        return self._delete_on_drop

    def setDeleteOnDrop(self, _delete_on_drop):
        self._delete_on_drop = _delete_on_drop

    def isCopyable(self):
        return self._is_copyable

    def setIsCopyable(self, is_copyable):
        self._is_copyable = is_copyable

    def isDeletable(self):
        return self._is_deletable

    def setIsDeletable(self, enable):
        self._is_deletable = enable

    def isDraggable(self):
        return self._is_draggable

    def setIsDraggable(self, _is_draggable):
        if _is_draggable is None: self._is_draggable = None
        elif _is_draggable: self._is_draggable = Qt.ItemIsDragEnabled
        elif not _is_draggable: self._is_draggable = 0
        else: self._is_draggable = Qt.ItemIsDragEnabled

    def isDroppable(self):
        return self._is_droppable

    def setIsDroppable(self, _is_droppable):
        if _is_droppable is None: self._is_droppable = None
        elif _is_droppable: self._is_droppable = Qt.ItemIsDropEnabled
        elif not _is_droppable: self._is_droppable = 0
        else: self._is_droppable = Qt.ItemIsDropEnabled

    def isEditable(self):
        return self._is_editable

    def setIsEditable(self, _is_editable):
        if _is_editable is None: self._is_editable = None
        elif _is_editable: self._is_editable = Qt.ItemIsEditable
        elif not _is_editable: self._is_editable = 0
        else: self._is_editable = Qt.ItemIsEditable

    def isEnabled(self):
        return self._is_enabled

    def setIsEnabled(self, enable):
        self._is_enabled = enable

    def isExpanded(self):
        return self._is_expanded

    def setIsExpanded(self, is_expanded):
        self._is_expanded = is_expanded

    def isEnableable(self):
        return self._is_enableable

    def setIsEnableable(self, enable):
        self._is_enableable = enable

    def isSelectable(self):
        return self._is_selectable

    def setIsSelectable(self, _is_selectable):
        if _is_selectable is None: self._is_selectable = None
        elif _is_selectable: self._is_selectable = Qt.ItemIsSelectable
        elif not _is_selectable: self._is_selectable = 0
        else: self._is_selectable = False


class AbstractDragDropFilterProxyModel(QSortFilterProxyModel):
    """ Proxy model designed for use with the abstract drag/drop system

    Note:
        Anything added here needs to have the virtual classes updated...
            AbstractDrag/DropView
            AbstractModelViewWidget
            AbstractShojiModelViewWidget

    Attributes:
        filters (list): of dict's containing regex filters to be used when on this model
            {"filter": QRegExp, "arg": str(arg)}
            arg is arg in the items data to check, please note that this needs to be a string value
    """
    def __init__(self, parent=None):
        super(AbstractDragDropFilterProxyModel, self).__init__(parent)
        self._filters = []
        self.setRecursiveFilteringEnabled(True)

    def addFilter(self, regex_filter, arg="name", name=None):
        """ Add's a new proxy filter

        Args:
            regex_filter (QRegExp):
            arg (str): column data arg to query
            name (str): internal name of this filter
        """
        name = name or regex_filter.pattern() + arg
        new_filter = {"filter": regex_filter, "arg": arg, "name":name}
        self._filters.append(new_filter)

    def clearFilters(self):
        self._filters = []

    def filters(self):
        return self._filters

    def removeFilter(self, regex_filter, arg="name"):
        try:
            self._filters.remove({"filter": regex_filter, "arg": arg})
        except ValueError:
            # Invalid filter
            pass

    def removeFilterByIndex(self, index):
        del self._filters[index]

    def removeFilterByName(self, name):
        for _filter in self._filters:
            if _filter["name"] == name:
                del self._filters[_filter]

    def updateFilterByName(self, pattern, name):
        """ Updates the given filter with the regex provided

        Args:
            pattern (str): regex pattern to be updated
            name (str): name of filter to update
        """
        for _filter in self._filters:
            if _filter["name"] == name:
                _filter["filter"].setPattern(pattern)
                self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        source_index = self.sourceModel().index(source_row, 0, source_parent)
        item = source_index.internalPointer()
        if item:
            for filter in self.filters():
                item_data = item.getArg(filter["arg"])
                match = filter["filter"].indexIn(item_data, 0)
                if match == -1:
                    return False

        return QSortFilterProxyModel.filterAcceptsRow(self, source_row, source_parent)


class AbstractDragDropModel(QAbstractItemModel):
    """
    Abstract model that is used for the Shoji.  This supports lists, and
    trees.
    TODO:
        - multi column support

    Attributes:
        item_type (Item): Data item to be stored on each index.  By default this
            set to the AbstractDragDropModelItem

    Export Data
        Uses the "exportModelToDict()" function to return the entire tree as a dictionary.
            {data : [
                        {"children": [
                            {"children": [], "name": item.getName()},
                            {"children": [], "name": item.getName()}], "name": item.getName()},
                        {"children": [], "name": item.getName()}
                    ]
            }
        Each child/location in the tree will be exported under the following structure
            {"children": [], "name": item.getName()}

        Additional data can be saved to each location by setting the "setItemExportDataFunction()"
        This function will:
            Take one arg, which is a function which should return a dictionary.
            Have the given function return a dictionary, which must include a the keypair
                "children": []
    """
    ITEM_HEIGHT = 35
    ITEM_WIDTH = 100

    def __init__(self, parent=None, root_item=None):
        super(AbstractDragDropModel, self).__init__(parent)
        # set up default item type
        self._item_type = AbstractDragDropModelItem
        self._item_height = AbstractDragDropModel.ITEM_HEIGHT
        self._item_width = AbstractDragDropModel.ITEM_WIDTH
        self._update_first = True

        # set up root item
        if not root_item:
            root_item = AbstractDragDropModelItem()
            root_item.setColumnData({"name":"root"})
        self._root_item = root_item
        self._root_drop_enabled = True

        # setup default attrs
        self._header_data = ['name']

        # flags
        self._is_selectable = Qt.ItemIsSelectable
        self._is_draggable = Qt.ItemIsDragEnabled
        self._is_droppable = Qt.ItemIsDropEnabled
        self._is_editable = Qt.ItemIsEditable
        self._is_enableable = True
        self._is_deletable = True
        self._is_copyable = False

        #
        self._dropping = False
        self._delete_item_on_drop = True
        self._last_selected_item = None

    """ UTILS """
    @staticmethod
    def getUniqueItemName(item):
        """ Finds a unique name for an item

        Note:
            The unique name refers to the string that is stored as the data in the first column

        Args:
            item (AbstractDragDropModelItem): item to find unique name for"""
        child_names = [child.name() for child in item.parent().children()]
        child_names.remove(item.name())
        item_name = item.name()
        while item_name in child_names:
            try:
                suffix = int(item_name[-1])
                suffix += 1
                item_name = item_name[:-1] + str(suffix)
            except ValueError:
                item_name = item_name + "0"
        return item_name

    def setItemEnabled(self, item, enabled):
        item.setIsEnabled(enabled)
        self.itemEnabledEvent(item, enabled)

    def deleteItem(self, item, event_update=False, update_first=True):
        """
        When an item is deleted this function will be called.

        Cancel event...
        If event_update is TRUE, and the itemDeleteEvent returns TRUE
        then this will return, and not delete the item.

        Args:
            item (AbstractDragDropModelItem): Item to be deleted
            event_update (bool): if True the user event will be run
                if the user event returns TRUE then the item will NOT
                be deleted... kinda counter intuitive, but w/e I don't
                feel like rewriting everything
            update_first (bool): determines if the update should be run before
                or after the delete has happened.

        Returns:

        """

        # preflight
        # todo for some reason this causes a regression with selection
        # if not item.row(): return
        try:
            # run deletion event
            if self.updateFirst():
                if event_update:
                    self.itemDeleteEvent(item)

            # get old parents
            old_parent_item = item.parent()
            old_parent_index = self.getParentIndexFromItem(item)

            # remove item
            self.beginRemoveRows(old_parent_index, item.row(), item.row() + 1)
            old_parent_item.children().remove(item)
            self.endRemoveRows()

            if not self.updateFirst():
                if event_update:
                    self.itemDeleteEvent(item)
        except TypeError:
            # for some reason when deleting the last item, or dropping from there it causes an error...
            # this is to suppress the warning.  Because if I don't hear it, its not a problem!
            # LALALALALALALALALALA CAN'T NO PROBLEMS HERE
            pass

    def clearModel(self, event_update=False):
        """
        Clears the entire model
        Args:
            update_event (bool): determines if user event should be
                run on each item during the deletion process.
        """
        for child in reversed(self.rootItem().children()):
            self.deleteItem(child, event_update=event_update)

    def rowCount(self, parent):
        """
        INPUTS: QModelIndex
        OUTPUT: int
        """
        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()

        return parent_item.childCount()

    def columnCount(self, parent):
        """
        INPUTS: QModelIndex
       OUTPUT: int
       """
        return len(self._header_data)

    def isItemCopyable(self, item):
        """ Determines if an item is copyable or not

        Args:
            item (AbstractDragDropModelItem): Item to check"""
        if item.isCopyable():
            return True
        elif self.isCopyable() and (item.isCopyable() or item.isCopyable() is None):
            return True
        return False

    def isItemDroppable(self, item):
        """ Determines if an item is droppable or not

        Args:
            item (AbstractDragDropModelItem): Item to check"""
        if item.isDroppable():
            return True
        elif self.isDroppable() and (item.isDroppable() or item.isDroppable() is None):
            return True

        return False

    def deleteItemOnDrop(self):
        return self._delete_item_on_drop

    def setDeleteItemOnDrop(self, enabled):
        self._delete_item_on_drop = enabled

    def data(self, index, role):
        """
        This is the main display class for the model.  Setting different
        display roles inside of this class will determine how the views
        will handle the model data

        INPUTS: QModelIndex, int
        OUTPUT: QVariant, strings are cast to QString which is a QVariant
        """

        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            for i in range(self.columnCount(item)):
                if index.column() == i:
                    try:
                        return_val = item.columnData()[self.getHeaderData()[i]]
                    except KeyError:
                        return_val = None
                    return return_val

        # change style for disabled items
        if role == Qt.FontRole:
            font = QApplication.font()

            font.setStrikeOut(not item.isEnabled())

            return font

        if role == Qt.ForegroundRole:
            if item.isEnabled():
                color = QColor(*iColor["rgba_text"])
            else:
                color = QColor(*iColor["rgba_text_disabled"])
            return color

        if role == Qt.SizeHintRole:
            return QSize(self.item_width, self.item_height)

    def setData(self, index, value, role=Qt.EditRole):
        """
        INPUTS: QModelIndex, QVariant, int (flag)
        """
        if index.isValid():
            if role == Qt.EditRole:
                item = index.internalPointer()
                arg = self._header_data[index.column()]
                item.columnData()[arg] = value
                return True
        return False

    def headerData(self, column, orientation, role):
        """
        Sets the header data for each column
        INPUTS: int, Qt::Orientation, int
        OUTPUT: QVariant, strings are cast to QString which is a QVariant
        """
        if role == Qt.DisplayRole:
            return self._header_data[column]

    def getHeaderData(self):
        """ Returns a list of the header names

        Note:
            not to be confused with headerData() which is the internal call
            for the model to get the data at the associated header position"""
        return self._header_data

    def setHeaderData(self, _header_data):
        self._header_data = _header_data

    """ INDEX | ITEMS """
    def parent(self, index):
        """
        INPUTS: QModelIndex
        OUTPUT: QModelIndex
        Should return the parent of the item with the given QModelIndex"""
        item = self.getItem(index)
        parent_item = item.parent()

        if parent_item == self._root_item:
            return QModelIndex()

        if parent_item == None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def index(self, row, column, parent):
        """
        Returns the QModelIndex associated with a row/column/parent provided

        Args:
                row (int)
                column (int)
                parent (QModelIndex)

        Returns (QModelIndex)
        """
        parent_item = self.getItem(parent)
        child_item = parent_item.child(row)

        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def getIndexFromItem(self, item):
        """
        Returns a QModelIndex relating to the corresponding item given
        Args:
            item (AbstractDragDropModelItem):

        Returns:

        """
        if item:
            row = item.row()
            if item and row != None:
                index = self.createIndex(row, 0, item)
            else:
                index = QModelIndex()
        else:
            index = QModelIndex()

        return index

    def getItem(self, index):
        """
        Returns the item held by the index provided
        Args:
            index (QModelIndex)
        Returns (AbstractDragDropModelItem)
        """
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self._root_item

    def getItemName(self, item):
        name = item.columnData()[self.getHeaderData()[0]]
        return name

    def isItemDescendantOf(self, item, ancestor):
        """ Determines if an item is a descendant of another item

        Args:
            item (AbstractDragDropModelItem): to look for ancestor
            ancestor (AbstractDragDropModelItem): to see if the item is a descendant of

        Returns (bool)"""
        if item.parent():
            if item.parent() == ancestor:
                return True
            else:
                return self.isItemDescendantOf(item.parent(), ancestor)
        else:
            return False

    """ ITEM SEARCHING """
    # TODO Add get selected items...
    # add this handler into the AbstractShojiModelViewWidget

    def findItems(self, value, index=None, role=Qt.DisplayRole, match_type=Qt.MatchExactly):
        """
        Finds all of the indexes of the value provided that are descendents of the index provided.
        If no index is provided, the default index will be the root.

        Args:
            value (string): to search for
            index (QModelIndex): to search from
            role (Qt.DisplayRole): to search data of
            match_type (Qt.MatchFlags): Flags to match with...
                Qt.MatchExactly | Qt.MatchStartsWith
                https://doc.qt.io/archives/qtjambi-4.5.2_01/com/trolltech/qt/core/Qt.MatchFlag.html
        Returns (list): of QModelIndex

        """
        indexes = []

        # get children to search from
        if index:
            children = index.internalPointer().children()
        else:
            children = self.rootItem().children()

        # get list
        for child in children:
            current_index = self.getIndexFromItem(child)
            indexes += self.match(current_index, role, value, flags=Qt.MatchRecursive | match_type, hits=-1)

        return indexes

    def getAllIndexes(self):
        all_indexes = self.findItems(".*", match_type=Qt.MatchRegExp)
        return list(set(all_indexes))

    def rootItem(self):
        return self._root_item

    def setRootItem(self, root_item):
        self._root_item = root_item

    """ Create index/items"""
    def setItemType(self, item_type):
        self._item_type = item_type

        # update root item
        root_item = item_type()
        root_item.setColumnData({"name":"root"})
        self.setRootItem(root_item)

    def itemType(self):
        return self._item_type

    def createNewItem(self, *args, **kwargs):
        """Creates a new item of the specified type"""
        item_type = self.itemType()
        new_item = item_type(*args, **kwargs)

        return new_item

    def insertNewIndex(
        self,
        row,
        name="None",
        column_data=None,
        parent=QModelIndex(),
        is_editable=None,
        is_selectable=None,
        is_enableable=None,
        is_deletable=None,
        is_draggable=None,
        is_droppable=None):
        """

        Args:
            row (int):
            name (str):
            column_data (dict):
            parent (QModelIndex):

        Returns (QModelIndex):

        """
        self.insertRow(row, parent)

        # setup custom object
        item_type = self.itemType()
        view_item = item_type()

        # create new index
        self.createIndex(row, 1, view_item)

        # get new index/item created
        new_index = self.index(row, 1, parent)
        view_item = new_index.internalPointer()

        # set column data
        if not column_data:
            column_data = {"name":name}
        view_item.setColumnData(column_data)

        # setup flags
        view_item.setIsEditable(is_editable)
        view_item.setIsSelectable(is_selectable)
        view_item.setIsDraggable(is_draggable)
        view_item.setIsDroppable(is_droppable)
        view_item.setIsEnableable(is_enableable)
        view_item.setIsDeletable(is_deletable)

        return new_index

    """ INSERT INDEXES """
    def insertRows(self, position, num_rows, parent=QModelIndex()):
        """
        INPUTS: int, int, QModelIndex
        """
        parent_item = self.getItem(parent)
        self.beginResetModel()
        self.beginInsertRows(parent, position, position + num_rows - 1)

        for row in range(num_rows):
            childCount = parent_item.childCount()
            childNode = self.createNewItem()
            success = parent_item.insertChild(position, childNode)

        self.endInsertRows()
        self.endResetModel()

        return success

    def removeRows(self, position, num_rows, parent=QModelIndex()):
        """INPUTS: int, int, QModelIndex"""
        # pre flight
        if self._dropping is True:
            self._dropping = False
            return True

        # get parent
        parent_item = self.getItem(parent)

        # remove rows
        self.beginRemoveRows(parent, position, position + num_rows - 1)
        for row in range(num_rows):
            success = parent_item.removeChild(position)
        self.endRemoveRows()

        return success

    def setItemParent(self, row, item, parent_index):
        """ Sets the items parent to a new parent"""
        self.beginResetModel()
        new_item = item
        self.deleteItem(item, event_update=False)

        self.beginInsertRows(parent_index, row, row + 1)
        parent_index.internalPointer().insertChild(row, new_item)
        self.endInsertRows()
        self.endResetModel()

    """ PROPERTIES """
    def lastSelectedItem(self):
        return self._last_selected_item

    def setLastSelectedItem(self, _last_selected_item):
        self._last_selected_item = _last_selected_item

    @property
    def item_height(self):
        return self._item_height

    @item_height.setter
    def item_height(self, _item_height):
        self._item_height = _item_height

    @property
    def item_width(self):
        return self._item_width

    @item_width.setter
    def item_width(self, _item_width):
        self._item_width = _item_width

    def updateFirst(self):
        return self._update_first

    def setUpdateFirst(self, update_first):
        self._update_first = update_first

    """ DRAG / DROP PROPERTIES """
    def isSelectable(self):
        return self._is_selectable

    def setIsSelectable(self, _is_selectable):
        if _is_selectable:
            self._is_selectable = Qt.ItemIsSelectable
        else:
            self._is_selectable = 0

    def isCopyable(self):
        return self._is_copyable

    def setIsCopyable(self, _is_copyable):
        self._is_copyable = _is_copyable

    def isDeletable(self):
        return self._is_deletable

    def setIsDeletable(self, _is_deletable):
        self._is_deletable = _is_deletable

    def isDraggable(self):
        return self._is_draggable

    def setIsDraggable(self, _is_draggable):
        if _is_draggable:
            self._is_draggable = Qt.ItemIsDragEnabled
        else:
            self._is_draggable = 0

    def isDroppable(self):
        return self._is_droppable

    def setIsDroppable(self, _is_droppable):
        if _is_droppable:
            self._is_droppable = Qt.ItemIsDropEnabled
        else:
            self._is_droppable = 0

    def isEnableable(self):
        return self._is_enableable

    def setIsEnableable(self, _is_enableable):
        self._is_enableable = _is_enableable

    def isRootDroppable(self):
        return self._root_drop_enabled

    def setIsRootDroppable(self, _root_drop_enabled):
        self._root_drop_enabled = _root_drop_enabled

    def isEditable(self):
        return self._is_editable

    def setIsEditable(self, _is_editable):
        if _is_editable:
            self._is_editable = Qt.ItemIsEditable
        else:
            self._is_editable = 0

    """ DRAG / DROP"""
    def getParentIndexFromItem(self, item):
        """
        Returns the parent index of an item.  This is especially
        useful when doing drag/drop operations

        Args:
            item (item): item whose parent a QModelIndex should be returned for

        Returns (QModelIndex)
        """
        parent_item = item.parent()
        if parent_item == self.rootItem():
            parent_index = QModelIndex()
        elif not parent_item:
            parent_index = QModelIndex()
        else:
            parent_index = self.createIndex(parent_item.row(), 0, parent_item)
        return parent_index

    def supportedDropActions(self):
        return Qt.MoveAction

    def flags(self, index):
        #https://doc.qt.io/qt-5/qt.html#ItemFlag-enum
        item = index.internalPointer()

        if item:
            # determine flag values
            if item.isSelectable() is not None: selectable = item.isSelectable()
            else: selectable = self.isSelectable()

            if item.isDroppable() is not None: drop_enabled = item.isDroppable()
            else: drop_enabled = self.isDroppable()

            if item.isDraggable() is not None:drag_enabled = item.isDraggable()
            else: drag_enabled = self.isDraggable()

            if item.isEditable() is not None: editable = item.isEditable()
            else: editable = self.isEditable()

            return (
                Qt.ItemIsEnabled
                | selectable
                | drag_enabled
                | drop_enabled
                | editable
            )

        # set up drag/drop on root node
        if self.isRootDroppable(): return Qt.ItemIsEnabled | Qt.ItemIsDropEnabled
        else: return Qt.ItemIsEnabled

    def mimeTypes(self):
        return ['application/x-qabstractitemmodeldatalist']

    def mimeData(self, indexes):
        """
        DragStart event

        Args:
            indexes:

        Returns:

        """
        # get indexes

        self.indexes = [index.internalPointer() for index in indexes if index.column() == 0]

        mimedata = QMimeData()
        mimedata.setData('application/x-qabstractitemmodeldatalist', QByteArray())
        mimedata = self.addMimeData(mimedata, self.indexes)

        # run virtual function
        self.dragStartEvent(self.indexes, self)

        # store indexes for recollection in drop event
        #self.indexes = [index.internalPointer() for index in indexes if index.column() == 0]
        return mimedata

    def dropMimeData(self, data, action, row, column, parent):
        # todo move this to beginMoveRows?
        # (QModelIndex, int sourceFirst, int sourceLast, QModelIndex, int destinationChild)
        # beginMoveRows(sourceParent, 2, 4, destinationParent, 2);

        # bypass remove rows
        self.beginResetModel()
        self._dropping = True

        # get parent item
        parent_item = parent.internalPointer()
        if not parent_item:
            parent_item = self.rootItem()

        # iterate through index list
        indexes = self.indexes
        new_items = []

        for item in indexes:
            # get row
            """ drop on item"""
            if row < 0:
                row = 0

            # drop between items
            else:
                # apply offset if dropping below the current location (due to deletion)
                if row > item.row():
                    if self.deleteItemOnDrop() or item.deleteOnDrop():
                        row -= 1
            # move this to beginMoveRows??
            # remove item
            if item.deleteOnDrop():
                self.deleteItem(item, event_update=False)
            elif item.deleteOnDrop() is None and self.deleteItemOnDrop():
                self.deleteItem(item, event_update=False)
            else:
                row += 1

            # duplicate item
            new_item = item
            new_items.append(new_item)

            # insert item
            self.beginInsertRows(parent, row, row + 1)
            parent_item.insertChild(row, new_item)
            self.endInsertRows()

        # run virtual function
        self.dropEvent(data, new_items, self, row, parent_item)
        self.endResetModel()
        return False

    """ EXPORT DATA """
    def setItemExportDataFunction(self, func):
        self.__getItemExportData = func

    def getItemExportData(self, item):
        return self.__getItemExportData(item)

    def __getItemExportData(self, item):
        return {"children": [], "name": item.name()}

    def exportModelToDict(self, item, item_data=None, allow_none_types=False):
        """ Recursive call to generate a dictionary from the entire model.

        # todo does this need the ability to work with none types?
        by default, None types will not be allowed

        Args:
            item (AbstractDragDropModelItem):
            args (list): of strings of arg item arg names to be stored
            item_data (list): of children, each child is returned as a dictionary of
                {"arg_name":<arg_value>, "arg_name2":<arg_value2>}
            """
        if item == self.rootItem():
            item_data = []

        # index = self.getIndexFromItem(item)
        for child in item.children():
            # todo add defualt item states... expanded, enabled, etc
            """ Will probably need to move this to the view"""
            new_data = self.getItemExportData(child)

            # add data if it exists
            if allow_none_types:
                item_data.append(new_data)
            else:
                if new_data:
                    item_data.append(new_data)

            if 0 < child.childCount():
                self.exportModelToDict(child, item_data=new_data["children"])

        return {"data":item_data}

    """ VIRTUAL FUNCTIONS """
    def setAddMimeDataFunction(self, function):
        """ During drag/drop of a header item.  This will add additional mimedata

        Args:
            mimedata (QMimedata):
            indexes (list): of QModelIndexes that are currently selected

        Returns (QMimeData) """
        self._add_mimedata = function

    def addMimeData(self, mimedata, indexes):
        return self._add_mimedata(mimedata, indexes)

    def _add_mimedata(self, mimedata, indexes):
        return mimedata

    def setItemDeleteEvent(self, function, update_first=True):
        self.__itemDeleteEvent = function
        self.setUpdateFirst(update_first)

    def itemDeleteEvent(self, item):
        self.__itemDeleteEvent(item)

    def __itemDeleteEvent(self, item):
        pass

    def setDragStartEvent(self, function):
        self.__startDragEvent = function

    def dragStartEvent(self, items, model):
        self.__startDragEvent(items, model)

    def __startDragEvent(self, items, model):
        pass

    def setDropEvent(self, function):
        self.__dropEvent = function

    def dropEvent(self, data, items, model, row, parent):
        """
        Virtual function that is run after the mime data has been dropped.

        Args:
            items (list): of AbstractDragDropModelItems
            parent (AbstractDragDropModelItem): item that was dropped on
            row (int): row that the item was dropped at
        """
        self.__dropEvent(data, items, model, row, parent)

    def __dropEvent(self, data, items, model, row, parent):
        pass

    def setItemEnabledEvent(self, function):
        self.__itemEnabledEvent = function

    def itemEnabledEvent(self, item, enabled):
        """
        Virtual function is run when an item is enabled/disabled using
        the 'D' key.

        Args:
            item (AbstractDragDropModelItem): item that has been manipulated
            enabled (boolean): whether or not the item was enabled/disabled

        Note:
            This will run through a for each loop and run for every single item in
            the current selection
        """
        self.__itemEnabledEvent(item, enabled)

    def __itemEnabledEvent(self, item, enabled):
        # print(item.columnData()['name'], enabled)
        pass

    def setTextChangedEvent(self, function):
        self.__textChangedEvent = function

    def textChangedEvent(self, item, old_value, new_value, column=0):
        """
        Virtual function that is run after the mime data has been dropped.

        Args:
            item (AbstractDragDropModelItem): item that has been manipulated
            old_value (str):
            new_value (str):
        """
        self.__textChangedEvent(item, old_value, new_value, column=column)

    def __textChangedEvent(self, item, old_value, new_value, column=0):
        pass

    def setItemSelectedEvent(self, function):
        self.__itemSelectedEvent = function

    def itemSelectedEvent(self, item, enabled):
        """
        When an item is selected, this event will run.

        Args:
            item (AbstractDragDropModelItem): item that has been manipulated
            enabled (boolean): whether or not the item was enabled/disabled
            column (int): index of column selected
        Note:
            This will run through a for each loop and run for every single item in
            the current selection
        """

        self.__itemSelectedEvent(item, enabled)

    def __itemSelectedEvent(self, item, enabled):
        pass
