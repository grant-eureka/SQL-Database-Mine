# -*- coding: utf-8 -*-
# Created on : 12/11/2024, 9:19:29 pm
# Author     : Grant Pearson, Eureka Technology Limited

import os

from .sql_db_mine_window import SQLDBMineWindow
from .sql_db_mine_utilities import (
    APP_NAME, MINE_LAYER_PREFIX, MessageBoxes, Utilities)
from qgis.core import (
    QgsProject, QgsProviderRegistry, QgsFeature)
from qgis.core import (
    QgsMapLayer, QgsVectorLayer)
from qgis.PyQt.QtCore import (
    Qt, QObject)
from qgis.PyQt.QtGui import (
    QIcon)
from qgis.PyQt.QtWidgets import (
    QApplication, QAction)


class SQLDBMine(QObject):
    """
    QGIS Plugin Implementation.
    """

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        super(SQLDBMine, self).__init__(iface)
        self.iface = iface
        self.parent = self.iface.mainWindow()
        self.level = 1
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # Declare instance attributes
        self.actions = []
        self.menu = "SQL Database &Mine"
        self.toolbar = self.iface.addToolBar("SQL Database Mine")
        self.toolbar.setOrientation(Qt.Orientation.Horizontal)
        self.toolbar.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        self.toolbar.setObjectName("SQL Database Mine")
        self.cid = 0

    def add_action(
            self,
            icon_path,
            text,
            callback,
            checkable=False,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToDatabaseMenu(
                self.menu,
                action)

        self.actions.append(action)
        return action

    def initGui(self):
        # Create the menu entries and toolbar icons inside the QGIS GUI.
        icon_plugin = '{}{}'.format(
            os.path.dirname(__file__),
            os.path.join(os.sep, 'images', 'icon.png'))
        self.add_action(
            icon_plugin,
            text="SQL Database &Mine",
            checkable=False,
            callback=self.readSelected,
            add_to_toolbar=True,
            parent=self.iface.mainWindow())

    def unload(self):
        # Removes the plugin menu item and icon from QGIS GUI.
        for action in self.actions:
            self.iface.removePluginDatabaseMenu(
                "SQL Database &Mine",
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def run(self):
        print('Hi Netbeans')

    def readSelected(self):
        # print('\n\n*****************************\nSQLDBMine')
        activeLayer = self.iface.activeLayer()
        if activeLayer is None:
            MessageBoxes.messageBox(
                self.parent,
                MessageBoxes.INFORMATION,
                APP_NAME,
                MessageBoxes.translate(
                    "Select active vector layer first."))
            return
        if activeLayer.type() != QgsMapLayer.LayerType.VectorLayer:
            MessageBoxes.messageBox(
                self.parent,
                MessageBoxes.INFORMATION,
                APP_NAME,
                MessageBoxes.translate(
                    "Vector layers only are supported.\n"
                    "Select active vector layer."))
            return
        selection = activeLayer.selectedFeatures()
        selectedFeatureCount = activeLayer.selectedFeatureCount()
#        print(f'Features selected: {n}')
        if selectedFeatureCount == 0:
            MessageBoxes.messageBox(
                self.parent,
                MessageBoxes.INFORMATION,
                APP_NAME,
                MessageBoxes.translate(
                    "No features selected in active vector layer.\n"
                    "Query Feature Form available to select features."))
            # return

#        print('active layer sourceName: '
#              f'{activeLayer.sourceName()}')
#        print('active layer storageType: '
#              f'{activeLayer.storageType()}')
#        print('active layer primaryKeyAttributes: '
#              f'{activeLayer.primaryKeyAttributes()}')
#        print('active layer dataProvider name: '
#              f'{activeLayer.dataProvider().name()}')
#        print('active layer dataProvider providerProperty: '
#              f'{activeLayer.dataProvider().providerProperty()}')
#        print('active layer dataProvider description: '
#              f'{activeLayer.dataProvider().description()}')
#        print('active layer dataProvider dataSourceUri: '
#              f'{activeLayer.dataProvider().dataSourceUri()}')
#        print('active layer dataProvider uri: '
#              f'{activeLayer.dataProvider().uri()}')

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        # set unique process call ID
        self.cid = self.cid + 1

        # get active data source
        storageType = activeLayer.storageType()
        if not Utilities.isDatabase(storageType):
            storageType = 'other'
        uriComponents = QgsProviderRegistry.instance().decodeUri(
            activeLayer.dataProvider().name(),
            activeLayer.source())
        sourceConfig = Utilities.extractSourceURI(
            storageType,
            uriComponents)
#        print(f'sourceConfig: {sourceConfig}')

        # get attribute fields
        fields = activeLayer.fields()
#        print('Fields:')

        # Create new memory vector layer
        mineLayerName = f'{MINE_LAYER_PREFIX}{activeLayer.name()} ' \
            f'[{self.cid}-{self.level}]'
        layers = QgsProject.instance().mapLayersByName(mineLayerName)
        for layer in layers:
            isMineLayer = layer.name() == mineLayerName \
                and layer.dataProvider().name() == 'memory'
            if isMineLayer:
                # print(f'found old {mineLayerName} : '
                #       f'{layer.dataProvider().name()}')
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

        # Read selected feature attributes from non-database layer
        # and insert into new memory vector layer
        if not Utilities.isDatabase(storageType):
            selection = activeLayer.selectedFeatures()
            selectedFeatureCount = activeLayer.selectedFeatureCount()
            # print(f'Features selected: {selectedFeatureCount}')
            mineLayer.startEditing()
            for feature in selection:
                mineFeature = QgsFeature()
                mineFeature.setAttributes(feature.attributes())
                mineData.addFeatures([mineFeature])
            mineLayer.commitChanges()
        # Read selected feature attributes from database
        # and insert into new memory vector layer
        elif selectedFeatureCount == 0:
            pass
        else:
            # compose sql query
            queryFields = Utilities.queryFieldList(fields)
            tablename = sourceConfig.get("tablename")
            pks = activeLayer.primaryKeyAttributes()
            primaryKey = Utilities.findPrimaryKey(fields, pks)
            if activeLayer.isSpatial():
                queryKeys = Utilities.querySelectionFeatureIDs(selection)
            else:
                keyField = activeLayer.fields().field(primaryKey)
                queryKeys = Utilities.queryKeysList(
                    selection,
                    primaryKey,
                    keyField.typeName().lower())
            sql = f'SELECT {queryFields}\nFROM {tablename} ' \
                  f'\nWHERE {primaryKey} IN ({queryKeys});'
            # print(sql)
            """
            postgres example
            from psycopg2 import sql as pysql
            sql = pysql.SQL(
                '""SELECT {queryFields}\nFROM {tablename} '
                '\nWHERE {primaryKey} IN ({queryKeys});""'.format(
                    tablename=pysql.Identifier(tablename),
                    primaryKey=pysql.Identifier(primaryKey)))
            """

            mineLayer.startEditing()
            mineData = Utilities.readDatabase(
                self.parent, sourceConfig,
                fields,
                sql,
                mineData)
            mineLayer.commitChanges()

        QApplication.restoreOverrideCursor()
        self.showAttributeTable(mineLayer)

    def showAttributeTable(self, mineLayer):
        """showAttributeTable
        Action to open new attribute table window with relation data for
        selected features

        :param mineLayer: Active layer to start from.
        """
        self.window = SQLDBMineWindow(self.parent, self.iface, mineLayer)
        self.window.init(self.cid, self.level)
