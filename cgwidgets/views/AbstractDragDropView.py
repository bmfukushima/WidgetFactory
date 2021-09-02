from qtpy import API_NAME

from qtpy.QtWidgets import (
    QListView, QAbstractItemView, QTreeView, QApplication,
    QProxyStyle, QStyledItemDelegate, QStyleOptionViewItem, QStyle, QMenu
)
from qtpy.QtCore import Qt, QPoint, QPointF, QRect, QItemSelectionModel, QSortFilterProxyModel
from qtpy.QtGui import QColor, QPen, QBrush, QCursor, QPolygonF, QPainterPath

from cgwidgets.utils import  showWarningDialogue
from cgwidgets.settings import iColor, attrs, icons

""" VIEWS """
class AbstractDragDropAbstractView(object):
    """

    """
    def __init__(self):
        # attrs
        self._context_menu_manifest = {}
        self._delete_warning_widget = None

        # setup style
        self.style = AbstractDragDropIndicator()
        self.setStyle(self.style)
        self.setupCustomDelegate()

        # setup flags
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self._isDropEnabled = False
        self._isDragEnabled = False
        self._isEditable = False
        self._isEnableable = False
        #self._isSelectable = True

        style_sheet_args = iColor.style_sheet_args
        self.createAbstractStyleSheet(style_sheet_args)

    def createAbstractStyleSheet(self, style_sheet_args, header_position=None, outline_width=1):
        """
        Creates a default style sheet to be used on the view.

        Args:
            style_sheet_args (dict): of color values in the form provided in
                cgwidgets.settings.color.iColor
            header_position (attrs.POSITION): What the current position of the header is.
            outline_width (int): the width of the outline shown
        """
        # todo this is a duplicate call to the ShojiModelViewWidget
        # * need to figure out how to auto populate this.. while maintaining customization
        # setup args

        style_sheet_args.update({
            'outline_width': outline_width,
            'type': type(self).__name__
        })
        style_sheet_args.update(icons)

        # header
        base_header_style_sheet = """
                QHeaderView::section {{
                    background-color: rgba{rgba_background_00};
                    color: rgba{rgba_text};
                    border: {outline_width}px solid rgba{rgba_outline};
                }}
                {type}{{
                    border:None;
                    background-color: rgba{rgba_background_00};
                    selection-background-color: rgba{rgba_invisible};
                }}
                    """.format(**style_sheet_args)

        # item style snippets ( so it can be combined later...)
        style_sheet_args['item_snippet'] = """
                    border: {outline_width}px solid rgba{rgba_black};
                    background-color: rgba{rgba_background_00};
                """.format(**style_sheet_args)
        style_sheet_args['item_selected_snippet'] = """
                    border: {outline_width}px solid rgba{rgba_selected};
                    background-color: rgba{rgba_gray_3};
                """.format(**style_sheet_args)

        # create style sheet
        header_style_sheet = self.__class__.createStyleSheet(self, header_position, style_sheet_args)

        # combine style sheets
        style_sheet_args['splitter_style_sheet'] = "{type}{{selection-background-color: rgba(0,0,0,0);}}".format(**style_sheet_args)
        style_sheet_args['header_style_sheet'] = header_style_sheet
        style_sheet_args['base_header_style_sheet'] = base_header_style_sheet

        style_sheet = """
        {base_header_style_sheet}
        {header_style_sheet}
        {type}::item:hover{{
            color: rgba{rgba_text_hover};
            background-color: rgba{rgba_background_01};
        }}
        {splitter_style_sheet}
        """.format(**style_sheet_args)

        self.setStyleSheet(style_sheet)
        return style_sheet_args

    def setupCustomDelegate(self):
        delegate = AbstractDragDropModelDelegate(self)
        self.setItemDelegate(delegate)

    def getIndexUnderCursor(self):
        """
        Returns the QModelIndex underneath the cursor
        https://bugreports.qt.io/browse/QTBUG-72234
        """
        pos = self.viewport().mapFromParent(self.mapFromGlobal(QCursor.pos()))
        index = self.indexAt(pos)
        return index

    def setOrientation(self, orientation):
        """
        Set the orientation/direction of the view.  This will determine
        the flow of the items, from LeftToRight, or TopToBottom, depending
        on the orientation.

        Args:
            orientation (Qt.Orientation): Can either be
                Qt.Horizonal | Qt.Vertical
        """
        if orientation == Qt.Horizontal:
            self.setFlow(QListView.TopToBottom)
            direction = Qt.Vertical
        else:
            self.setFlow(QListView.LeftToRight)
            direction = Qt.Horizontal
        # update drag/drop style
        # todo WARNING: HARDCODED HERE
        try:
            if "ListView" in str(type(self)):
                self.style.setOrientation(direction)
            else:
                self.style.setOrientation(Qt.Vertical)
        except AttributeError:
            # for some reason katana doesnt like this...
            pass

    def setMultiSelect(self, multi_select):
        if multi_select is True:
            self.setSelectionMode(QAbstractItemView.MultiSelection)
        else:
            self.setSelectionMode(QAbstractItemView.SingleSelection)

    """ DRAG / DROP PROPERTIES """
    def setIsDragEnabled(self, enabled):
        self._isDragEnabled = enabled
        self.model().setIsDragEnabled(enabled)

    def setIsDropEnabled(self, enabled):
        self._isDropEnabled = enabled
        self.model().setIsDropEnabled(enabled)

    def setIsRootDropEnabled(self, enabled):
        self._isRootDropEnabled = enabled
        self.model().setIsRootDropEnabled(enabled)

    def setIsEditable(self, enabled):
        self._isEditable = enabled
        self.model().setIsEditable(enabled)

    def setIsEnableable(self, enabled):
        self._isEnableable = enabled
        self.model().setIsEnableable(enabled)

    def setIsDeleteEnabled(self, enabled):
        self._isDeleteEnabled = enabled
        self.model().setIsDeleteEnabled(enabled)

    """ SELECTION """
    def setIndexSelected(self, index, selected):
        """
        Args:
            index (QModelIndex):
            selected (bool):

        Returns:

        """
        if selected:
            self.selectionModel().select(index, QItemSelectionModel.Select)
        else:
            self.selectionModel().select(index, QItemSelectionModel.Deselect)
        return True

    def clearItemSelection(self):
        self.selectionModel().clearSelection()
        # for index in self.selectedIndexes():
        #     self.selectionModel().select(index, QItemSelectionModel.Deselect)

    """ DELETE """
    def deleteWarningWidget(self):
        return self._delete_warning_widget

    def setDeleteWarningWidget(self, widget):
        self._delete_warning_widget = widget

    """ UTILS """
    def recurseFromIndexToRoot(self, index, function, *args, **kwargs):
        """
        Recursively searches up the ancestory doing the function provided to each index

        Args:
            index (QModelIndex):
            function (function): function to be passed to index.  This function takes
                atleast one arg, index
                Args: view, index, *args, **kwargs

        Returns:

        """
        parent_index = index.parent()
        parent_item = parent_index.internalPointer()
        if parent_item:
            function(self, parent_index, *args, **kwargs)
            #self.setExpanded(parent_index, expanded)
            return self.recurseFromIndexToRoot(parent_index, function, *args, **kwargs)
        else:
            return

    """ EVENTS """
    def enterEvent(self, event):
        self.setFocus()
        return QAbstractItemView.enterEvent(self, event)

    def keyPressEvent(self, event):

        # Clear Selection
        if event.key() == Qt.Key_Escape:
            # from qtpy.QtWidgets import qApp
            # if qApp.widgetAt(QCursor.pos()) == self:
            self.clearItemSelection()

        # Delete Item
        if self.model().isDeleteEnabled():
            if event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
                # delete events
                def deleteItems(widget):
                    indexes = self.selectionModel().selectedRows(0)
                    for index in indexes:
                        item = index.internalPointer()
                        self.model().deleteItem(item, event_update=True)

                def dontDeleteItem(widget):
                    return

                # delete item
                if self.deleteWarningWidget():
                    showWarningDialogue(self, self.deleteWarningWidget(), deleteItems, dontDeleteItem)
                else:
                    deleteItems(None)

        # Disable Item
        if self.model().isEnableable():
            if event.key() == Qt.Key_D:
                indexes = self.selectionModel().selectedRows(0)
                for index in indexes:
                    #if index.column() == 0:
                    item = index.internalPointer()
                    enabled = False if item.isEnabled() else True
                    self.model().setItemEnabled(item, enabled)
                self.model().layoutChanged.emit()

        #self.__keyPressEvent(event)

        return QAbstractItemView.keyPressEvent(self, event)

    """ VIRTUAL """
    def __keyPressEvent(self, event):
        return

    def setKeyPressEvent(self, function):
        self.__keyPressEvent = function

    def setExpanded(self, index, bool):
        """ override for list views """
        return QAbstractItemView.keyPressEvent(self, index, bool)

    """ CONTEXT MENU """
    def contextMenuEvent(self, event):
        # populate menu entries
        context_menu = AbstractViewContextMenu(self)
        for entry_name in self.contextMenuManifest():
            context_menu.addAction(entry_name)

        # Show/Execute menu
        pos = event.globalPos()
        context_menu.popup(pos)
        action = context_menu.exec_(pos)

        # get selected items / items under cursor
        index_clicked = context_menu.item
        selected_indexes = self.selectionModel().selectedRows(0)

        # do user defined event
        if action is not None:
            self.contextMenuManifest()[action.text()](index_clicked, selected_indexes)

    def addContextMenuEvent(self, name, event):
        """
        Adds an entry into the RMB popup menu.

        Args:
            name (str): name of function to be displayed
            event (function): takes two args:
                item_under_cursor (item): current item under cursor
                indexes (list): of currently selected QModelIndexes
        """
        self.contextMenuManifest()[name] = event

    def contextMenuManifest(self):
        return self._context_menu_manifest


