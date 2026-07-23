# -*- coding: utf-8 -*-
# Created on : 30/11/2024, 10:10:24 pm
# Author     : Grant Pearson, Eureka Technology Limited

import os
import configparser
import zipfile
from configparser import ConfigParser
from enum import Enum
from urllib.parse import urlsplit
from PIL import Image
from qgis.core import QgsFeature
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import (
    QIcon, QPixmap, QImage)
from qgis.PyQt.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QListWidgetItem, QLabel)

APP_NAME = "SQLDBMine"
DATABASES = ["mysql", "mariadb",
             "mssql",
             "oracle",
             "postgres", "redshift",
             "sqlite", "gpkg",
             "odbc"]
FILESOURCES = ["sqlite", "gpkg",
               "csv"]
MINE_LAYER_PREFIX = 'db_mine_'
STYLESHEET = \
    "QToolButton {" \
    " background-color: #eff0f1; color: black; margin: 1px;" \
    " border-style: outset; border-width: 1px; border-radius: 6px; "\
    " border-left-color: darkgray;" \
    " border-top-color: darkgray;" \
    " border-right-color: black;" \
    " border-bottom-color: black} " \
    "QToolButton:hover {background-color: white; " \
    " border-style: inset; border-width: 2px; border-radius: 6px;" \
    " border-left-color: darkgray;" \
    " border-top-color: darkgray;" \
    " border-right-color: black;" \
    " border-bottom-color: black} " \
    "QToolButton:pressed {background-color: #c4c8cc;" \
    " border-style: inset; border-width: 2px; border-radius: 6px;" \
    " border-left-color: black;" \
    " border-top-color: black;" \
    " border-right-color: lightgray;" \
    " border-bottom-color: lightgray;} " \
    "QPushButton {" \
    " background-color: #eff0f1; color: black; margin: 5px;" \
    " border-style: outset; border-width: 2px; border-radius: 6px; "\
    " border-left-color: darkgray;" \
    " border-top-color: darkgray;" \
    " border-right-color: black;" \
    " border-bottom-color: black;" \
    " min-width: 90px;" \
    " font: Semibold 14px;" \
    " padding: 4px;} " \
    "QPushButton:hover {background-color: white; " \
    " border-style: inset; border-width: 2px; border-radius: 6px;" \
    " border-left-color: darkgray;" \
    " border-top-color: darkgray;" \
    " border-right-color: black;" \
    " border-bottom-color: black} " \
    "QPushButton:pressed {background-color: #c4c8cc;" \
    " border-style: inset; border-width: 2px; border-radius: 6px;" \
    " border-left-color: black;" \
    " border-top-color: black;" \
    " border-right-color: lightgray;" \
    " border-bottom-color: lightgray;} " \
    "QLineEdit {background-color: white; color: black; } " \
    "QLabel {color: black; } " \
    "QMainWindow {background-color: #e0ffe1;} " \
    "QMessageBox {background-color: #e0ffe1;} " \
    "QDialog {background-color: #e0ffe1;} "


# attempt to import Python database modules
try:
    import mariadb
    mysql_connect = mariadb.connect
    HAS_MARIADB = True
    HAS_MYSQL = False
    HAS_PYMYSQL = False
except ImportError:
    HAS_MARIADB = False
    try:
        from MySQLdb import _mysql
        mysql_connect = _mysql.connect
        HAS_MYSQL = True
        HAS_PYMYSQL = False
    except ImportError:
        HAS_MYSQL = False
        try:
            import pymysql
            mysql_connect = pymysql.connect
            HAS_PYMYSQL = True
        except ImportError:
            HAS_PYMYSQL = False

try:
    import sqlite3 as sqlite
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False

try:
    import pymssql
    HAS_MSSQL = True
except ImportError:
    HAS_MSSQL = False

try:
    import oracledb
    HAS_ORACLE = True
except ImportError:
    HAS_ORACLE = False

try:
    import psycopg3 as psycopg
    HAS_PG3 = True
    HAS_PG2 = False
except ImportError:
    HAS_PG3 = False
    try:
        import psycopg2 as psycopg
        HAS_PG2 = True
    except ImportError:
        HAS_PG2 = False

try:
    import pyodbc as pyodbc
    HAS_ODBC = True
except ImportError:
    try:
        import pypyodbc as pyodbc
        HAS_ODBC = True
    except ImportError:
        HAS_ODBC = False


