# -*- coding: utf-8 -*-
# Created on : 12/11/2024, 9:19:29 pm
# Author     : Grant Pearson, Eureka Technology Limited
"""
/***************************************************************************
 SQLDBMineDialog
                                 A QGIS plugin
 An attribute query dialog
 Create query field for each field in layer
 Execute database sql query and puts results in parent display table
 ***************************************************************************/
"""

import os
from qgis.core import QgsProject, QgsProviderRegistry
from qgis.PyQt.QtCore import (
    Qt, QCoreApplication, QSize)
from qgis.PyQt.QtGui import (
    QIcon, QFont)
from qgis.PyQt.QtWidgets import (
    QLabel, QApplication, QDialog,
    QFrame, QFormLayout, QVBoxLayout, QHBoxLayout,
    QSizePolicy, QSpacerItem, QScrollArea,
    QLineEdit, QToolButton)

from .sql_db_mine_utilities import (
    APP_NAME, MINE_LAYER_PREFIX, MessageBoxes, Utilities)


# class SQLDBMineDialog(QgsAttributeForm):
class SQLDBMineDialog(QDialog):
    def __init__(self, parent, iface, layer):
        """
        Constructor
        """
        super(SQLDBMineDialog, self).__init__(parent)
        self.parent = parent
        self.iface = iface
        self.layer = layer
        self.iconQuery = Utilities.getIcon(
            os.path.join('images', 'database-search.png'))
        self.iconQueryDisabled = Utilities.getIcon(
            os.path.join('images', 'database-search-disabled.png'))
        self.iconHelp = Utilities.getIcon(
            os.path.join('images', 'help.png'))
        self.iconReturn = Utilities.getIcon(
            os.path.join('images', 'return.png'))
    # /__init__

    # Initialize dialog
    def init(self, cid, level):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.cid = cid
        self.level = level
        self.setStyleSheet(Utilities.stylesheet())
        sizePolicyExpanding = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicyExpanding.setHorizontalStretch(0)
        sizePolicyExpanding.setVerticalStretch(0)
        sizePolicyFixed = QSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicyFixed.setHorizontalStretch(0)
        sizePolicyFixed.setVerticalStretch(0)

        self.setWindowTitle(MessageBoxes.translate("Query Feature Form"))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.resize(640, 750)
        self.setBaseSize(QSize(640, 750))
        self.setMinimumSize(QSize(200, 200))
        self.setMaximumSize(QSize(16777215, 16777215))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self.centralLayout = QVBoxLayout(self)
        self.centralLayout.setSpacing(1)
        self.centralLayout.setObjectName(u"centralLayout")
        self.centralLayout.setContentsMargins(0, 0, 0, 0)

        font = QFont()
        font.setPointSize(9)

        self.activeLayerName = self.layer.name().removeprefix(
            MINE_LAYER_PREFIX).removesuffix(
                f' [{self.cid}-{self.level}]')
        layers = QgsProject.instance().mapLayersByName(self.activeLayerName)
        for mapLayer in layers:
            if mapLayer.name() == self.activeLayerName:
                self.activeMapLayer = mapLayer
        self.fields = self.activeMapLayer.fields()
        self.formFrame = QFrame()
        self.formFrame.setObjectName(u"formFrame")
        sizePolicyExpanding.setHeightForWidth(
            self.formFrame.sizePolicy().hasHeightForWidth())
        self.formFrame.setSizePolicy(sizePolicyExpanding)
        self.formFrame.setMinimumSize(QSize(200, (self.fields.size() * 30)))
        self.formFrame.setMaximumSize(
            QSize(16777215, (self.fields.size() * 40)))
        self.formFrame.setBaseSize(QSize(600, (self.fields.size() * 40)))
        self.formFrame.setLineWidth(0)

        self.formLayout = QFormLayout(self.formFrame)

        self.textFields = []
        i = 0
        for field in self.fields:
            # print(f"{field.displayName()} {field.typeName().lower()}")
            textField = QLineEdit()
            textField.setObjectName(field.name())
            textField.setReadOnly(False)
            textField.setText(None)
            textField.setFixedHeight(30)
            sizePolicyExpanding.setHeightForWidth(
                textField.sizePolicy().hasHeightForWidth())
            textField.setSizePolicy(sizePolicyExpanding)
            textField.setClearButtonEnabled(True)
            textField.setStyleSheet(u"color: black; background-color: white; ")
            fieldType = field.typeName().lower()
            match fieldType:
                case "string":
                    tip = "Query string value"
                case "date":
                    tip = "Query date value ('YYYY-MM-DD')"
                case "datetime":
                    tip = "Query datetime value ('YYYY-MM-DD HH:MM:SS')"
                case "time":
                    tip = "Query time value ('HH:MM:SS')"
                case "real" | "double" | "float" | "integer" | "integer64":
                    tip = "Query numeric value (prefix with comparitor, " \
                          "default is '=')"
                case _:
                    tip = "Query value"
            textField.setToolTip(MessageBoxes.translate(tip))
            self.textFields.append(textField)
            self.formLayout.addRow(
                QLabel(field.displayName().replace("_", " ").title()),
                self.textFields[i])
            i += 1

        self.scroll = QScrollArea()
        self.scroll.setWidget(self.formFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(u"background-color: #e0ffe1; ")

        self.centralLayout.addWidget(self.scroll)
        self.verticalSpacer = QSpacerItem(
            10, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.centralLayout.addItem(self.verticalSpacer)

        self.actionButtonFrame = QFrame()
        self.actionButtonFrame.setObjectName(u"actionButtonFrame")
        self.actionButtonFrame.setMinimumSize(QSize(134, 33))
        self.actionButtonFrame.setMaximumSize(QSize(16777215, 33))
        sizePolicyExpanding.setHeightForWidth(
            self.actionButtonFrame.sizePolicy().hasHeightForWidth())
        self.actionButtonFrame.setSizePolicy(sizePolicyExpanding)
        self.actionButtonFrame.setLineWidth(0)
        self.horizontalLayoutButtonFrame = QHBoxLayout(self.actionButtonFrame)
        self.horizontalLayoutButtonFrame.setSpacing(0)
        self.horizontalLayoutButtonFrame.setObjectName(
            u"horizontalLayoutButtonFrame")
        self.horizontalLayoutButtonFrame.setContentsMargins(0, 0, 0, 0)

        self.horizontalSpacer1 = QSpacerItem(
            600, 32, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.horizontalLayoutButtonFrame.addItem(self.horizontalSpacer1)

        self.queryButton = QToolButton(self.actionButtonFrame)
        self.queryButton.setObjectName(u"queryButton")
        self.queryButton.setBaseSize(QSize(0, 0))
        self.queryButton.setFont(font)
        self.queryButton.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.queryButton.setIconSize(QSize(32, 32))
        self.queryButton.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.queryButton.setText(
            QCoreApplication.translate("MainWindow", u"Query", None))
        self.queryButton.setToolTip(
            MessageBoxes.translate("Query features from database"))
        self.queryButton.setSizePolicy(sizePolicyFixed)
        self.queryButton.setFixedSize(QSize(87, 32))
        self.queryButton.setAutoRaise(False)
        self.queryButton.setIcon(QIcon(self.iconQuery))
        self.queryButton.clicked.connect(self.executeQuery)
        self.horizontalLayoutButtonFrame.addWidget(self.queryButton)

        self.horizontalSpacer2 = QSpacerItem(
            600, 32, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.horizontalLayoutButtonFrame.addItem(self.horizontalSpacer2)

        self.helpButton = QToolButton(self.actionButtonFrame)
        self.helpButton.setObjectName(u"helpButton")
        self.helpButton.setBaseSize(QSize(0, 0))
        self.helpButton.setFont(font)
        self.helpButton.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.helpButton.setIconSize(QSize(32, 32))
        self.helpButton.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.helpButton.setText(
            QCoreApplication.translate("MainWindow", u"Help", None))
        self.helpButton.setIcon(QIcon(self.iconReturn))
        self.helpButton.setToolTip(
            MessageBoxes.translate("Query help"))
        self.helpButton.setSizePolicy(sizePolicyFixed)
        self.helpButton.setFixedSize(QSize(87, 32))
        self.helpButton.setAutoRaise(False)
        self.helpButton.setIcon(QIcon(self.iconHelp))
        self.helpButton.clicked.connect(self.help)
        self.horizontalLayoutButtonFrame.addWidget(self.helpButton)

        self.horizontalSpacer3 = QSpacerItem(
            600, 32, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.horizontalLayoutButtonFrame.addItem(self.horizontalSpacer3)

        self.returnButton = QToolButton(self.actionButtonFrame)
        self.returnButton.setObjectName(u"returnButton")
        self.returnButton.setBaseSize(QSize(0, 0))
        self.returnButton.setFont(font)
        self.returnButton.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.returnButton.setIconSize(QSize(32, 32))
        self.returnButton.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.returnButton.setText(
            QCoreApplication.translate("MainWindow", u"Return", None))
        self.returnButton.setIcon(QIcon(self.iconReturn))
        self.returnButton.setToolTip(
            MessageBoxes.translate("Close query form"))
        self.returnButton.setSizePolicy(sizePolicyFixed)
        self.returnButton.setFixedSize(QSize(87, 32))
        self.returnButton.setAutoRaise(False)
        self.returnButton.setIcon(QIcon(self.iconReturn))
        self.returnButton.clicked.connect(self.closeWindow)
        self.horizontalLayoutButtonFrame.addWidget(self.returnButton)

        self.horizontalSpacer4 = QSpacerItem(
            600, 32, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.horizontalLayoutButtonFrame.addItem(self.horizontalSpacer4)

        self.centralLayout.addWidget(self.actionButtonFrame)

        v = self.formFrame.size().height() + \
            self.actionButtonFrame.size().height() + 33
        if v > 800:
            v = 800
        self.resize(self.size().width(), v)
        self.setLayout(self.centralLayout)
        QApplication.restoreOverrideCursor()
        self.setVisible(True)
    # /init

    # Action to copy selected rows to clipboard
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_F1:
            self.help()
        elif event.key() == Qt.Key.Key_F3:
            self.executeQuery()
        elif event.key() == Qt.Key.Key_F and \
                (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.executeQuery()
    # /keyPressEvent

    def help(self):
        help = \
            MessageBoxes.translate(
                u'Help on SQL Database Query Form:\n\n'
                'Enter exact values for fields to query on.\n'
                'Standard SQL comparison clauses can be entered by'
                ' starting with a SQL comparison operator:\n') + \
            '\tBETWEEN AND\n' + \
            '\t=\n' + \
            '\t>=\n' + \
            '\t>\n' + \
            '\tIN\n' + \
            '\tIS NOT NULL\n' + \
            '\tIS NOT\n' + \
            '\tIS NULL\n' + \
            '\tIS\n' + \
            '\tISNULL\n' + \
            '\t<=\n' + \
            '\t<\n' + \
            '\tNOT BETWEEN\n' + \
            '\t!=\n' + \
            '\tNOT IN'
        MessageBoxes.messageBox(
            self,
            MessageBoxes.INFORMATION,
            f'{Utilities.getApptitle(self)} : Query Help',
            help)
    # /help

    # Action to display a query form for the active layer
    def executeQuery(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        conditions = None
        operators = ['=', '<', '>', '!', 'between', 'in', 'is', 'not']
        # get field names and conditions
        for textField in self.textFields:
            text = textField.text()
            if text:
                fieldName = textField.objectName()
                field = None
                for f in self.fields:
                    if f.name() == fieldName:
                        field = f
                if field:
                    if text.lower().strip() == "null":
                        c = f"{textField.objectName()} IS NULL"
                    elif text.lower().strip() == "not null":
                        c = f"{textField.objectName()} IS NOT NULL"
                    else:
                        first = text.split()[0].lower()
                        if text[0] in operators or first in operators:
                            c = f"{textField.objectName()} {text}"
                        else:
                            fieldType = field.typeName().lower()
                            match fieldType:
                                case "string":
                                    t = text.replace("'", "''")
                                    c = f"{textField.objectName()}='{t}'"
                                case "date":
                                    if text[0].isnumeric():
                                        c = f"{textField.objectName()}='{text}'"
                                    else:
                                        c = f"{textField.objectName()} {text}"
                                case "datetime":
                                    if text[0].isnumeric():
                                        c = f"{textField.objectName()}='{text}'"
                                    else:
                                        c = f"{textField.objectName()} {text}"
                                case "time":
                                    if text[0].isnumeric():
                                        c = f"{textField.objectName()}='{text}'"
                                    else:
                                        c = f"{textField.objectName()} {text}"
                                case "real" | "double" | "float" | "integer" | \
                                     "integer64":
                                    if text[0].isnumeric():
                                        c = f"{textField.objectName()}={text}"
                                    else:
                                        c = f"{textField.objectName()} {text}"
                                case _:
                                    c = f"{textField.objectName()}={text}"
                    if conditions:
                        conditions += "\nAND " + c
                    else:
                        conditions = "\nWHERE " + c
        if conditions:
            queryFields = Utilities.queryFieldList(self.fields)
            # get table name
            uriComponents = QgsProviderRegistry.instance().decodeUri(
                self.activeMapLayer.dataProvider().name(),
                self.activeMapLayer.source())
            sourceConfig = Utilities.extractSourceURI(
                self.activeMapLayer.storageType(),
                uriComponents)
            queryTable = sourceConfig.get("tablename")
            # build sql query and execute
            sql = f'SELECT {queryFields}\nFROM {queryTable}'
            sql += conditions + ";"
            # print(sql)
            self.layer.startEditing()
            mineData = self.layer.dataProvider()
            mineData.addAttributes(self.fields)
            mineData = Utilities.readDatabase(
                self,
                sourceConfig,
                self.fields,
                sql,
                mineData)
            self.layer.commitChanges()
            self.parent.updateAttributeTable(mineData)
            QApplication.restoreOverrideCursor()
        else:
            QApplication.restoreOverrideCursor()
            msg = MessageBoxes.translate("Query conditions must be entered.")
            MessageBoxes.messageBox(
                self,
                MessageBoxes.WARNING,
                APP_NAME,
                msg)
    # /executeQuery

    # Action to close attribute table window
    def closeWindow(self):
        self.close()
    # /closeWindow

    # Cleanup before attribute table window closes
    def cleanupWhenWindowClosed(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.returnButton.clicked.disconnect(self.closeWindow)
        self.helpButton.clicked.disconnect(self.help)
        self.queryButton.clicked.disconnect(self.executeQuery)
        QApplication.restoreOverrideCursor()
    # /cleanupWhenWindowClosed

    # Trigger action for when close event occurs
    def closeEvent(self, event):
        # print(f'close event {self.activeLayer.name()}')
        self.cleanupWhenWindowClosed()
    # /closeEvent
# /SQLDBMineDialog