class AbstractDragDropListView(QListView, AbstractDragDropAbstractView):
    def __init__(self, parent=None):
        super(AbstractDragDropListView, self).__init__(parent)
        if API_NAME == "PySide2":
            AbstractDragDropAbstractView.__init__(self)
        self.setEditTriggers(QAbstractItemView.DoubleClicked)
        self._isDropEnabled = False

    def createStyleSheet(self, header_position, style_sheet_args):
        """
        Args:
            header_position (attrs.POSITION): the current position of the header
            style_sheet_args (dict): current dictionary of stylesheet args
        Returns (dict): style sheet
        """
        if header_position == attrs.NORTH:
            style_sheet = """
            {type}::item{{
                {item_snippet}
                border-right: None;
                border-top: None;
            }}
            {type}::item:selected{{
                {item_selected_snippet}
                border-right: None;
                border-bottom: None;
            }}
            """.format(**style_sheet_args)
        elif header_position == attrs.SOUTH:
            style_sheet = """
            {type}::item{{
                {item_snippet}
                border-right: None;
                border-bottom: None;
            }}
            {type}::item:selected{{
                {item_selected_snippet}
                border-right: None;
                border-top: None;
            }}
            """.format(**style_sheet_args)
        elif header_position == attrs.EAST:
            style_sheet = """
            {type}::item{{
                {item_snippet}
                border-top: None;
                border-right: None;
            }}
            {type}::item:selected{{
                {item_selected_snippet}
                border-top: None;
                border-left: None;
            }}
            """.format(**style_sheet_args)
        elif header_position == attrs.WEST:
            style_sheet = """
            {type}::item{{
                {item_snippet}
                border-top: None;
                border-left: None;
            }}
            {type}::item:selected{{
                {item_selected_snippet}
                border-top: None;
                border-right: None;
            }}
            """.format(**style_sheet_args)
        else:
            style_sheet = """
            {type}::item{{
                {item_snippet}
            }}
            {type}::item:selected{{
                {item_selected_snippet}
            }}
            """.format(**style_sheet_args)

        # add scroll bar
        from cgwidgets.settings.stylesheets import scroll_bar_ss
        style_sheet += scroll_bar_ss

        #
        return style_sheet

    """ STUPID PYSIDE2 INHERITANCE SHIT"""
    def selectionChanged(self, selected, deselected):
        for index in selected.indexes():
            if index.column() == 0:
                item = index.internalPointer()
                self.model().itemSelectedEvent(item, True)
        for index in deselected.indexes():
            if index.column() == 0:
                item = index.internalPointer()
                self.model().itemSelectedEvent(item, False)

    def keyPressEvent(self, event):
        print("=== LIST EVENT")
        # Clear Selection
        if event.key() == Qt.Key_Escape:
            # from qtpy.QtWidgets import qApp
            # if qApp.widgetAt(QCursor.pos()) == self:
            self.clearItemSelection()

        # Delete Item
        if self.model().isDeleteEnabled():
            if event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
                # delete events
                def deleteItems(widget):
                    #indexes = self.selectionModel().selectedRows(0)
                    indexes = self.selectionModel().selectedIndexes()
                    for index in indexes:
                        item = index.internalPointer()
                        self.model().deleteItem(item, event_update=True)

                def dontDeleteItem(widget):
                    return
                # delete item
                if self.deleteWarningWidget():
                    showWarningDialogue(self, self.deleteWarningWidget(), deleteItems, dontDeleteItem)
                else:
                    deleteItems(None)

        # Disable Item
        if self.model().isEnableable():
            if event.key() == Qt.Key_D:
                indexes = self.selectionModel().selectedIndexes()
                for index in indexes:
                    #if index.column() == 0:
                    item = index.internalPointer()
                    enabled = False if item.isEnabled() else True
                    self.model().setItemEnabled(item, enabled)
                self.model().layoutChanged.emit()

        #self.__keyPressEvent(event)

        return QListView.keyPressEvent(self, event)


