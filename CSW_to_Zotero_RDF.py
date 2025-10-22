# CSW_to_Zotero_RDF.py - KOMPLETT SKRIPT MED ALLA FIXAR

import requests
import re
import uuid
import sys
import datetime
import os
from lxml import etree as ET
from urllib.parse import urlparse, parse_qs

# --- HJÄLPFUNKTIONER ---

def clean_tag(element):
    """Extraherar text från ett lxml-element och rensar upp."""
    return element.text if element is not None and element.text else ''

def sanitize_text_single_line(text):
    """Rensar text från inledande/avslutande blanksteg och konverterar till en rad."""
    if text is None:
        return ''
    return ' '.join(text.split()).strip()

def sanitize_text_preserve_newlines(text):
    """Rensar text men bevarar radbrytningar för abstract-fältet."""
    if text is None:
        return ''
    lines = [line.strip() for line in text.splitlines()]
    return '\n'.join(line for line in lines if line).strip()

# --- DATABEARBETNINGSFUNKTIONER ---

def get_bounding_box(root, ISO_NAMESPACES):
    """Extraherar Bounding Box-information från ISO 19139 XML."""
    
    xpath_bbox = './/gmd:geographicElement/gmd:EX_GeographicBoundingBox'
    bbox_element = root.xpath(xpath_bbox, namespaces=ISO_NAMESPACES)
    
    if not bbox_element:
        return None

    xpath_west = './gmd:westBoundLongitude/gco:Decimal'
    xpath_east = './gmd:eastBoundLongitude/gco:Decimal'
    xpath_south = './gmd:southBoundLatitude/gco:Decimal'
    xpath_north = './gmd:northBoundLatitude/gco:Decimal'
    
    try:
        # Säker parsningslogik
        west = clean_tag(bbox_element[0].xpath(xpath_west, namespaces=ISO_NAMESPACES)[0])
        east = clean_tag(bbox_element[0].xpath(xpath_east, namespaces=ISO_NAMESPACES)[0])
        south = clean_tag(bbox_element[0].xpath(xpath_south, namespaces=ISO_NAMESPACES)[0])
        north = clean_tag(bbox_element[0].xpath(xpath_north, namespaces=ISO_NAMESPACES)[0])
        
        return (f"Väst: {west}, Öst: {east}\n"
                f"Syd: {south}, Nord: {north}")
                
    except IndexError:
        return None 

def get_xml_data(csw_url):
    """Hämtar XML-metadata från en CSW GetRecordById URL."""
    # --- START GUID-EXTRAKTION (Dessa rader saknades eller skadades) ---
    parsed_url = urlparse(csw_url)
    query_params = parse_qs(parsed_url.query)
    guid_from_query = query_params.get('id', [None])[0]
    
    if not guid_from_query:
        match = re.search(r'/metadata/([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})', csw_url)
        guid_from_query = match.group(1) if match else None
    # --- SLUT GUID-EXTRAKTION ---

    if not guid_from_query:
        raise ValueError("Kunde inte extrahera GUID från den angivna URL:en.")
        
    csw_base_url = 'https://www.geodata.se/geodataportalen/srv/swe/csw' 
    
    # FIX: Mer specifik Accept-header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/xml; charset=UTF-8, text/xml, */*' 
    }
    
    # FIX: Lägg till OutputSchema
    params = {
        'service': 'CSW',
        'version': '2.0.2',
        'request': 'GetRecordById',
        'id': guid_from_query,  # <-- variabeln måste vara definierad här
        'elementsetname': 'full',
        'outputschema': 'http://www.isotc211.org/2005/gmd' 
    }
    
    response = requests.get(csw_base_url, params=params, headers=headers, timeout=30)
    response.raise_for_status() 
    
    xml_data = response.text
    
    # Debugging av kort respons
    if len(xml_data.strip()) < 50:
         print(f"DEBUG: XML-data är kort ({len(xml_data)} tecken). Början: {xml_data[:50]}...")
         
    return xml_data


