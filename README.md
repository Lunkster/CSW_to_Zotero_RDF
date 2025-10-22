# CSW_to_Zotero_RDF
To get metadata from geodata catalogues such as the Swedish Lantmäteriet and Länsstyrelser and import them to Zotero is a bit of a hassle. This script can help you with that.  
You'll need lxml!
```markdown
```console
pip install requests lxml
```
And you can run the script with one or several URLs and they will be saved in a folder called "rdf_output"
```markdown
```console
python CSW_to_Zotero_RDF.py "https://www.geodata.se/geodataportalen/srv/swe/catalog.search#/metadata/8dc153f5-a26f-40c7-b735-fbe4f1278815" "https://www.geodata.se/geodataportalen/srv/swe/catalog.search#/metadata/9de2cb7a-8162-44d9-9224-385b60ed0aec"
```
These files that get their name from de GUID such as: "8dc153f5-a26f-40c7-b735-fbe4f1278815.rdf" kan be easily imported in Zotero.  

It will be saved as:  
Item type: Dataset  
author: Producer  
title: Geodata name  
date: last date of produced or revised  
tags: GIS, geodata and possibly some other från the csw  
abstract: Summary including geographic extent  
identifier: metadata URL  
rights: legal constraints

