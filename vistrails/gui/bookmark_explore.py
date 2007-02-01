############################################################################
##
## Copyright (C) 2006-2007 University of Utah. All rights reserved.
##
## This file is part of VisTrails.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-license.php
##
## If you are unsure which license is appropriate for your use (for
## instance, you are interested in developing a commercial derivative
## of VisTrails), please contact us at vistrails@sci.utah.edu.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################
""" This file contains widgets related to parameter exploration 
of aliases in user's bookmarks

QAliasExplorationPanel
QAliasDimensionWidget
QAliasDropBox
QAliasExplorationTable
QRangeStringContainer

"""
from PyQt4 import QtCore, QtGui
from gui.theme import CurrentTheme
from gui.common_widgets import QToolWindowInterface
from gui.bookmark_alias import QAliasTable, QAliasTableWidgetItem
from gui.param_explore import QRangeString 

################################################################################
class QAliasExplorationPanel(QtGui.QFrame, QToolWindowInterface):
    """
    QAliasExplorationPanel shows aliases to be explored.
    
    """
    def __init__(self, parent=None, manager=None):
        """ QAliasExplorationPanel(parent: QWidget, manaager: BookmarksManager)
                                                 -> QAliasExplorationPanel
        Initializes the panel and sets bookmark manager
        
        """
        QtGui.QFrame.__init__(self, parent)
        self.bookmarkPanel = None
        self.setFrameStyle(QtGui.QFrame.Panel|QtGui.QFrame.Sunken)
        self.manager = manager
        self.dimLabels = ['Dim %d' % (i+1) for i in range(4)]
        vLayout = QtGui.QVBoxLayout()
        vLayout.setSpacing(0)
        vLayout.setMargin(0)
        self.setLayout(vLayout)
        self.dimTab = QtGui.QTabWidget()
        for t in range(4):
            tab = QAliasDimensionWidget(manager=self.manager)
            tab.paramEx = self
            self.dimTab.addTab(tab, self.dimLabels[t]+' (1)')        
        vLayout.addWidget(self.dimTab)
        createButton = QtGui.QPushButton("Perform Exploration")
        vLayout.addWidget(createButton)
        if parent:
            self.bookmarkPanel = parent.bookmarkPanel
        self.connect(createButton, QtCore.SIGNAL('clicked()'),
                     self.startParameterExploration)
        self.setWindowTitle('Parameter Exploration')

    def startParameterExploration(self):
        """ startParameterExploration() -> None
        Collects inputs from widgets and the builders to setup and
        start a parameter exploration
        
        """
        if not self.manager.controller:
            return
        specs = []
        dimCount = 0
        for dim in range(self.dimTab.count()):
            tab = self.dimTab.widget(dim)
            stepCount = tab.sizeEdit.value()
            specsPerDim = []
            for row in range(tab.dropbox.parameters.rowCount()):
                type = tab.dropbox.parameters.verticalHeaderItem(row).type
                alias = tab.dropbox.parameters.verticalHeaderItem(row).alias
                ranges = []
                if type == 'String':
                    wgt = tab.dropbox.parameters.cellWidget(row,0)
                    strCount = wgt.listWidget.count()
                    strings = [str( wgt.listWidget.item(i%strCount).text())
                               for i in range(stepCount)]
                    ranges.append(strings)
                else:
                    convert = {'Integer': int,
                               'Float': float}
                    cv = convert[type]
                    sItem = tab.dropbox.parameters.item(row,0)
                    eItem = tab.dropbox.parameters.item(row,1)
                    ranges.append((cv(sItem.text()),cv(eItem.text())))
                interpolator = (alias, type, ranges, stepCount) 
                specsPerDim.append(interpolator)                
            specs.append(specsPerDim)
        ids = self.bookmarkPanel.bookmarkPalette.checkedList
        self.manager.parameterExploration(ids, specs)

    def clear(self):
        """ clear() -> None
        Clear all settings and leave the GUI empty
        
        """
        for dim in range(self.dimTab.count()):
            tab = self.dimTab.widget(dim)
            tab.dropbox.clear()

    def removeAlias(self,alias):
        """removeAlias(alias:str) -> None
        Propagates event down to each tab. """
        for dim in range(self.dimTab.count()):
            tab = self.dimTab.widget(dim)
            tab.dropbox.parameters.removeAlias(alias)