def iso19139_till_zotero_rdf(xml_data, csw_url):
    """
    Parsar ISO 19139 XML och konverterar till Zotero RDF XML-struktur.
    """
    
    # --- NAMESPACES ---
    RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    DC_NS = "http://purl.org/dc/elements/1.1/"
    ZOTERO_NS = "http://www.zotero.org/namespaces/export#" 
    FOAF_NS = "http://xmlns.com/foaf/0.1/"
    BIB_NS = "http://purl.org/net/biblio#"
    DCTERMS_NS = "http://purl.org/dc/terms/"
    LINK_NS = "http://purl.org/rss/1.0/modules/link/" 
    
    ISO_NAMESPACES = {
        'gmd': 'http://www.isotc211.org/2005/gmd',
        'gco': 'http://www.isotc211.org/2005/gco',
        'gml': 'http://www.opengis.net/gml',
        'srv': 'http://www.isotc211.org/2005/srv'
    }
    
    # FIX: Tar bort XML-deklarationen (för lxml-kompatibilitet)
    if xml_data and xml_data.strip().startswith('<?xml'):
        xml_data = re.sub(r'<\?xml[^>]*\?>', '', xml_data, count=1).strip()
    
    try:
        root = ET.fromstring(xml_data)
    except Exception as e:
        raise ValueError(f"FEL vid parsning av XML med lxml: {e}")
        
    # --- Datahämtning och Sanering (ANVÄNDER ROBUSTA XPATHS) ---
    
    # Titel (Robusta XPaths)
    xpath_titel = './/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString'
    titel_element = root.xpath(xpath_titel, namespaces=ISO_NAMESPACES)
    titel = clean_tag(titel_element[0]) if titel_element else ''
    
    # Abstrakt (Robusta XPaths)
    xpath_abstrakt = './/gmd:abstract/gco:CharacterString'
    abstrakt_element = root.xpath(xpath_abstrakt, namespaces=ISO_NAMESPACES)
    abstrakt = clean_tag(abstrakt_element[0]) if abstrakt_element else ''

    # Datum (Hitta senaste datum)
    latest_date = None
    xpath_date_types = './/gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="creation" or gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="revision"]/gmd:date/gco:Date'
    date_elements = root.xpath(xpath_date_types, namespaces=ISO_NAMESPACES)
    
    for date_el in date_elements:
        date_str = clean_tag(date_el)
        try:
            current_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                if len(date_str) == 4 and date_str.isdigit():
                    current_date = datetime.datetime.strptime(date_str, '%Y').date()
                else:
                    continue
            except ValueError:
                continue 

        if latest_date is None or current_date > latest_date:
            latest_date = current_date
            
    if latest_date:
        date_output_str = latest_date.strftime("%Y-%m-%d")
    else:
        date_output_str = datetime.date.today().strftime("%Y-%m-%d") 
    
    # Ansvarig organisation (Robusta XPaths)
    ansvarig_list = []
    xpath_responsible = (
        './/gmd:CI_ResponsibleParty[gmd:role/gmd:CI_RoleCode/@codeListValue="owner" or gmd:role/gmd:CI_RoleCode/@codeListValue="custodian"]/'
        'gmd:organisationName/gco:CharacterString'
    )
    for org_element in root.xpath(xpath_responsible, namespaces=ISO_NAMESPACES):
        ansvarig_list.append(clean_tag(org_element))
        
    if not ansvarig_list:
        ansvarig_list.append('Geodata Provider') 

    # Hämta Spatial Representation Type
    xpath_spatial_format = './/gmd:spatialRepresentationType/gmd:MD_SpatialRepresentationTypeCode/@codeListValue'
    spatial_format_element = root.xpath(xpath_spatial_format, namespaces=ISO_NAMESPACES)
    spatial_format = sanitize_text_single_line(spatial_format_element[0]) if spatial_format_element else ''
    
    # GUID
    match = re.search(r'([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})', csw_url)
    guid = match.group(1) if match else 'no-guid-found'
    
    # Hämta BBox
    bbox_info = get_bounding_box(root, ISO_NAMESPACES) 

    # SKAPAR titel_clean HÄR
    titel_clean = sanitize_text_single_line(titel)
    
    # FIX: Fallback-titel om metadata saknar titel (här definieras variabeln)
    if not titel_clean:
        titel_clean = f"Metadata saknar titel: {guid}" 
        
    license_clean = 'Creative Commons CC0 1.0 Public Domain Dedication' 
    
    tags_list = ["GIS", "geodata"] 
    xpath_keywords = './/*[local-name()="MD_Keywords"]/*[local-name()="keyword"]/*[local-name()="CharacterString"]'
    for tag_element in root.xpath(xpath_keywords, namespaces=ISO_NAMESPACES):
        tag = sanitize_text_single_line(clean_tag(tag_element))
        if tag and tag not in tags_list:
             tags_list.append(tag)

    abstract_content = sanitize_text_preserve_newlines(abstrakt)
    if bbox_info:
        abstract_content += f"\n\n--- Geografisk Utbredning ---\n{sanitize_text_preserve_newlines(bbox_info)}"
    
    # --- BYGG ZOTERO RDF XML ---
    # ... (Resten av logiken för att bygga RDF-trädet) ...
    
    ns_map_list = [
        ('rdf', RDF_NS), ('z', ZOTERO_NS), ('dc', DC_NS), 
        ('foaf', FOAF_NS), ('bib', BIB_NS), ('link', LINK_NS), 
        ('dcterms', DCTERMS_NS)
    ]
    ns_map = dict(ns_map_list)
    
    rdf_root = ET.Element(f"{{{RDF_NS}}}RDF", nsmap=ns_map)
    
    # --- A. HUVUDPOST ---
    
    link_id = guid + "-link"
    
    item_element = ET.SubElement(rdf_root, f"{{{RDF_NS}}}Description", 
                                 attrib={f"{{{RDF_NS}}}about": csw_url}) 
    
    ET.SubElement(item_element, f"{{{ZOTERO_NS}}}itemType").text = "dataset"
    
    if ansvarig_list:
        authors_element = ET.SubElement(item_element, f"{{{BIB_NS}}}authors")
        seq_element = ET.SubElement(authors_element, f"{{{RDF_NS}}}Seq") 
        for org in ansvarig_list:
            li_element = ET.SubElement(seq_element, f"{{{RDF_NS}}}li")
            
            org_element = ET.SubElement(li_element, f"{{{FOAF_NS}}}Person")
            ET.SubElement(org_element, f"{{{FOAF_NS}}}surname").text = sanitize_text_single_line(org)

    ET.SubElement(item_element, f"{{{LINK_NS}}}link", 
                  attrib={f"{{{RDF_NS}}}resource": f"#{link_id}"}) 

    for tag in tags_list:
        ET.SubElement(item_element, f"{{{DC_NS}}}subject").text = tag
        
    ET.SubElement(item_element, f"{{{DC_NS}}}title").text = titel_clean
    ET.SubElement(item_element, f"{{{DCTERMS_NS}}}abstract").text = abstract_content 
    ET.SubElement(item_element, f"{{{DC_NS}}}date").text = date_output_str 
    
    identifier_element = ET.SubElement(item_element, f"{{{DC_NS}}}identifier")
    uri_element = ET.SubElement(identifier_element, f"{{{DCTERMS_NS}}}URI")
    ET.SubElement(uri_element, f"{{{RDF_NS}}}value").text = csw_url
    
    ET.SubElement(item_element, f"{{{DC_NS}}}rights").text = license_clean 
    
    ET.SubElement(item_element, f"{{{ZOTERO_NS}}}type").text = "Geodata"
    
    if spatial_format:
        ET.SubElement(item_element, f"{{{ZOTERO_NS}}}medium").text = spatial_format.lower()
    
    # --- B. BILAGA (ATTACHMENT) ---
    
    attachment_element = ET.SubElement(rdf_root, f"{{{ZOTERO_NS}}}Attachment", 
                                        attrib={f"{{{RDF_NS}}}about": f"#{link_id}"})
    ET.SubElement(attachment_element, f"{{{ZOTERO_NS}}}itemType").text = "attachment"
    ET.SubElement(attachment_element, f"{{{DC_NS}}}title").text = "Kataloglänk"
    
    att_identifier_element = ET.SubElement(attachment_element, f"{{{DC_NS}}}identifier")
    att_uri_element = ET.SubElement(att_identifier_element, f"{{{DCTERMS_NS}}}URI")
    ET.SubElement(att_uri_element, f"{{{RDF_NS}}}value").text = csw_url

    ET.SubElement(attachment_element, f"{{{ZOTERO_NS}}}linkMode").text = "1" 
    
    xml_output = ET.tostring(rdf_root, encoding='utf-8', pretty_print=True, xml_declaration=False).decode('utf-8')

    return xml_output


