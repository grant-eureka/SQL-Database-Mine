# -*- coding: utf-8 -*-
# Created on : 12/11/2024, 9:19:29 pm
# Author     : Grant Pearson, Eureka Technology Limited
"""
/***************************************************************************
 DBMineWindow
                                 A QGIS plugin
 An attribute table with relation options
 ***************************************************************************/
"""

import os
import platform
import sys

from qgis.PyQt import QtCore
from qgis.utils import Qgis
from qgis.core import (
    QgsProject, QgsProviderRegistry,
    QgsVectorLayer, QgsVectorLayerCache,
    QgsFeature, QgsFeatureRequest)
from qgis.gui import (
    QgsAttributeTableModel, QgsAttributeTableFilterModel)
from qgis.PyQt.QtCore import (
    Qt)
from qgis.PyQt.QtGui import (
    QIcon)
from qgis.PyQt.QtWidgets import (
    QLabel, QAbstractItemView, QApplication, QMainWindow)

from .sql_db_mine_utilities import APP_NAME
from .sql_db_mine_utilities import MINE_LAYER_PREFIX
from .sql_db_mine_utilities import MessageBoxes
from .sql_db_mine_utilities import RelationItems
from .sql_db_mine_utilities import Utilities
from .ui_sql_db_mine_window import Ui_MainWindow
from .sql_db_mine_dialog import SQLDBMineDialog


class SQLDBMineWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent, iface, layer):
        """
        Constructor
        """
        super(SQLDBMineWindow, self).__init__(parent)
        #   Set up the user interface that is constructed with Qt Designer.
        self.parent = parent
        self.iface = iface
        self.metadata = Utilities.readMetadata(self)
        self.activeLayer = layer
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # self.setupUi(self)
        self.setWindowTitle(MessageBoxes.translate(Utilities.getApptitle(self)))
        self.iconRelations = Utilities.getIcon(
            os.path.join('images', 'relations.png'))
        self.iconQuery = Utilities.getIcon(
            os.path.join('images', 'database-search.png'))
        self.iconQueryDisabled = Utilities.getIcon(
            os.path.join('images', 'database-search-disabled.png'))
        self.iconSelectAll = Utilities.getIcon(
            os.path.join('images', 'select-all.png'))
        self.iconSelectNone = Utilities.getIcon(
            os.path.join('images', 'select-none.png'))
        self.iconCopy = Utilities.getIcon(
            os.path.join('images', 'copy.png'))
        self.iconSelectMap = Utilities.getIcon(
            os.path.join('images', 'map-icon.png'))
        self.iconSelectMapDisabled = Utilities.getIcon(
            os.path.join('images', 'map-icon-disabled.png'))
        self.iconReturn = Utilities.getIcon(
            os.path.join('images', 'return.png'))
        self.iconAbout = Utilities.getIcon(
            os.path.join('images', 'about.png'))
        self.iconExit = Utilities.getIcon(
            os.path.join('images', 'window-close.png'))

        icon = Utilities.getIcon(os.path.join('images', 'icon.png'))
        self.setWindowIcon(icon)
    # /__init__

    # Initialize window dialog
    def init(self, cid, level, pos=None, geometry=None):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.cid = cid
        self.level = level
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.closeAllWindows = False
        self.setStyleSheet(Utilities.stylesheet())

        # print(f'INIT\nlayer.name()={layer.name()} : '
        #       f'cid={self.cid} : level={self.level}')
        self.activeLayerName = self.activeLayer.name().removeprefix(
            MINE_LAYER_PREFIX).removesuffix(
                f' [{self.cid}-{self.level}]')
        # print(f'\t> self.activeLayerName={self.activeLayerName}')
        self.ui.layerField.setText(self.activeLayerName)
        self.setActiveLayer(self.activeLayerName)

        self.ui.relationsList.setToolTip(
            MessageBoxes.translate("Select relationship"))
        self.getRelations()

        # set widget settings
        self.ui.mineButton.setIcon(QIcon(self.iconRelations))
        self.ui.mineButton.setToolTip(
            MessageBoxes.translate("Mine related data from database"))
        self.ui.mineButton.clicked.connect(self.readRelated)

        self.ui.queryButton.setToolTip(
            MessageBoxes.translate("Open database query dialogue"))
        self.ui.queryButton.clicked.connect(self.showQueryForm)
        if Utilities.isDatabase(self.activeMapLayer.storageType()):
            self.ui.queryButton.setIcon(QIcon(self.iconQuery))
            self.ui.queryButton.setEnabled(True)
        else:
            self.ui.queryButton.setIcon(QIcon(self.iconQueryDisabled))
            self.ui.queryButton.setEnabled(False)

        self.ui.selectAllButton.setIcon(QIcon(self.iconSelectAll))
        self.ui.selectAllButton.setToolTip(
            MessageBoxes.translate("Select all rows"))
        self.ui.selectAllButton.clicked.connect(self.selectAll)

        self.ui.selectNoneButton.setIcon(QIcon(self.iconSelectNone))
        self.ui.selectNoneButton.setToolTip(
            MessageBoxes.translate("Clear selection"))
        self.ui.selectNoneButton.clicked.connect(self.selectNone)

        self.ui.copyButton.setIcon(QIcon(self.iconCopy))
        self.ui.copyButton.setToolTip(
            MessageBoxes.translate(
                "Copy selected feature attributes to clipboard"))
        self.ui.copyButton.clicked.connect(self.copyTable)

        self.ui.mapButton.setToolTip(
            MessageBoxes.translate("Map selected features"))
        self.ui.mapButton.clicked.connect(self.selectMap)
        if self.activeMapLayer.isSpatial():
            self.ui.mapButton.setIcon(QIcon(self.iconSelectMap))
            self.ui.mapButton.setEnabled(True)
        else:
            self.ui.mapButton.setIcon(QIcon(self.iconSelectMapDisabled))
            self.ui.mapButton.setEnabled(False)

        self.ui.returnButton.setIcon(QIcon(self.iconReturn))
        self.ui.returnButton.setToolTip(
            MessageBoxes.translate("Return to previous level"))
        self.ui.returnButton.clicked.connect(self.closeWindow)

        self.ui.aboutButton.setIcon(QIcon(self.iconAbout))
        self.ui.aboutButton.setToolTip(
            MessageBoxes.translate("Help about application"))
        self.ui.aboutButton.clicked.connect(self.aboutApp)

        self.ui.exitButton.setIcon(QIcon(self.iconExit))
        self.ui.exitButton.setToolTip(
            MessageBoxes.translate("Close plugin window"))
        self.ui.exitButton.clicked.connect(self.closeAll)

        # setup attribute table
        self.tableCache = QgsVectorLayerCache(
            self.activeLayer, self.activeLayer.featureCount())
        self.tableModel = QgsAttributeTableModel(self.tableCache)
        self.tableModel.loadLayer()
        self.tableFilterModel = QgsAttributeTableFilterModel(
            self.iface.mapCanvas(),
            self.tableModel)
        self.ui.tableView.setModel(self.tableFilterModel)
        self.ui.tableView.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.tableView.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.selectionModel = self.ui.tableView.selectionModel()
        self.ui.tableView.clicked.connect(self.tableClicked)
        self.activeLayer.selectionChanged.connect(self.selectionChanged)

        # Create a status bar
        self.statuslabel = QLabel()
        self.statuslabel.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.statuslabel.setFixedHeight(self.ui.statusbar.size().height())
        self.ui.statusbar.addWidget(self.statuslabel)
        self.updateStatus()

        self.savePos = pos
        self.saveGeometry = geometry
        QApplication.restoreOverrideCursor()
        self.setVisible(True)
    # /init

    def getAppname(self):
        return self.__class__.__name__
    # /getAppname

    def setActiveLayer(self, layerName):
        layers = QgsProject.instance().mapLayersByName(layerName)
        self.activeMapLayer = Utilities.findFirst(
            layers,
            lambda mapLayer: mapLayer.name() == layerName)
        """
        for mapLayer in layers:
            if mapLayer.name() == layerName:
                self.activeMapLayer = mapLayer
        """
    # /setActiveLayer

    def activeLayer(self):
        return self.activeLayer
    # /activeLayer

    def getRelations(self):
        #   Get relations for layer
        # print(f'\nRELATIONS for {self.activeMapLayer.name()}')
        relationNames = QgsProject.instance().relationManager().relations()
        for relationName in relationNames:
            relation = QgsProject.instance().relationManager().relation(
                relationName)
            kField = next(iter(relation.fieldPairs().keys()))
            vField = next(iter(relation.fieldPairs().values()))
            if self.activeLayerName == relation.referencedLayer().name():
                # print(f'{relation.name()} * referencedLayer'
                #       f'\n\treferencedLayer={relation.referencedLayer().name()}'
                #       f'\tvField={kField}'
                #       f'\n\treferencingLayer={relation.referencingLayer().name()}'
                #       f'\tkField={vField}'
                #       f'\n\t{relation.fieldPairs()}')
                storageType = relation.referencingLayer().storageType()
                # print(f'referencedLayer type {storageType}')
                isDatabase = Utilities.isDatabase(storageType) \
                    or Utilities.isFileSource(storageType) \
                    or storageType.lower() == "esri shapefile"
                if isDatabase:
                    RelationItems(
                        relation.referencedLayer().name(),
                        vField,
                        relation.referencingLayer().name(),
                        kField,
                        self.ui.relationsList)
            elif self.activeLayerName == relation.referencingLayer().name():
                # print(f'{relation.name()} * referencingLayer'
                #       f'\n\treferencedLayer={relation.referencedLayer().name()}'
                #       f'\t{vField}'
                #      f'\n\treferencingLayer={relation.referencingLayer().name()}'
                #       f'\t{kField}'
                #       f'\n\t{relation.fieldPairs()}')
                storageType = relation.referencedLayer().storageType()
                # print(f'referencingLayer type {storageType}')
                isDatabase = Utilities.isDatabase(storageType) \
                    or Utilities.isFileSource(storageType) \
                    or storageType.lower() == "esri shapefile"
                if isDatabase:
                    RelationItems(
                        relation.referencingLayer().name(),
                        kField,
                        relation.referencedLayer().name(),
                        vField,
                        self.ui.relationsList)

        #   Get joins for layer
        joins = self.activeMapLayer.vectorJoins()
        for join in joins:
            # print(f'JOIN for layer: {self.activeMapLayer.name()} '
            #       f'({join.targetFieldName()}) > '
            #       f'{join.joinLayer().name()} ({join.joinFieldName()})')
            storageType = join.joinLayer().storageType()
            isDatabase = Utilities.isDatabase(storageType) \
                or Utilities.isFileSource(storageType) \
                or storageType.lower() == "esri shapefile"
            if isDatabase:
                RelationItems(
                    self.activeMapLayer.name(),
                    join.targetFieldName(),
                    join.joinLayer().name(),
                    join.joinFieldName(),
                    self.ui.relationsList)

        #   Get joins referencing layer
        joinLayers = QgsProject.instance().mapLayers(True).values()
        for joinLayer in joinLayers:
            if joinLayer.type() == QgsVectorLayer.LayerType.VectorLayer:
                storageType = joinLayer.storageType()
                isDatabase = Utilities.isDatabase(storageType) \
                    or Utilities.isFileSource(storageType) \
                    or storageType.lower() == "esri shapefile"
                if isDatabase:
                    joins = joinLayer.vectorJoins()
                    for join in joins:
                        isJoinName = join.joinLayer().name() \
                            == self.activeMapLayer.name()
                        if isJoinName:
                            # print('JOIN referencing layer: '
                            #       f'{self.activeMapLayer.name()} '
                            #       f'({join.targetFieldName()}) > '
                            #       f'{joinLayer.name()} '
                            #       f'({join.joinFieldName()})')
                            RelationItems(
                                self.activeMapLayer.name(),
                                join.targetFieldName(),
                                joinLayer.name(),
                                join.joinFieldName(),
                                self.ui.relationsList)
        self.ui.relationsList.sortItems()
    # /getRelations

    def readRelated(self):
        # test for valid user selection
        # print('\nLOOKUP RELATED!')
        if len(self.ui.relationsList) == 0:
            msg = MessageBoxes.translate("No relations defined for")
            MessageBoxes.messageBox(
                self,
                MessageBoxes.INFORMATION,
                APP_NAME,
                f'{msg} {self.activeLayerName}.')
            return
        if len(self.ui.relationsList.selectedItems()) == 0:
            MessageBoxes.messageBox(
                self,
                MessageBoxes.INFORMATION,
                APP_NAME,
                MessageBoxes.translate(
                    "Select relationship from the list before mining."))
            return
        selectedFeatureCount = self.activeLayer.selectedFeatureCount()
        if selectedFeatureCount == 0:
            MessageBoxes.messageBox(
                self,
                MessageBoxes.INFORMATION,
                APP_NAME,
                MessageBoxes.translate(
                    "Select features from the table before mining."))
            return
        selection = self.activeLayer.selectedFeatures()

        # get target data source
        relation = self.ui.relationsList.selectedItems()[0]
        relation.__class__ = RelationItems

        # get referenced layer
        layers = QgsProject.instance().mapLayersByName(relation.refLayer)
        referenceLayer = Utilities.findFirst(
            layers,
            lambda layer: layer.name() == relation.refLayer)
        fields = referenceLayer.fields()
        keyField = self.activeLayer.fields().field(relation.primaryField)

        # create temporary memory layer to store related data for
        #  attribute table
        mineLayerName = \
            f'{MINE_LAYER_PREFIX}{referenceLayer.name()}' \
            f' [{self.cid}-{self.level + 1}]'
        layers = QgsProject.instance().mapLayersByName(mineLayerName)
        for layer in layers:
            isMineLayer = layer.name() == mineLayerName \
                and layer.dataProvider().name() == 'memory'
            if isMineLayer:
                QgsProject.instance().removeMapLayer(layer.id())
        mineLayer = QgsVectorLayer(
            path='None',
            baseName=mineLayerName,
            providerLib='memory')
        QgsProject.instance().addMapLayer(mineLayer)
        mineLayer.startEditing()
        mineData = mineLayer.dataProvider()
        mineData.addAttributes(fields)
        mineLayer.updateFields()
        mineLayer.commitChanges()

        # get active data source
        storageType = referenceLayer.storageType()
        mineLayer.startEditing()
        isDatabase = Utilities.isDatabase(storageType)
        isFileSource = Utilities.isFileSource(storageType)
        isEsriShapefile = storageType.lower() == "esri shapefile"
        if isDatabase:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            # query database to get related data
            # print(f'\nquery database to get related data: {storageType}')
            uriComponents = QgsProviderRegistry.instance().decodeUri(
                referenceLayer.dataProvider().name(),
                referenceLayer.source())
            # print(f'name = {referenceLayer.dataProvider().name()}')
            # print(f'source = {referenceLayer.source()}')
            # print(f'uriComponents = {uriComponents}')
            sourceConfig = Utilities.extractSourceURI(
                storageType,
                uriComponents)
            # print(f'sourceConfig: {sourceConfig}')

            # get selected key field values
            queryKeys = Utilities.queryKeysList(
                selection,
                relation.primaryField,
                keyField.typeName().lower())

            # get attribute fields
            queryFields = Utilities.queryFieldList(fields)
            queryTable = sourceConfig.get("tablename")
            queryKeyField = relation.refField

            sql = f'SELECT {queryFields}\nFROM {queryTable}' \
                f'\nWHERE {queryKeyField} IN ({queryKeys});'
            # print(sql)
            mineData = Utilities.readDatabase(
                self,
                sourceConfig,
                fields,
                sql,
                mineData)
            QApplication.restoreOverrideCursor()
        elif isFileSource or isEsriShapefile:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            # get selected key field values
            queryKeys = Utilities.queryKeysOrList(
                selection,
                relation.primaryField,
                keyField.typeName().lower(),
                relation.refField)

            request = QgsFeatureRequest().setFilterExpression(f'{queryKeys}')
            selectedFeats = layer.getFeatures(request)
            for result in selectedFeats:
                mineFeature = QgsFeature()
                mineFeature.setAttributes(list(result))
                mineData.addFeatures([mineFeature])
            QApplication.restoreOverrideCursor()
        else:
            msg = MessageBoxes.translate("Source type not supported yet:")
            MessageBoxes.messageBox(
                self,
                MessageBoxes.WARNING,
                APP_NAME,
                f'{msg} {storageType}')

        mineLayer.commitChanges()
        self.showAttributeTable(mineLayer)
    # /readRelated

    # Override setVisible function to restore window geometry and position
    def setVisible(self, visible):
        if visible:
            super().setVisible(visible)
            # print(f'saveGeometry={self.saveGeometry}')
            if self.savePos:
                self.move(self.savePos)
            if self.saveGeometry:
                self.setGeometry(self.saveGeometry)
        else:
            self.savePos = self.pos()
            self.saveGeometry = self.geometry()
            super().setVisible(visible)
    # /setVisible

    # Action to select all features from attribute table
    def selectAll(self):
        self.ui.tableView.selectAll()
    # /selectAll

    # Action to deselect all features from attribute table
    def selectNone(self):
        self.activeLayer.removeSelection()
    # /selectNone

    # Action to copy selected features from attribute table into clipboard
    def copyTable(self):
        copy_text = ''
        for c in range(self.ui.tableView.horizontalHeader().count()):
            if c > 0:
                copy_text += '\t'
            copy_text += '"' + self.tableModel.headerData(
                c, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) + '"'
        selection = self.activeLayer.selectedFeatures()
        fields = self.activeLayer.fields()
        i = 0
        for feature in selection:
            i += 1
            copy_text += '\n'
            first = True
            for field in fields:
                if first:
                    first = False
                else:
                    copy_text += '\t'
                if feature[field.name()]:
                    if field.typeName() == "String":
                        copy_text += f'"{feature[field.name()]}"'
                    elif field.typeName() == "DateTime":
                        d = feature[field.name()].toPyDateTime()
                        copy_text += f'{d:"%Y-%m-%d %H:%M:%S%z"}'
                    elif field.typeName() == "Date":
                        d = feature[field.name()].toPyDate()
                        copy_text += f'{d:%Y-%m-%d}'
                    elif field.typeName() == "Time":
                        d = feature[field.name()].toPyTime()
                        copy_text += f'{d:%H:%M:%S%z}'
                    else:
                        copy_text += f'{feature[field.name()]}'
        copy_text += '\n'
        QApplication.clipboard().setText(copy_text)
        msg = MessageBoxes.translate(f"{i} features copied to clipboard.")
        MessageBoxes.messageBox(
            self,
            MessageBoxes.INFORMATION,
            APP_NAME,
            msg)
    # /copyTable

    # Action to select selected features from attribute table on map layer
    def selectMap(self):
        if not self.activeMapLayer.isSpatial():
            return
        try:
            self.iface.setActiveLayer(self.activeMapLayer)
            QgsProject.instance().layerTreeRoot().findLayer(
                self.activeMapLayer.id()).setItemVisibilityChecked(True)
            self.activeMapLayer.removeSelection()
            selection = self.activeLayer.selectedFeatures()
            fields = self.activeMapLayer.fields()
            pks = self.activeMapLayer.primaryKeyAttributes()
            keyName = Utilities.findPrimaryKey(fields, pks)
            for feature in selection:
                id = feature[keyName]
                # print(f'\t{keyName}={id}')
                self.activeMapLayer.select(id)
            # if self.activeMapLayer.name() != self.activeLayerName:
            #     self.iface.mapCanvas().zoomToSelected(self.activeMapLayer)
            self.iface.mapCanvas().zoomToSelected(self.activeMapLayer)
        except () as err:
            msg = MessageBoxes.translate("Error viewing map features:")
            MessageBoxes.messageBox(
                self,
                MessageBoxes.WARNING,
                APP_NAME,
                f'{msg}\n{err}')
    # /selectMap

    # Action to display a query form for the active layer
    def showQueryForm(self):
        # self.showQueryForm()
        self.attribute_form = SQLDBMineDialog(
            self, self.iface, self.activeLayer)
        self.attribute_form.init(self.cid, self.level)
    # /showQueryForm

    # Trigger action when selection from attribute table changes
    def selectionChanged(self, fids):
        # print(f"selectionChanged {fids}")
        self.updateStatus()
    # /selectionChanged

    # Trigger action to select/deselect whole row from attribute table
    def tableClicked(self, index=None):
        id = self.tableFilterModel.rowToId(index)
        # print(f'clicked ({row}, {index.column()}) feature id ({id})')
        if Utilities.isFeatureSelected(self.activeLayer, id):
            self.activeLayer.deselect(id)
        else:
            self.activeLayer.select(id)
    # /tableClicked

    # Update statusbar with selection count and total count from attribute table
    def updateStatus(self):
        msg = f'{self.activeLayer.selectedFeatureCount()}' \
            ' features selected out of ' \
            f'{self.activeLayer.featureCount()}'
        self.statuslabel.setText(MessageBoxes.translate(msg))
    # /updateStatus

    def showAttributeTable(self, mineLayer):
        """showAttributeTable
        Action to open new attribute table window with relation data for
        selected features

        :param mineLayer: Active layer to start from.
        """
        self.mineLayer = mineLayer
        # self.iface.showAttributeTable(self.mineLayer)
        self.window = SQLDBMineWindow(self, self.iface, self.mineLayer)
        self.setVisible(False)
        self.window.init(
            self.cid, self.level + 1, self.pos(), self.frameGeometry())