class QAliasDimensionWidget(QtGui.QWidget):
    """
    QALiasDimensionWidget is the tab widget holding parameter info for a
    single dimension
    
    """
    def __init__(self, parent=None, manager=None):
        """ QAliasDimensionWidget(parant: QWidget) -> QALiasDimensionWidget      
        Initialize the tab with appropriate labels and connect all
        signals and slots
                             
        """
        QtGui.QWidget.__init__(self, parent)
        self.manager = manager
        self.sizeLabel = QtGui.QLabel('&Step Count')
        self.sizeEdit = QtGui.QSpinBox()
        self.sizeEdit.setMinimum(1)        
        self.connect(self.sizeEdit,QtCore.SIGNAL("valueChanged(int)"),
                     self.stepCountChanged)
        self.sizeLabel.setBuddy(self.sizeEdit)
        
        sizeLayout = QtGui.QHBoxLayout()
        sizeLayout.addWidget(self.sizeLabel)
        sizeLayout.addWidget(self.sizeEdit)
        sizeLayout.addStretch(0)
        
        topLayout = QtGui.QVBoxLayout()
        topLayout.addLayout(sizeLayout)
        self.dropbox = QAliasDropBox(None, self.manager)
        topLayout.addWidget(self.dropbox)
        self.setLayout(topLayout)
        self.paramEx = None
        
    def stepCountChanged(self, count):
        """ stepCountChanged(count: int)        
        When the number step in this dimension is changed, notify and
        invalidate all of its children
        
        """
        idx = self.paramEx.dimTab.indexOf(self)
        self.paramEx.dimTab.setTabText(idx,
                                       self.paramEx.dimLabels[idx] +
                                       ' (' + str(count) + ')')
        for i in range(self.dropbox.parameters.rowCount()):
            item = self.dropbox.parameters.verticalHeaderItem(i)
            if item.type =='String':
                child = self.dropbox.parameters.cellWidget(i,0)
                child.updateStepCount(child.listWidget.count())

class QAliasDropBox(QtGui.QScrollArea):
    """
    QAliasDropBox is just a widget such that alias items from
    QBookmarkAliasPanel can be dropped into its client rect. It then
    construct an input form based on the type of handling widget
    
    """
    def __init__(self, parent=None, manager=None):
        """ QAliasDropBox(parent: QWidget) -> QAliasDropBox
        Initialize widget constraints
        
        """
        QtGui.QScrollArea.__init__(self, parent)
        self.setAcceptDrops(True)
        self.panel = self.createPanel()
        self.panel.setVisible(False)
        self.setWidgetResizable(True)
        self.setWidget(self.panel)
        self.updateLocked = False
        self.manager = manager

    def createPanel(self):
        """createPanel() -> QWidget
        Creates a widget with a layout to hold a QAliasExplorationTable

        """
        widget = QtGui.QWidget(self)
        layout = QtGui.QVBoxLayout()
        widget.setLayout(layout)
        widget.layout().setMargin(0)
        widget.layout().setSpacing(0)

        self.parameters = QAliasExplorationTable()
        
        layout.addWidget(self.parameters, 1)

        return widget

    def dragEnterEvent(self, event):
        """ dragEnterEvent(event: QDragEnterEvent) -> None
        Set to accept drops from alias table
        
        """
        if type(event.source())==QAliasTable:
            data = event.mimeData()
            if hasattr(data, 'aliases'):
                event.accept()
        else:
            event.ignore()
        
    def dragMoveEvent(self, event):
        """ dragMoveEvent(event: QDragMoveEvent) -> None
        Set to accept drag move event from alias table
        
        """
        if type(event.source())==QAliasTable:
            data = event.mimeData()
            if hasattr(data, 'aliases'):
                event.accept()

    def dropEvent(self, event):
        """ dropEvent(event: QDragMoveEvent) -> None
        Accept drop event to add a new alias
        
        """
        if type(event.source())==QAliasTable:
            data = event.mimeData()
            if hasattr(data, 'aliases'):
                event.setDropAction(QtCore.Qt.CopyAction)
                event.accept()
                for item in data.aliases:
                    if self.parameters.rowCount() == 0:
                        self.parameters.horizontalHeader().show()

                    self.parameters.createAliasRow(item.alias, item.type)
                    self.scrollContentsBy(0, self.viewport().height())

