<!DOCTYPE html>
<html>
<body lang="en-NZ" dir="ltr">
<h2>SQL Database Mine</h2><br/>
<p>
    QGIS Plugin to mine related data from a SQL database server.<br/>
    <br/>
    Designed as a plugin for QGIS version 3.40+ and is QGIS4 ready but yet to be tested.  Works with QGIS 3.44 and Qt6.<br/>
    Python 3.11+<br/>
    Required Python modules should already be installed for QGIS to be working database layers.<br/>
    Supports Qt5 & Qt6<br/>
    <br/>
    Mine data from selected features within a QGIS vector layer.<br/>
    Related data derived from a layer's Relationships and Joins can then be searched by selecting the required relationship.<br/>
    Once related data is searched, you can keep mining deeper with any further relationships.<br/>
    <br/>
    Where a vector layer is stored within a SQL database, the search is executed on the SQL database server, utilising the database indexes for rapid responses.<br/>
    <br/>
    If the related data has GIS features, these can be selected and zoomed into on the QGIS map.  These features may not be visible if there are other layers overlaying.<br/>
    <br/>
    Rows of selected data can be copied into the clipboard for use in other applications.<br/>
    <br/>
    A query form is also included to enable SQL database searches and view the resulting features on the QGIS map.<br/>
    <br/>
    The inbuilt QGIS features to view table data loads and scans the layers full data, which is unusable for large datasets.<br/>
    SQL Database Mine performs the query on the database server and only deals with the resulting dataset.<br/>
    <br/>
    SQL Database Mine has mostly been tested against a MariaDB database.<br/>
    Minimal testing has been performed using ODBC, SqlLite and Postgres.<br/>
    Requires testing on MSSQL and newer versions of Oracle.<br/>
</p>
</body>
</html>