class AbstractDragDropTreeView(QTreeView, AbstractDragDropAbstractView):
    def __init__(self, parent=None):
        super(AbstractDragDropTreeView, self).__init__(parent)
        if API_NAME == "PySide2":
            AbstractDragDropAbstractView.__init__(self)

    """ """
    def setHeaderData(self, _header_data):
        """
        Sets the header display data.

        Args:
            header_data (list): of strings that will be displayed as the header
                data.  This will also set the number of columns in the view aswell.
        """
        self.model().setHeaderData(_header_data)

    """ Overload """
    def createStyleSheet(self, header_position, style_sheet_args):
        """
        Args:
            header_position (attrs.POSITION): the current position of the header
            style_sheet_args (dict): current dictionary of stylesheet args
        Returns (dict): style sheet
        """
        style_sheet = """
        QHeaderView::section {{
            background-color: rgba{rgba_background_00};
            color: rgba{rgba_text};
            border: {outline_width}px solid rgba{rgba_black};
        }}
        {type}::item{{
            {item_snippet}
        }}
        {type}::item:selected{{
            {item_selected_snippet}
        }}
        {type}::branch:open:has-children {{
            image: url({path_branch_open})
        }}  
        {type}::branch:closed:has-children {{
            image: url({path_branch_closed})
        }}  
            """.format(**style_sheet_args)

        # add scroll bar
        from cgwidgets.settings.stylesheets import scroll_bar_ss
        style_sheet += scroll_bar_ss

        # return
        return style_sheet

    def setFlow(self, _):
        pass

    """ STUPID PYSIDE2 INHERITANCE SHIT"""
    def selectionChanged(self, selected, deselected):
        for index in selected.indexes():
            if index.column() == 0:
                item = index.internalPointer()
                self.model().itemSelectedEvent(item, True)
        for index in deselected.indexes():
            if index.column() == 0:
                item = index.internalPointer()
                self.model().itemSelectedEvent(item, False)

    def keyPressEvent(self, event):
        # Clear Selection
        if event.key() == Qt.Key_Escape:
            # from qtpy.QtWidgets import qApp
            # if qApp.widgetAt(QCursor.pos()) == self:
            self.clearItemSelection()

        # Delete Item
        if self.model().isDeleteEnabled():
            if event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
                # delete events
                def deleteItems(widget):
                    indexes = self.selectionModel().selectedRows(0)
                    for index in indexes:
                        item = index.internalPointer()
                        self.model().deleteItem(item, event_update=True)

                def dontDeleteItem(widget):
                    return

                # delete item
                if self.deleteWarningWidget():
                    showWarningDialogue(self, self.deleteWarningWidget(), deleteItems, dontDeleteItem)
                else:
                    deleteItems(None)

        # Disable Item
        if self.model().isEnableable():
            if event.key() == Qt.Key_D:
                indexes = self.selectionModel().selectedRows(0)
                for index in indexes:
                    #if index.column() == 0:
                    item = index.internalPointer()
                    enabled = False if item.isEnabled() else True
                    self.model().setItemEnabled(item, enabled)
                self.model().layoutChanged.emit()

        #self.__keyPressEvent(event)

        return QTreeView.keyPressEvent(self, event)


