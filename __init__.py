"""
Initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    from .sql_db_mine import SQLDBMine
    return SQLDBMine(iface)