#        self.iface.openFeatureForm(mineLayer, QgsFeature(), True)
    # /showAttributeTable

    def updateAttributeTable(self, data):
        """updateAttributeTable
        Action to update attribute table with new data
        """
        self.activeLayer.updateFields()

        self.tableCache = QgsVectorLayerCache(
            self.activeLayer, data.featureCount())
        self.tableModel = QgsAttributeTableModel(self.tableCache)
        self.tableModel.loadLayer()
        self.tableFilterModel = QgsAttributeTableFilterModel(
            self.iface.mapCanvas(),
            self.tableModel)
        self.ui.tableView.setModel(self.tableFilterModel)
        self.updateStatus()
    # /updateAttributeTable

    def getMineLayer(self):
        return self.activeLayer
    # /getMineLayer

    # Action to copy selected rows to clipboard
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if (
            event.key() == Qt.Key.Key_C and (
                event.modifiers() & Qt.KeyboardModifier.ControlModifier)):
            self.copyTable()
        elif (
            event.key() == Qt.Key.Key_A and (
                event.modifiers() & Qt.KeyboardModifier.ControlModifier)):
            self.selectAll()
    # /keyPressEvent

    # Action to display help about dialog
    def aboutApp(self):
        version = Utilities.getMetadata(
            self.metadata, 'general', 'version')
        author = Utilities.getMetadata(
            self.metadata, 'general', 'author')
        about = Utilities.getMetadata(
            self.metadata, 'general', 'about')
        generalLicense = Utilities.getMetadata(
            self.metadata, 'license', 'general')
        env = f'\n<h2>{Utilities.getApptitle(self)}</h2>'
        if version:
            env += f'<b> v.{version}</b><br><br>'
        env += f'Running on host: {platform.node()}<br>'
        env += f'&nbsp;&nbsp;{platform.system()} '
        env += f'v.{platform.release()} '
        env += f'({platform.machine()})<br>'
        env += f'&nbsp;&nbsp;Python v.{sys.version}<br>'
        env += f'&nbsp;&nbsp;Qt v.{QtCore.QT_VERSION_STR}<br>'
        env += f'&nbsp;&nbsp;PyQt v.{QtCore.PYQT_VERSION_STR}<br>'
        env += f'&nbsp;&nbsp;QGIS v.{Qgis.QGIS_VERSION}<br><br>'
        if author:
            env += f'Author: {author}<br><br>'
        if about:
            env += f'<i>{about}</i><br><br>'
        env += f'{generalLicense}<br>'
        icon = Utilities.getPixmap(os.path.join('images', 'icon.png'))
        if icon:
            icon = icon.scaledToWidth(128)
            icon = icon.scaledToWidth(128)
        MessageBoxes.messageBox(
            self,
            MessageBoxes.INFORMATION,
            f'About: {Utilities.getApptitle(self)}',
            env, icon)
    # /aboutApp

    # Action to close attribute table window
    def closeWindow(self):
        self.close()
    # /closeWindow

    # Action to close all attribute table window (exit)
    def closeAll(self):
        self.closeAllWindows = True
        self.close()
    # /closeAll

    # Cleanup before attribute table window closes
    def cleanupWhenWindowClosed(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.activeLayer.selectionChanged.disconnect(self.selectionChanged)
        self.ui.tableView.clicked.disconnect(self.tableClicked)
        self.ui.mineButton.clicked.disconnect(self.readRelated)
        self.ui.selectAllButton.clicked.disconnect(self.selectAll)
        self.ui.selectNoneButton.clicked.disconnect(self.selectNone)
        self.ui.queryButton.clicked.disconnect(self.showQueryForm)
        self.ui.mapButton.clicked.disconnect(self.selectMap)
        self.ui.returnButton.clicked.disconnect(self.closeWindow)
        self.ui.aboutButton.clicked.disconnect(self.aboutApp)
        self.ui.exitButton.clicked.disconnect(self.closeAll)

        layers = QgsProject.instance().mapLayersByName(self.activeLayer.name())
        for layer in layers:
            if layer.name() == self.activeLayer.name():
                QgsProject.instance().removeMapLayer(layer.id())
        layers = QgsProject.instance().mapLayersByName(self.activeLayerName)
        activeLayer = Utilities.findFirst(
            layers,
            lambda layer: layer.name() == self.activeLayerName)
        if activeLayer:
            self.iface.setActiveLayer(activeLayer)
        """
        for layer in layers:
            if layer.name() == self.activeLayerName:
                self.iface.setActiveLayer(layer)
        """
        self.ui.relationsList.clear()

        if self.level > 1 and self.parent:
            if self.closeAllWindows:
                self.parent.closeAll()
            else:
                self.parent.setVisible(True)
        QApplication.restoreOverrideCursor()
        QApplication.restoreOverrideCursor()
    # /cleanupWhenWindowClosed

    # Trigger action for when close event occurs
    def closeEvent(self, event):
        # print(f'close event {self.activeLayer.name()}')
        self.cleanupWhenWindowClosed()
    # /closeEvent