class AbstractViewContextMenu(QMenu):
    def __init__(self, parent=None):
        super(AbstractViewContextMenu, self).__init__(parent)
        self.item = None

    def showEvent(self, event):
        self.item = self.parent().getIndexUnderCursor()


""" STYLES """
class AbstractDragDropModelDelegate(QStyledItemDelegate):
    """
    Default item delegate that is used in the custom Drag/Drop model

    Attributes:
        delegate_widget (QWidget): constructor to be displayed when editor is shown
    """
    def __init__(self, parent=None):
        super(AbstractDragDropModelDelegate, self).__init__(parent)
        # importing the default delegate here
        # as it will run into import errors if imported at top most lvl
        from cgwidgets.widgets.AbstractWidgets import AbstractStringInputWidget
        self._delegate_widget = AbstractStringInputWidget
        # from qtpy.QtWidgets import QLineEdit
        # self._delegate_widget = QLineEdit

    def sizeHint(self, *args, **kwargs):
        return QStyledItemDelegate.sizeHint(self, *args, **kwargs)

    def updateEditorGeometry(self, editor, option, index):
        """
        Updates the editor geometry to will up the entire row

        Updates the delegates geometry with the options rect
        for some reason this wont work if you manually do a
        setGeometry(0,0,100,100), but it works when plugging in
        a rect /shrug
        """
        rect = option.rect
        width = self.parent().geometry().width()
        rect.setWidth(width)
        rect.setX(0)
        editor.setGeometry(option.rect)

    def createEditor(self, parent, option, index):
        """

        """
        delegate_widget = self.delegateWidget(parent)
        return delegate_widget

    def setEditorData(self, editor, index):
        # text = index.model().data(index, Qt.DisplayRole)
        # editor.setText(text)
        return QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        '''
        # swap out 'v' for current value
        '''
        # =======================================================================
        # get data
        # =======================================================================
        "setting model data???"
        new_value = editor.text()
        if new_value == '':
            return
        item = index.internalPointer()
        arg = model._header_data[index.column()]
        old_value = item.columnData()[arg]
        new_value = editor.text()

        # set model data
        item.columnData()[arg] = new_value

        # emit text changed event
        model.textChangedEvent(item, old_value, new_value)

        #model.setData(index, QVariant(new_value))
        #model.aov_list[index.row()] = new_value
        '''
        data_type = self.getDataType(index)
        main_table = self.parent()
        old_value = main_table.getCurrentValue()
        value = main_table.evaluateCell(old_value, new_value, data_type=data_type)
        model.setData(index, QtCore.QVariant(value))
        '''

    def setDelegateWidget(self, delegate_widget):
        self._delegate_widget = delegate_widget

    def delegateWidget(self, parent):
        constructor = self._delegate_widget
        widget = constructor(parent)
        return widget

    def paint(self, painter, option, index):
        """
        Overrides the selection highlight color.

        https://www.qtcentre.org/threads/41299-How-to-Change-QTreeView-highlight-color
        Note: this can actually do alot more than that with the QPalette...
            which is something I should learn how to use apparently...

        """
        from qtpy.QtGui import QPalette
        item = index.internalPointer()
        new_option = QStyleOptionViewItem(option)
        brush = QBrush()
        if item.isEnabled():
            color = QColor(*iColor["rgba_text"])
        else:
            color = QColor(*iColor["rgba_text_disabled"])
        # TODO highlight selection color???
        # why did I move this here?
        brush.setColor(color)

        # brush2 = QBrush(QColor(0, 255, 0, 128))
        new_option.palette.setBrush(QPalette.Normal, QPalette.HighlightedText, brush)
        # new_option.palette.setBrush(QPalette.Normal, QPalette.Highlight, brush2)

        QStyledItemDelegate.paint(self, painter, new_option, index)

        # if option.state == QStyle.State_Selected:
        #     brush2 = QBrush(QColor(0, 255, 255, 128))
        return