class SourceConfig():
    """ Class to store layer database source connection details.
    """
    """'Type' definition for database server connections.
    To avoid warning of "Possible hardcoded password: 'None'":
        'username' is translated to 'u'
        'password' is translated to 'p'
    """
    sourceConfig = {
        "databasetype": None,
        "u": None,
        "p": None,
        "hostname": None,
        "port": None,
        "databasename": None,
        "tablename": None,
        "path": None
    }

    def __init__(self):
        pass
    # /__init__

    def __str__(self):
        return f'{self.sourceConfig}'
    # /__str__

    # set a key value
    def setKey(self, key, value):
        k = key.lower()
        if k.endswith('type'):
            tp = ('databasetype', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('user') or k == 'usr':
            tp = ('u', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('pass') or k == 'pwd':
            tp = ('p', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('host') or k.startswith('server') or k == 'dsn':
            tp = ('hostname', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('port'):
            tp = ('port', value)
            self.sourceConfig.__setitem__(*tp)
        if k == 'database' or k == 'databasename' or \
           k.startswith('schema') or k.startswith('db'):
            tp = ('databasename', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('table') or k.startswith('view'):
            tp = ('tablename', value)
            self.sourceConfig.__setitem__(*tp)
        if k.startswith('uri') or k.endswith('path'):
            tp = ('path', value)
            self.sourceConfig.__setitem__(*tp)
    # /setKey

    # return the key value
    def get(self, key):
        if key is None:
            return None
        if key == 'username':
            return self.sourceConfig.get('u')
        if key == 'password':
            return self.sourceConfig.get('p')
        return self.sourceConfig.get(key)
    # /get

    def getConfig(self):
        return self.sourceConfig
    # /getConfig

    # clear all key values
    def clearAll(self):
        self.setKey("databasetype", None)
        self.setKey("username", None)
        self.setKey("password", None)
        self.setKey("hostname", None)
        self.setKey("port", None)
        self.setKey("databasename", None)
        self.setKey("tablename", None)
        self.setKey("path", None)
    # /clearAll
# /SourceConfig


class RelationItems(QListWidgetItem):
    """Extension of QListWidgetItem to contain relationship definitions.
    """

    def __init__(self, primaryLayer, primaryField, refLayer, refField, list):
        super(RelationItems, self).__init__(list)
        self.primaryLayer = primaryLayer
        self.primaryField = primaryField
        self.refLayer = refLayer
        self.refField = refField
        super().setText(self.text())
        # print(f'RelationItems = {self.text()}')
    # /__init__

    def __str__(self):
        return self.text()
    # /__str__

    def primaryLayer(self):
        return self.primaryLayer
    # /primaryLayer

    def primaryField(self):
        return self.primaryField
    # /primaryField

    def refLayer(self):
        return self.refLayer
    # /refLayer

    def refField(self):
        return self.refField
    # /refField

    def text(self):
        return f'({self.primaryField}) > {self.refLayer}({self.refField})'
    # /text
# /RelationItems


class MessageBoxes(Enum):
    NONE = 0
    INFORMATION = 1
    WARNING = 2
    QUESTION = 4
    CRITICAL = 8
    ERROR = 8

    def messageBox(parent, style, title, message, icon=None):
        """Display a message box.
        :param type: Message box type from MessageBoxes.INFORMATION,
         MessageBoxes.WARNING, MessageBoxes.CRITICAL
        :type type: int

        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :param title: Message box title.
        :type title: str

        :param message: Message text.
        :type message: str
        """
        QApplication.restoreOverrideCursor()
        msgBox = QMessageBox(parent)
        lines = message.count('<br>')
        if lines > 10:
            w = msgBox.findChild(QLabel, "qt_msgbox_label").width()
            w = int(w + (w * lines / 100))
            msgBox.findChild(QLabel, "qt_msgbox_label").setFixedWidth(w)
        question = False
        if icon:
            msgBox.setIconPixmap(icon)
        else:
            match style:
                case MessageBoxes.INFORMATION:
                    msgBox.setIcon(QMessageBox.Icon.Information)
                case MessageBoxes.WARNING:
                    msgBox.setIcon(QMessageBox.Icon.Warning)
                case MessageBoxes.CRITICAL:
                    msgBox.setIcon(QMessageBox.Icon.Critical)
                case MessageBoxes.QUESTION:
                    msgBox.setIcon(QMessageBox.Icon.Question)
                    question = True
                case _:
                    msgBox.setIcon(QMessageBox.Icon.NoIcon)
        if question:
            msgBox.setStandardButtons(
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.No)
            msgBox.setDefaultButton(QMessageBox.StandardButton.Ok)
            msgBox.setEscapeButton(QMessageBox.StandardButton.No)
        else:
            msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
            msgBox.setDefaultButton(QMessageBox.StandardButton.Ok)
            msgBox.setEscapeButton(QMessageBox.StandardButton.Ok)
        msgBox.setText(message)
        msgBox.setWindowTitle(title)
        returnValue = msgBox.exec()
        return (returnValue == QMessageBox.StandardButton.Ok)
    # /messageBox

    def translate(message):
        """Get the translation for a string using Qt translation API.
        :param message: Text message for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate(APP_NAME, message)
    # /translate
# /MessageBoxes


class Utilities():
    def stylesheet():
        return STYLESHEET
    # /stylesheet

    def getAppname(parent):
        if isinstance(parent, QMainWindow):
            return parent.getAppname()
        else:
            return parent.parent.getAppname()
    # /getAppname

    def getApptitle(parent):
        if isinstance(parent, QMainWindow):
            return Utilities.getMetadata(
                parent.metadata, 'general', 'name')
        else:
            return Utilities.getMetadata(
                parent.parent.metadata, 'general', 'name')
    # /getApptitle

    def readMetadata(parent):
        metaName = 'metadata.txt'
        infoName = 'metainfo.txt'
        metadata = ConfigParser()
        if os.path.isfile(metaName):
            file = open(metaName, 'r', newline='', encoding="utf-8-sig")
            Utilities.readMetadataFile(metadata, file)
            file.close()
            file = open(infoName, 'r', newline='', encoding="utf-8-sig")
            Utilities.readMetadataFile(metadata, file)
            file.close()
        else:
            try:
                (root, ext) = os.path.split(__file__)
                (file, ext) = os.path.splitext(root)
                if ext == '.zip' or ext == '.pyz':
                    with zipfile.ZipFile(root, 'r') as zip:
                        file = zip.open(metaName, 'r')
                        Utilities.readMetadataFile(metadata, file)
                        file.close()
                        file = zip.open(infoName, 'r')
                        Utilities.readMetadataFile(metadata, file)
                        file.close()
                else:
                    (root, f) = os.path.split(__file__)
                    file = open(os.path.join(root, metaName), 'rt')
                    Utilities.readMetadataFile(metadata, file)
                    file.close()
                    file = open(os.path.join(root, infoName), 'rt')
                    Utilities.readMetadataFile(metadata, file)
                    file.close()
            except IOError as err:
                print(f'Failed to open file: {metaName} and {infoName}'
                      f'\n{err}')
        return metadata
    # /readMetadata

    def readMetadataFile(metadata, metaFile):
        try:
            text = metaFile.read()
            if isinstance(text, bytes):
                metadata.read_string(
                    text.decode('utf-8-sig').replace('\n ', '<br> '))
            else:
                metadata.read_string(
                    text.replace('\n ', '<br> '))
        except IOError as err:
            print('Failed to read metadata file:'
                  f'\n{err}')
    # /readMetadataFile

    def getMetadata(metadata, section='DEFAULT', key=None):
        if metadata and key:
            try:
                value = metadata.get(section, key)
            except (configparser.NoSectionError, configparser.NoOptionError):
                return ''
            if value:
                return value
            else:
                return ''
        return ''
    # /getMetadata

    def getPixmap(filename):
        if filename:
            (root, file) = os.path.split(__file__)
            path = os.path.join(root, filename)
            if os.path.isfile(path):
                pixmap = QPixmap(path)
                return pixmap
            else:
                try:
                    (root, ext) = os.path.split(__file__)
                    (file, ext) = os.path.splitext(root)
                    if ext == '.zip' or ext == '.pyz':
                        with zipfile.ZipFile(root, 'r') as zip:
                            iconFile = zip.open(filename)
                            image = Image.open(iconFile)
                            image = image.convert("RGBA")
                            data = image.tobytes("raw", "BGRA")
                            qim = QImage(data, image.width, image.height,
                                         QImage.Format.Format_ARGB32)
                            image.close()
                            iconFile.close()
                            pixmap = QPixmap.fromImage(qim)
                            return pixmap
                except (IOError, AttributeError, TypeError) as err:
                    print(f'Failed to open file: {filename}'
                          f'\n{err}')
        return None
    # /getPixmap

    def getIcon(filename):
        if filename:
            (root, file) = os.path.split(__file__)
            path = os.path.join(root, filename)
            if os.path.isfile(path):
                icon = QIcon(path)
                return icon
            else:
                try:
                    (root, ext) = os.path.split(__file__)
                    (file, ext) = os.path.splitext(root)
                    if ext == '.zip' or ext == '.pyz':
                        with zipfile.ZipFile(root, 'r') as zip:
                            iconFile = zip.open(filename)
                            image = Image.open(iconFile)
                            image = image.convert("RGBA")
                            data = image.tobytes("raw", "BGRA")
                            qim = QImage(data, image.width, image.height,
                                         QImage.Format.Format_ARGB32)
                            image.close()
                            iconFile.close()
                            pixmap = QPixmap.fromImage(qim)
                            icon = QIcon(pixmap)
                            return icon
                except (IOError, AttributeError, TypeError) as err:
                    print(f'Failed to open file: {filename}'
                          f'\n{err}')
        return None
    # /getIcon

    def findFirst(iterable=None, condition=lambda x: True):
        """
        Returns the first item in the `iterable` that
        satisfies the `condition`.

        If the condition is not given, returns the first item of the iterable.

        >>> first( (1,2,3), condition=lambda x: x % 2 == 0)
        2
        >>> first(range(3, 100))
        3
        """
        if iterable:
            if condition:
                try:
                    return next(x for x in iterable if condition(x))
                except StopIteration:
                    pass
            else:
                return iterable[0]
        return None
    # /findFirst

    def isDatabase(storageType):
        """Test if a layer source type is a supported database
        :param storageType: Data source database type.
        :type storageType: str, QString

        :returns: True if database source type is supported.
        :rtype: Boolean
        """
        if storageType:
            if storageType.lower() in DATABASES:
                return True
        return False
    # /isDatabase

    def isFileSource(storageType):
        """Test if a layer source type is a supported database
        :param storageType: Data source database type.
        :type storageType: str, QString

        :returns: True if database source type is supported.
        :rtype: Boolean
        """
        if storageType:
            if storageType.lower() in FILESOURCES:
                return True
        return False
    # /isFileSource

    def extractSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        vector layer source URI
        :param storageType: Data source database type.
        :type storageType: str, QString

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        # print(f'extractSourceURI\nuriComponents:\n\t{uriComponents}')
        if uriComponents:
            # print(f'storageType={storageType} : '
            #       'isDatabase={Utilities.isDatabase(storageType)}')
            if Utilities.isDatabase(storageType):
                if storageType.lower() == "odbc":
                    return Utilities.extractODBCSourceURI(
                        storageType, uriComponents)
                else:
                    return Utilities.extractDatabaseSourceURI(
                        storageType, uriComponents)
            elif Utilities.isFileSource(storageType):
                return Utilities.extractFileSourceURI(
                    storageType, uriComponents)
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        return sourceConfig
    # /extractSourceURI

    def extractODBCSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        ODBC layer source URI
        :param storageType: Data source database type.
        :type storageType: str, QString

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        urlParts = urlsplit(uriComponents["path"])
        username = None
        password = None
        path = uriComponents['databaseName']
        if path is None:
            path = urlParts.path
        sourceConfig.setKey('path', path)
        if path:
            sep = path.find('@')
            length = len(path)
            if sep == 0:
                path = path[1:length]
            elif sep > 0:
                authentication = path[0:sep]
                path = path[sep + 1:length]
                sep = authentication.find('/')
                length = len(authentication)
                if sep == 0:
                    username = authentication[1:length]
                elif sep > 0:
                    username = authentication[0:sep]
                    password = authentication[sep + 1:length]
        sourceConfig.setKey('username', username)
        sourceConfig.setKey('password', password)
        sourceConfig.setKey('databasename', path)
        tableName = uriComponents['layerName']
        sourceConfig.setKey('tablename', tableName)
        if urlParts.hostname:
            sourceConfig.setKey('hostname', urlParts.hostname)
        if urlParts.port:
            sourceConfig.setKey('port', urlParts.port)
        return sourceConfig
    # /extractODBCSourceURI

    def extractDatabaseSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        database layer source URI
        :param storageType: Data source database type.
        :type storageType: str, QString

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        if Utilities.isFileSource(storageType):
            databaseName = uriComponents['path']
            sourceConfig.setKey('databasename', databaseName)
            tableName = uriComponents['layerName']
            sourceConfig.setKey('tablename', tableName)
        else:
            databaseName = uriComponents['databaseName']
            sourceConfig.setKey('databasename', databaseName)
        urlParts = urlsplit(uriComponents["path"])
        path = urlParts.path
        sourceConfig.setKey('path', path)
        if urlParts.username:
            sourceConfig.setKey('username', urlParts.username)
        if urlParts.password:
            sourceConfig.setKey('password', urlParts.password)
        if urlParts.hostname:
            sourceConfig.setKey('hostname', urlParts.hostname)
        if urlParts.port:
            sourceConfig.setKey('port', urlParts.port)
        else:
            sourceConfig.setKey(
                'port', Utilities.defaultPort(storageType.lower()))
        components = path.split(',')
        for component in components:
            if component.find('=') > 0:
                c = component.split('=', 1)
                sourceConfig.setKey(c[0], c[1])
        return sourceConfig
    # /extractDatabaseSourceURI

    def extractFileSourceURI(storageType, uriComponents):
        """Extract database source connection information from a
        file source URI
        :param storageType: Data source database type.
        :type storageType: str, QString

        :param uriComponents: Data source database URI components.
        :type uriComponents: QVariantMap

        :returns: layer source URI split into connection components.
        :rtype: SourceConfig
        """
        sourceConfig = SourceConfig()
        sourceConfig.clearAll()
        sourceConfig.setKey('databasetype', storageType)
        databaseName = uriComponents['path']
        sourceConfig.setKey('databasename', databaseName)
        urlParts = urlsplit(uriComponents["path"])
        path = urlParts.path
        sourceConfig.setKey('path', path)
        return sourceConfig
    # /extractFileSourceURI

    def defaultPort(storageType):
        """Get default port number for database tcp connection.
        :param storageType: Storage database type.
        :type storageType: str

        :returns: Default port number for database type.
        :rtype: str
        """
        if storageType == "mysql":
            return '3306'
        if storageType == "mariadb":
            return '3306'
        if storageType == "mssql":
            return '1433'
        if storageType == "oracle":
            return '1521'
        if storageType == "postgres":
            return '5432'
        if storageType == "redshift":
            return '5439'
        return None
    # /defaultPort

    def queryFieldList(fields):
        """Get list of table fields for SQL SELECT statement
        and allows some formatting of date and numeric type fields for
        attribute table compatibility
        :param fields: List of attribute fields for layer.
        :type fields: QgsFields

        :returns: Comma delimited list of field names with aliases of
        converted fields.
        :rtype: str
        """
        # get attribute fields
        # print('Fields:')
        queryFields = None
        for field in fields:
            name = field.name()
            indx = fields.indexOf(name)
            if fields.fieldOrigin(indx) == fields.OriginProvider:
                # print(f'Field: {field}')
                fieldType = field.typeName().lower()
                isNumber = fieldType == 'real' \
                    or fieldType == 'double' \
                    or fieldType.startswith('float')
                if fieldType == 'datetime':
                    if queryFields:
                        queryFields = f'{queryFields}, date_format(' \
                            f'{field.name()}, "%Y-%m-%dT%H:%i:%s.%f") ' \
                            f'{field.name()}'
                    else:
                        queryFields = 'date_format(' \
                            f'{field.name()}, "%Y-%m-%dT%H:%i:%s.%f") ' \
                            f'{field.name()}'
                elif fieldType == 'date':
                    if queryFields:
                        queryFields = f'{queryFields}, date_format(' \
                            f'{field.name()}, "%Y-%m-%d") {field.name()}'
                    else:
                        queryFields = 'date_format(' \
                            f'{field.name()}, "%Y-%m-%d") {field.name()}'
                elif fieldType == 'time':
                    if queryFields:
                        queryFields = f'{queryFields}, date_format(' \
                            f'{field.name()}, "%H:%i:%s.%f") {field.name()}'
                    else:
                        queryFields = 'date_format(' \
                            f'{field.name()}, %H:%i:%s.%f") {field.name()}'
                elif isNumber:
                    if queryFields:
                        queryFields = f'{queryFields}, ' \
                            f'format({field.name()}, ' \
                            f'{field.precision()}) {field.name()}'
                    else:
                        queryFields = f'format({field.name()}, ' \
                            f'{field.precision()}) {field.name()}'
                else:
                    if queryFields:
                        queryFields = f'{queryFields}, {field.name()}'
                    else:
                        queryFields = field.name()
        return queryFields
    # /queryFieldList

    def findPrimaryKey(fields, pks=None):
        """Take a best stab at which field is the feature ID or primary key
        without looking up the database server dictionary schema.
        Composite primary keys not supported
        :param fields: List of attribute fields for layer.
        :type fields: QgsFields
        :param pks: List of primary key field indexes (uses only first value).
        :type pks: int

        :returns: Name of field assumed to be the feature ID or primary key.
        :rtype: str
        """
        primaryKey = None
        if pks:
            primaryKey = fields.field(pks[0]).name()
        else:
            i = fields.lookupField('OGR_FID')
            if i < 0:
                i = fields.lookupField('ctid')
            if i < 0:
                i = fields.lookupField('oid')
            if i < 0:
                i = fields.lookupField('id')
            if i >= 0:
                primaryKey = fields.at(i).name()
            else:
                pk = Utilities.findFirst(
                    fields,
                    lambda field: field.typeName().lower().startswith('int'))
                if not pk:
                    pk = Utilities.findFirst(
                        fields,
                        lambda field: any(field.name().lower().endswith('id'),
                                          field.name().lower().endswith('index')
                                          ))
                if not pk:
                    pk = Utilities.findFirst(
                        fields,
                        lambda field: any(field.name().lower().endswith('no'),
                                          field.name().lower().endswith('num')
                                          ))
                if pk:
                    primaryKey = pk.name()
                """
                for field in fields:
                    if not primaryKey \
                       and field.typeName().lower().startswith('int'):
                        primaryKey = field.name()
                if not primaryKey:
                    for field in fields:
                        isIndex = field.name().lower().endswith('id') \
                            or field.name().lower().endswith('index')
                        isprimaryKey = not primaryKey and isIndex
                        if isprimaryKey:
                            primaryKey = field.name()
                if not primaryKey:
                    for field in fields:
                        isIndex = field.name().lower().endswith('no') \
                            or field.name().lower().endswith('num')
                        isprimaryKey = not primaryKey and isIndex
                        if isprimaryKey:
                            primaryKey = field.name()
                """
        return primaryKey
    # /findPrimaryKey

    def querySelectionFeatureIDs(selection):
        """Get list of features IDs from a layer selection.
        :param selection: List of selected features from a layer.
        :type selection: QgsFeatureList

        :returns: Comma delimited list of feature IDs.
        :rtype: str
        """
        queryKeys = None
        for feature in selection:
            if not queryKeys:
                queryKeys = f'{feature.id()}'
            else:
                queryKeys = f'{queryKeys}, {feature.id()}'
        return queryKeys
    # /querySelectionFeatureIDs

    def queryKeysList(selection, keyName, fieldType):
        """Get list of key values from a layer selection for a SQL where clause.
        :param selection: List of selected features from a layer.
        :type selection: QgsFeatureList

        :param keyName: Name of attribute key field from a layer.
        :type keyName: str

        :param fieldType: Key field type name (integer and string supported).
        :type fieldType: str

        :returns: Comma delimited list of key values.
        :rtype: str
        """
        queryKeys = None
        for feature in selection:
            id = feature[keyName]
            if fieldType == 'string':
                if not queryKeys:
                    queryKeys = f'"{id}"'
                elif Utilities.isDistinctKey(queryKeys, f'"{id}"', ','):
                    queryKeys = f'{queryKeys},"{id}"'
            else:
                if not queryKeys:
                    queryKeys = f'{id}'
                elif Utilities.isDistinctKey(queryKeys, f'{id}', ','):
                    queryKeys = f'{queryKeys},{id}'
        return queryKeys
    # /queryKeysList

    def queryKeysOrList(selection, keyName, fieldType, refField):
        """Get list of key values from a layer selection for a layer filter.
        :param selection: List of selected features from a layer.
        :type selection: QgsFeatureList

        :param keyName: Name of attribute key field from a layer.
        :type keyName: str

        :param fieldType: Key field type name (integer and string supported).
        :type fieldType: str

        :param keyName: Name of key field from a referenced layer.
        :type keyName: str

        :returns: List of <key name> "OR" <key values>
        :rtype: str
        """
        queryKeys = None
        for feature in selection:
            id = feature[keyName]
            if fieldType == 'string':
                if not queryKeys:
                    queryKeys = f"{refField}='{id}'"
                elif Utilities.isDistinctKey(queryKeys, f"'{id}'", '='):
                    queryKeys = f"{queryKeys} OR {refField}='{id}'"
            else:
                if not queryKeys:
                    queryKeys = f'{refField}={id}'
                elif Utilities.isDistinctKey(queryKeys, f'{id}', '='):
                    queryKeys = f'{queryKeys} OR {refField}={id}'
        return queryKeys
    # /queryKeysOrList

    def isDistinctKey(queryKeys, id, delimiter):
        """Test if an id is not found in queryKeys
        :param queryKeys: Data source database type.
        :type queryKeys: str

        :param id: Feature ID.
        :type id: str

        :param delimiter: List delimiter string (e.g. "," or "=").
        :type delimiter: str

        :returns: True if id is not found in queryKeys.
        :rtype: Boolean
        """
        # print(f'isDistinctKey {queryKeys}; {id}; {delimiter}')
        if not queryKeys:
            return True
        if queryKeys == id:
            return False
        keys = delimiter + queryKeys + delimiter
        i = keys.find(delimiter + id + delimiter)
        if i < 0:
            i = keys.find(delimiter + id + ' ')
        if i < 0:
            return True
        elif i == 0:
            return False
        if queryKeys[i - 1] == delimiter:
            return False
        return True
    # /isDistinctKey

    def isFeatureSelected(layer, id):
        """Test if a given feature ID is already selected
        :param layer: Vector layer of feature.
        :type layer: QgsVectorLayer

        :param id: Feature ID.
        :type id: int

        :returns: True if feature with given ID is selected.
                  False if not selected or not found.
        :rtype: Boolean
        """
        if not layer or not id:
            return False
        selection = layer.selectedFeatures()
        fid = Utilities.findFirst(
            selection,
            lambda feature: feature.id() == id)
        if fid == id:
            return True
        """
        for feature in selection:
            fid = feature.id()
            if fid == id:
                return True
        """
        return False
    # /isFeatureSelected

    def convertFieldType(value, type):
        """Convert from database field type.
        :param value: Field value.
        :type value: object

        :param type: Field type.
        :type type: str

        :returns: Value converted to python type.
        :rtype: object
        """
        if not value:
            return
        if type.lower().startswith('int'):
            newValue = int(value)
        elif type.lower().startswith('dec'):
            newValue = float(value)
        elif type.lower().startswith('real'):
            newValue = float(value)
        elif type.lower().startswith('float'):
            newValue = float(value)
        else:
            newValue = value
        return newValue
    # /convertFieldType

    def readDatabase(parent, sourceConfig, fields, sql, data):
        """Read data from database server.
        Calls readDatabase for each supported database.
        :param parent: Parent application window or dialog.
        :type parent: QtWidget

        :param sourceConfig: Database connection components.
        :type sourceConfig: SourceConfig

        :param fields: List of attribute fields for layer.
        :type fields: QgsFields

        :param sql: SQL query statement.
        :type sql: str

        :param data: Vector layer data provider.
        :type data: QgsVectorDataProvider

        :returns: Vector layer data provider.
        :rtype: QgsVectorDataProvider
        """
        if data:
            data.truncate()
        storageType = sourceConfig.get("databasetype")
        isMysql = storageType.lower() == "mysql" \
            or storageType.lower() == "mariadb"
        isMssql = storageType.lower() == "mssql"
        isSqlite = storageType.lower() == "sqlite" \
            or storageType.lower() == "gpkg"
        isOracle = storageType.lower() == "oracle"
        isPostgres = storageType.lower() == "postgres" \
            or storageType.lower() == "redshift"
        isODBC = storageType.lower() == "odbc"
        if isMysql:
            if HAS_MARIADB or HAS_MYSQL or HAS_PYMYSQL:
                mineData = readDatabaseMysql(
                    parent,
                    sourceConfig,
                    fields,
                    sql,
                    data)
            else:
                mineData = data
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    APP_NAME,
                    MessageBoxes.translate(
                        "No Python module for MySQL/MariaDB Connector found.\n"
                        "Install Python MySQL/MariaDB connector module."))
        elif isSqlite:
            if HAS_SQLITE:
                mineData = readDatabaseSqlite(
                    parent,
                    sourceConfig,
                    fields,
                    sql,
                    data)
            else:
                mineData = data
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    APP_NAME,
                    MessageBoxes.translate(
                        "No Python module for SQLite found.\n"
                        "Install Python sqlite3 module."))
        elif isMssql:
            if HAS_MSSQL:
                mineData = readDatabaseMSSQL(
                    parent,
                    sourceConfig,
                    fields,
                    sql,
                    data)
            else:
                mineData = data
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    APP_NAME,
                    MessageBoxes.translate(
                        "No Python module for Microsoft SQL Server Connector "
                        "found.\n"
                        "Install Python pymssql module."))
        elif isOracle:
            if HAS_ORACLE:
                mineData = readDatabaseOracle(
                    parent,
                    sourceConfig,
                    fields,
                    sql,
                    data)
            else:
                mineData = data
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    APP_NAME,
                    MessageBoxes.translate(
                        "No Python module for Oracle Connector found.\n"
                        "Install Python cx_Oracle module."))
        elif isPostgres:
            if HAS_PG2 or HAS_PG3:
                mineData = readDatabasePostgres(
                    parent,
                    sourceConfig,
                    fields,
                    sql,
                    data)
            else:
                mineData = data
                msg = MessageBoxes.translate(
                    "No Python module for Postgres Connector found.\n"
                    "Install Python psycopg2 or psycopg3 module.")
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    APP_NAME,
                    msg)
        elif isODBC:
            if HAS_ODBC:
                mineData = readDatabaseODBC(
                    parent,
                    sourceConfig,
                    fields,
                    sql,
                    data)
            else:
                mineData = data
                MessageBoxes.messageBox(
                    parent,
                    MessageBoxes.WARNING,
                    APP_NAME,
                    MessageBoxes.translate(
                        "No Python module for ODBC Connector found.\n"
                        "Install Python pyodbc module."))
        else:
            mineData = data
            msg = MessageBoxes.translate("Database source type unsupported:")
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.INFORMATION,
                APP_NAME,
                f'{msg} {storageType}')
        return mineData
    # /readDatabase
# /Utilities


def readDatabaseMysql(parent, sourceConfig, fields, sql, mineData):
    """Read data from MySQL/MariaDB database server.
    Called from readDatabase.
    """
    config = {
        "host": sourceConfig.get("hostname"),
        "port": int(sourceConfig.get("port")),
        "user": sourceConfig.get("username"),
        "password": sourceConfig.get("password"),
        "database": sourceConfig.get("databasename")
    }
    try:
        # print(f'Try MariaDB/MySQL Connector {config}...')
        cnx = mysql_connect(**config)
        # print('Connected to MariaDB/MySQL')
        try:
            if HAS_MYSQL:
                cnx.query(f"""{sql}""")
                r = cnx.store_result()
                results = r.fetch_row(r.rowcount, 1)
                for result in results:
                    newResult = []
                    for key in result:
                        value = result.get(key)
                        # print(f'{key} : {value}')
                        if value:
                            value = value.decode('utf-8')
                        field = fields.field(key)
                        value = Utilities.convertFieldType(
                            value, field.typeName())
                        newResult.append(value)
                        tp = (key, value)
                        result.__setitem__(*tp)
                        # print(f'{key} : {result.get(key)}')
                    mineFeature = QgsFeature()
                    mineFeature.setAttributes(newResult)
                    mineData.addFeatures([mineFeature])
                    # print(f'{newResult}')
            else:
                cur = cnx.cursor()
                cur.execute(sql)
                for result in cur:
                    # print(f'{result}')
                    mineFeature = QgsFeature()
                    mineFeature.setAttributes(list(result))
                    mineData.addFeatures([mineFeature])
                cur.close()
        except () as err:
            msg = MessageBoxes.translate(
                "Failed to read from MariaDB/MySQL database:")
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                APP_NAME,
                f'{msg}\n{err}')
        cnx.close()
    except () as err:
        msg = MessageBoxes.translate(
            "Failed to connect to MariaDB/MySQL database:")
        MessageBoxes.messageBox(
            parent,
            MessageBoxes.WARNING,
            APP_NAME,
            f'{msg}\n{err}')
    return mineData
# /readDatabaseMysql


def readDatabaseSqlite(parent, sourceConfig, fields, sql, mineData):
    """Read data from Sqlite database server.
    Called from readDatabase.
    """
    try:
        cnx = sqlite.connect(sourceConfig.get("path"))
        # print('Connected to SQLite')
        try:
            cur = cnx.cursor()
            cur.execute(sql)
            for result in cur:
                mineFeature = QgsFeature()
                mineFeature.setAttributes(list(result))
                mineData.addFeatures([mineFeature])
                # print(f'{result}')
            cur.close()
        except () as err:
            msg = MessageBoxes.translate("Failed to read from SQLite database:")
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                APP_NAME,
                f'{msg}\n{err}')
        cnx.close()
    except () as err:
        msg = MessageBoxes.translate("Failed to connect to SQLite database:")
        MessageBoxes.messageBox(
            parent,
            MessageBoxes.WARNING,
            APP_NAME,
            f'{msg}\n{err}')
    return mineData
# /readDatabaseSqlite


def readDatabaseMSSQL(parent, sourceConfig, fields, sql, mineData):
    """Read data from MSSQL database server.
    Called from readDatabase.
    """
    try:
        cnx = pymssql.connect(
            host=sourceConfig.get("hostname"),
            port=int(sourceConfig.get("port")),
            user=sourceConfig.get("username"),
            password=sourceConfig.get("password"),
            database=sourceConfig.get("databasename"))
        # print('Connected to SQL Server')
        try:
            cur = cnx.cursor()
            cur.execute(sql)
            results = cur.fetchall()
            for result in results:
                mineFeature = QgsFeature()
                mineFeature.setAttributes(list(result))
                mineData.addFeatures([mineFeature])
                # print(f'{result}')
            cur.close()
        except () as err:
            msg = MessageBoxes.translate(
                "Failed to read from SQL Server database:")
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                APP_NAME,
                f'{msg}\n{err}')
        cnx.close()
    except () as err:
        msg = MessageBoxes.translate(
            "Failed to connect to SQL Server database:")
        MessageBoxes.messageBox(
            parent,
            MessageBoxes.WARNING,
            APP_NAME,
            f'{msg}\n{err}')
    return mineData
# /readDatabaseMSSQL


def readDatabaseOracle(parent, sourceConfig, fields, sql, mineData):
    """Read data from Oracle database server.
    Called from readDatabase.
    """
    try:
        # cs=f'''(description = (retry_count=20)(retry_delay=3)
        #       (address=(protocol=tcps)
        #            (port={sourceConfig.get("port")})
        #            (host={sourceConfig.get("hostname")}))
        #            (connect_data=(service_name=xxx.adb.oraclecloud.com))
        #            (security=(ssl_server_dn_match=yes)))'''
        cnx = oracledb.connect(
            user=sourceConfig.get("username"),
            password=sourceConfig.get("password"),
            dsn=sourceConfig.get("hostname"))
        # print('Connected to Oracle')
        try:
            cur = cnx.cursor()
            cur.execute(sql)
            results = cur.fetchall()
            for result in results:
                mineFeature = QgsFeature()
                mineFeature.setAttributes(list(result))
                mineData.addFeatures([mineFeature])
                # print(f'{result}')
            cur.close()
        except () as err:
            msg = MessageBoxes.translate("Failed to read from Oracle database:")
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                APP_NAME,
                f'{msg}\n{err}')
        cnx.close()
    except () as err:
        msg = MessageBoxes.translate("Failed to connect to Oracle database:")
        MessageBoxes.messageBox(
            parent,
            MessageBoxes.WARNING,
            APP_NAME,
            f'{msg}\n{err}')
    return mineData
# /readDatabaseOracle


def readDatabasePostgres(parent, sourceConfig, fields, sql, mineData):
    """Read data from Postgres/Redshift database server.
    Called from readDatabase.
    """
    config = {
        "user": sourceConfig.get("username"),
        "password": sourceConfig.get("password"),
        "host": sourceConfig.get("hostname"),
        "port": int(sourceConfig.get("port")),
        "dbname": sourceConfig.get("databasename")
    }
    try:
        cnx = psycopg.connect(**config)
        # print('Connected to Postgres/Redshift')
        try:
            cur = cnx.cursor()
            cur.execute(sql)
            results = cur.fetchmany(cur.rowcount)
            for result in results:
                mineFeature = QgsFeature()
                mineFeature.setAttributes(list(result))
                mineData.addFeatures([mineFeature])
                # print(f'{result}')
            cur.close()
        except () as err:
            msg = MessageBoxes.translate(
                "Failed to read from Postgres/Redshift database:")
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                APP_NAME,
                f'{msg}\n{err}')
        cnx.close()
    except () as err:
        msg = MessageBoxes.translate(
            "Failed to connect to Postgres/Redshift database:")
        MessageBoxes.messageBox(
            parent,
            MessageBoxes.WARNING,
            APP_NAME,
            f'{msg}\n{err}')
    return mineData
# /readDatabasePostgres


def readDatabaseODBC(parent, sourceConfig, fields, sql, mineData):
    """Read data from ODBC database.
    Called from readDatabase.
    """

    try:
        host = sourceConfig.get("hostname")
        port = sourceConfig.get("port")
        database = sourceConfig.get("databasename")
        user = sourceConfig.get("username")
        password = sourceConfig.get("password")

        connectionString = f'DSN={database}'
        if host:
            connectionString = f'{connectionString};SERVER={host}'
        if port:
            connectionString = f'{connectionString};Port={port}'
        # if database:
        #     connectionString = f'{connectionString};DATABASE={database}'
        if user:
            connectionString = f'{connectionString};UID={user}'
        if password:
            connectionString = f'{connectionString};PWD={password}'
        cnx = pyodbc.connect(
            connectionString,
            autocommit=False,
            attrs_before=None,
            encoding='utf-16le')
        try:
            cur = cnx.cursor()
            cur.execute(sql)
            results = cur.fetchall()
            for result in results:
                mineFeature = QgsFeature()
                mineFeature.setAttributes(list(result))
                mineData.addFeatures([mineFeature])
                # print(f'{result}')
            cur.close()
        except () as err:
            msg = MessageBoxes.translate("Failed to read from ODBC database:")
            MessageBoxes.messageBox(
                parent,
                MessageBoxes.WARNING,
                APP_NAME,
                f'{msg}\n{err}')
        cnx.close()
    except () as err:
        msg = MessageBoxes.translate("Failed to connect to ODBC database:")
        MessageBoxes.messageBox(
            parent,
            MessageBoxes.WARNING,
            APP_NAME,
            f'{msg}\n{err}')
    return mineData
# /readDatabaseODBC
