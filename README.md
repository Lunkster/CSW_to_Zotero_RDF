# CSW_to_Zotero_RDF
To get metadata from geodata catalogues such as the Swedish Lantmäteriet and Länsstyrelser and import them to Zotero is a bit of a hassle. This script can help you with that.
You'll need lxml
'pip install requests lxml'
'python CSW_to_Zotero_RDF.py "https://www.geodata.se/geodataportalen/srv/swe/catalog.search#/metadata/8dc153f5-a26f-40c7-b735-fbe4f1278815" "https://www.geodata.se/geodataportalen/srv/swe/catalog.search#/metadata/9de2cb7a-8162-44d9-9224-385b60ed0aec"'