# example drop indicator
class AbstractDragDropIndicator(QProxyStyle):
    """
    Drag / drop style.

    Args:
        direction (Qt.DIRECTION): What direction the current flow of
            the widget is
    """
    INDICATOR_WIDTH = 2
    INDICATOR_SIZE = 10

    def __init__(self, parent=None):
        super(AbstractDragDropIndicator, self).__init__(parent)
        self._orientation = Qt.Vertical

    def orientation(self):
        return self._orientation

    def setOrientation(self, orientation):
        self._orientation = orientation

    def __drawVertical(self, widget, option, painter, size, width):
        # drop between
        y_pos = option.rect.topLeft().y()
        if option.rect.height() == 0:
            # create indicators
            l_indicator = self.createTriangle(size, attrs.EAST)
            l_indicator.translate(QPoint(size + (width / 2), y_pos))

            r_indicator = self.createTriangle(size, attrs.WEST)
            r_indicator.translate(QPoint(
                widget.width() - size - (width / 2), y_pos)
            )

            # draw
            painter.drawPolygon(l_indicator)
            painter.drawPolygon(r_indicator)
            painter.drawLine(
                QPoint(size + (width / 2), y_pos),
                QPoint(widget.width() - size - (width / 2), y_pos)
            )

            # set fill color
            background_color = QColor(*iColor["rgba_gray_3"])
            brush = QBrush(background_color)
            path = QPainterPath()
            path.addPolygon(l_indicator)
            path.addPolygon(r_indicator)
            painter.fillPath(path, brush)
        #
        # # drop on
        else:
            indicator_rect = QRect((width / 2), y_pos, widget.width() - (width / 2), option.rect.height())
            painter.drawRoundedRect(indicator_rect, 1, 1)

    def __drawHorizontal(self, widget, option, painter, size, width):
        x_pos = option.rect.topLeft().x()
        if option.rect.width() == 0:
            # create indicators
            top_indicator = self.createTriangle(size, attrs.NORTH)
            top_indicator.translate(QPoint(x_pos, size + (width / 2)))

            bot_indicator = self.createTriangle(size, attrs.SOUTH)
            bot_indicator.translate(QPoint(x_pos, option.rect.height() - size - (width / 2)))

            # draw
            painter.drawPolygon(top_indicator)
            painter.drawPolygon(bot_indicator)
            painter.drawLine(
                QPoint(x_pos, size + (width / 2)),
                QPoint(x_pos, option.rect.height() - size + (width / 2))
            )

            # set fill color
            background_color = QColor(*iColor["rgba_gray_3"])
            brush = QBrush(background_color)
            path = QPainterPath()
            path.addPolygon(top_indicator)
            path.addPolygon(bot_indicator)

            painter.fillPath(path, brush)

        # drop on
        else:
            painter.drawRoundedRect(option.rect, 1, 1)

    def drawPrimitive(self, element, option, painter, widget=None):
        """
        https://www.qtcentre.org/threads/35443-Customize-drop-indicator-in-QTreeView

        Draw a line across the entire row rather than just the column
        we're hovering over.  This may not always work depending on global
        style - for instance I think it won't work on OSX.

        Still draws the original line - not really sure why
            - clearing the painter will clear the entire view
        """
        if element == self.PE_IndicatorItemViewItemDrop:
            # border
            # get attrs
            size = AbstractDragDropIndicator.INDICATOR_SIZE
            width = AbstractDragDropIndicator.INDICATOR_WIDTH

            # border color
            border_color = QColor(*iColor["rgba_selected"])
            pen = QPen()
            pen.setWidth(AbstractDragDropIndicator.INDICATOR_WIDTH)
            pen.setColor(border_color)

            # background
            background_color = QColor(*iColor["rgba_selected"])
            background_color.setAlpha(64)
            brush = QBrush(background_color)

            # set painter
            painter.setPen(pen)
            painter.setBrush(brush)

            # draw
            if self.orientation() == Qt.Vertical:
                self.__drawVertical(widget, option, painter, size, width)
            elif self.orientation() == Qt.Horizontal:
                self.__drawHorizontal(widget, option, painter, size, width)
        else:
            super(AbstractDragDropIndicator, self).drawPrimitive(element, option, painter, widget)

    def createTriangle(self, size, direction=attrs.EAST):
        """
        Creates a triangle to be displayed by the painter.

        Args:
            size (int): the size of the triangle to draw
            direction (attrs.DIRECTION): which way the triangle should point
        """
        if direction == attrs.EAST:
            triangle_point_list = [
                [0, 0],
                [-size, size],
                [-size, -size],
                [0, 0]
            ]
        if direction == attrs.WEST:
            triangle_point_list = [
                [0, 0],
                [size, size],
                [size, -size],
                [0, 0]
            ]
        if direction == attrs.NORTH:
            triangle_point_list = [
                [0, 0],
                [size, -size],
                [-size, -size],
                [0, 0]
            ]
        if direction == attrs.SOUTH:
            triangle_point_list = [
                [0, 0],
                [size, size],
                [-size, size],
                [0, 0]
            ]

        # fixed this...
        if API_NAME == "PySide2":
            triangle = QPolygonF([QPointF(point[0], point[1]) for point in triangle_point_list])
        else:
             triangle = QPolygonF(map(lambda p: QPoint(*p), triangle_point_list))

        return triangle