# --- HUVUDFUNKTION FÖR TERMINALEN ---

def main():
    """Hanterar argument från kommandoraden och kör konverteringen."""
    
    if len(sys.argv) < 2:
        print("Användning: python CSW_to_Zotero_RDF.py <CSW_URL_1> [CSW_URL_2] ...")
        sys.exit(1)

    url_list = sys.argv[1:]
    
    output_folder = "rdf_output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for csw_url in url_list:
        try:
            print(f"Hämtar data för: {csw_url}")
            
            xml_data = get_xml_data(csw_url)

            rdf_output = iso19139_till_zotero_rdf(xml_data, csw_url)

            if rdf_output is None:
                print(f"VARNING: Konverteringen returnerade ingen data för {csw_url}. Hoppar över.")
                continue

            match = re.search(r'([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})', csw_url)
            guid = match.group(1) if match else str(uuid.uuid4())
            
            output_filename = os.path.join(output_folder, f"{guid}.rdf")

            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(rdf_output)
            
            print(f"KONVERTERING KLAR: Sparad som {output_filename}")

        except requests.exceptions.HTTPError as e:
            print(f"FEL (HTTP): Kunde inte hämta {csw_url}. Serverfel: {e}")
        except Exception as e:
            print(f"FEL (General): Kunde inte konvertera {csw_url}. Orsak: {e}")


if __name__ == "__main__":
    main()