class QAliasExplorationTable(QtGui.QTableWidget):
    """
    QAliasExplorationTable just inherits from QTableWidget to have a customized
    table and items

    """
    def __init__(self, parent=None, manager=None):
        """ QAliasExplorationTable(parent: QWidget, manager:BookmarkManager ) -> 
        QAliasExplorationTable
        Set bookmark manager
        """
        QtGui.QTableWidget.__init__(self, parent)
        self.manager = manager
        self.aliases = {}
        self.setColumnCount(2)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)
        labels = QtCore.QStringList()
        labels << "Start" << "End"
        self.setHorizontalHeaderLabels(labels)
        self.horizontalHeader().hide()
        self.connect(self.verticalHeader(),
                     QtCore.SIGNAL("sectionClicked(int)"),
                     self.updateFocus)
        self.verticalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        
    def createAliasRow(self, alias, type):
        """ createAliasRow( alias: str, type: str) -> None
        Creates a row in the table
        
        """
        row = self.rowCount()
        self.insertRow(row)
        
        item = QAliasTableWidgetItem(alias, type, alias)
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        self.setVerticalHeaderItem(row,item)
        
        if type != 'String':
            sItem = QAliasTableWidgetItem(alias, type, "") 
            sItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable \
                           | QtCore.Qt.ItemIsSelectable)
            eItem = QAliasTableWidgetItem(alias, type, "")
        
            self.setItem(row, 0, sItem)
            self.setSpan(row,0,1,1)
            self.setItem(row, 1, eItem)
        else:
            #join the two columns in one
            self.setSpan(row,0,1,2)
            widget = QRangeStringContainer(self)
            layout = QtGui.QGridLayout()
            widget.setLayout(layout)
            lineEdit = QRangeString(0, widget)
            widget.listWidget = lineEdit.listWidget
            layout.addWidget(lineEdit,0,1,1,2)
            self.connect(widget.listWidget,
                         QtCore.SIGNAL("changed(int)"),
                         widget.updateStepCount)
            h = widget.sizeHint().height()
            w = widget.sizeHint().width()
            self.setRowHeight(row,h)
            self.setCellWidget(row,0,widget)
            widget.updateStepCount(widget.listWidget.count())

    def updateFocus(self, row):
        """ updateFocus(row: int) -> None
        Set focus to the alias cell when clicking on the header cell 

        """
        self.setCurrentCell(row,0)

    def getItemRow(self, alias):
        """getItemRow(alias:str) -> int 
        Searches for the row that contains the alias name 

        """
        for i in range(self.rowCount()):
            item = self.verticalHeaderItem(i)
            if item:
                if item.alias == alias:
                    return i
        return -1

    def removeAlias(self, alias):
        """removeAlias(alias:str) -> None Removes the row containing alias """
        row = self.getItemRow(alias)
        self.deleteRow(row)
    
    def keyPressEvent(self, event):
        """keyPressEvent(event: QKeyEvent) -> None 
        Event handler for key press events. 
         - Ctrl(Command) + Backspace or Ctrl(command) + Del 
                     removes the current row
        """
        if (event.key() == QtCore.Qt.Key_Delete or 
            event.key() == QtCore.Qt.Key_Backspace):
            if event.modifiers() & QtCore.Qt.ControlModifier:
                event.accept()
                row = self.currentRow()
                self.deleteRow(row)
            else:
                event.ignore()
        else:
            event.ignore()

    def deleteRow(self, row):
        """deleteRow(row: int) -> None 
        Removes a row and updates the table.

        """
        if row > -1:
            self.removeRow(row)
            item = self.verticalHeaderItem(row)
            if item.type != 'String':
                self.setSpan(row,0,1,1)
            if self.rowCount() == 0:
                self.horizontalHeader().hide()

class QRangeStringContainer(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

    def stepCount(self):
        dropbox = self.parent().parent().parent().parent().parent() 
        return dropbox.parent().sizeEdit.value()
    
    def updateStepCount(self, count):
        display = 'Count: '+ str(count)
        stepCount = self.stepCount()
        if count>stepCount:
            display = display + ' (Too many values)'
        if count<stepCount:
            display = display + ' (Need more values)'        
        self.setToolTip(display)