if __name__ == '__main__':
    import sys
    from qtpy.QtWidgets import (
        QApplication, QTreeView, QListView, QAbstractItemView)
    from qtpy.QtGui import QCursor

    from cgwidgets.views import AbstractDragDropModel
    app = QApplication(sys.argv)

    def testDrag(indexes):
        " test drag..."
        print(indexes)

    def testDrop(indexes, parent):
        print(indexes, parent)

    def testEdit(item, old_value, new_value):
        print(item, old_value, new_value)

    def testEnable(item, enabled):
        print(item.columnData()['name'], enabled)

    def testDelete(item):
        print(item.columnData()['name'])

    model = AbstractDragDropModel()

    for x in range(0, 4):
        model.insertNewIndex(x, str('node%s'%x))

    #model.setIsRootDropEnabled(False)
    #model.setIsDragEnabled(False)
    # set model event
    model.setDragStartEvent(testDrag)
    model.setDropEvent(testDrop)
    model.setTextChangedEvent(testEdit)
    model.setItemEnabledEvent(testEnable)
    model.setItemDeleteEvent(testDelete)

    tree_view = AbstractDragDropListView()
    tree_view.setStyle(AbstractDragDropIndicator())

    tree_view.move(QCursor.pos())
    tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

    tree_view.setModel(model)
    #model.setIsDragEnabled(True)

    list_view = AbstractDragDropListView()

    list_view.move(QCursor.pos())
    #list_view.setDragDropOverwriteMode(False)
    list_view.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
    #list_view.setDropIndicatorShown(True)
    list_view.setModel(model)
    list_view.setIsDropEnabled(False)
    list_view.setIsEnableable(False)
    # table_view = QTableView()
    # table_view.show()

    #tree_view.show()

    list_view.show()
    # table_view.setModel(model)

    sys.exit(app.exec_())