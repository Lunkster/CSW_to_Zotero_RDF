# CSW_to_Zotero_RDF
To get metadata from geodata catalogues such as The Swedish National Land Survey Geodata Portal [Lantmäteriets Geodataportal](https://www.geodata.se/geodataportalen/srv/swe/catalog.search#/home) and the County Administrative Boards Geodata Catalogue [Länsstyrelsernas Geodatakatalog](https://ext-geodatakatalog.lansstyrelsen.se/GeodataKatalogen/srv/swe/catalog.search#/home) and import them to Zotero is a bit of a hassle. This script can help you with that.  
It might work on other catalogues with the same format and csw structure, that is the Swedish metadata standard and [TC211](https://www.isotc211.org/2005/gmd/)  

You'll need lxml!

```bash
pip install requests lxml
```
And you can run the script **CSW_to_Zotero_RDF.py** with one or several URLs and they will be saved in a folder called "rdf_output"

```bash
python CSW_to_Zotero_RDF.py "https://www.geodata.se/geodataportalen/srv/swe/catalog.search#/metadata/8dc153f5-a26f-40c7-b735-fbe4f1278815" "https://www.geodata.se/geodataportalen/srv/swe/catalog.search#/metadata/9de2cb7a-8162-44d9-9224-385b60ed0aec"
```
These files that get their name from de GUID such as: "8dc153f5-a26f-40c7-b735-fbe4f1278815.rdf" kan be easily imported in Zotero.  

It will be saved as:  
*Item type:* Dataset  
*author:* Producer  
*title:* Geodata name  
*date:* last date of produced or revised  
*tags:* GIS, geodata and possibly some other from the csw URL 
*abstract:* Summary including geographic extent  
*identifier:* metadata URL  
*rights:* legal constraints

If you use the file for Jupyter **CSW_to_Zotero_RDF.ipynb**, the 4 blocks have to be run in order and the results will be save in the same folder as the spript.
Only one URL at a time can be run.
Jupyter was used for testing mostly
