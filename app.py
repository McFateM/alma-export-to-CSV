#!/usr/bin/env python3
"""
Alma Digital Title Export to CSV - Flet Application

This application searches for digital titles in Alma API and exports
bibliographic record metadata to a CSV file with predefined column headings.
"""

import csv
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional

import flet as ft
from almapipy import AlmaCnxn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging():
    """Setup comprehensive logging to both file and console."""
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create timestamp for log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"alma_export_{timestamp}.log")
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # File handler (detailed logging)
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler (less verbose)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Log the setup
    logging.info("="*50)
    logging.info("Alma Digital Title Export Application Started")
    logging.info(f"Log file: {log_filename}")
    logging.info("="*50)
    
    return log_filename

# Initialize logging
LOG_FILE = setup_logging()
logger = logging.getLogger(__name__)


class AlmaAPIClient:
    """Client for interacting with the Alma API using almapipy."""
    
    def __init__(self, api_key: str, region: str = "na"):
        """
        Initialize the Alma API client using almapipy.
        
        Args:
            api_key: Alma API key
            region: Alma API region code (na, eu, ap, ca, cn) - default: na (North America)
        """
        self.api_key = api_key
        self.region = "na"
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize almapipy connection
        # AlmaCnxn expects environment variable ALMA_API_KEY or direct parameter
        self.logger.info(f"Initializing AlmaAPIClient with almapipy for region: {region}")
        self.cnxn = AlmaCnxn(api_key, data_format='json')
        self.logger.info(f"AlmaAPIClient initialized successfully")
        self.logger.debug(f"API key length: {len(api_key)} characters")
    
    
    def get_bib_details(self, mms_id: str) -> Optional[Dict]:
        """
        Get detailed bibliographic record using almapipy.
        
        Args:
            mms_id: MMS ID of the bibliographic record
            
        Returns:
            Detailed bibliographic record or None
        """
        # Clean the MMS ID - remove any whitespace or hidden characters
        mms_id_clean = mms_id.strip()
        
        self.logger.debug(f"Fetching detailed record for MMS ID: {mms_id_clean}")
        
        try:
            # Use almapipy to get the specific bib record
            # Pass as a string to get single record
            response = self.cnxn.bibs.catalog.get(
                mms_id_clean,
                # expand="p_avail,e_avail,d_avail"
            )
            
            self.logger.debug(f"API response type: {type(response)}")
            
            # The response should be a single bib record dict
            if isinstance(response, dict):
                # Check if it's a valid bib record
                if 'mms_id' in response:
                    self.logger.debug(f"Successfully retrieved record for {mms_id_clean}")
                    return response
                # Sometimes it might be wrapped in a bib array
                elif 'bib' in response:
                    bibs = response.get("bib", [])
                    if bibs and len(bibs) > 0:
                        self.logger.debug(f"Successfully retrieved record from 'bib' array for {mms_id_clean}")
                        return bibs[0]
                    else:
                        self.logger.warning(f"Empty 'bib' array in response for MMS ID: {mms_id_clean}")
                        return None
                else:
                    self.logger.warning(f"Unexpected response structure for {mms_id_clean}: {list(response.keys())}")
                    return None
            else:
                self.logger.warning(f"Response is not a dict for {mms_id_clean}: {type(response)}")
                return None
            
        except Exception as e:
            self.logger.warning(f"Failed to get detailed record for {mms_id_clean}: {str(e)}")
            return None
    
    def get_bibs_from_mms_ids(self, mms_ids: List[str], progress_callback=None) -> List[Dict]:
        """
        Retrieve bibliographic records for a list of MMS IDs.
        
        Args:
            mms_ids: List of MMS IDs to retrieve
            progress_callback: Optional callback function(current, total) for progress updates
            
        Returns:
            List of bibliographic records
        """
        self.logger.info(f"Starting retrieval of {len(mms_ids)} bibliographic records by MMS ID")
        
        all_bibs = []
        failed_ids = []
        total = len(mms_ids)
        
        for i, mms_id in enumerate(mms_ids, 1):
            self.logger.debug(f"Fetching record {i}/{total}: MMS ID {mms_id}")
            
            try:
                bib = self.get_bib_details(mms_id.strip())
                if bib:
                    all_bibs.append(bib)
                    if i % 10 == 0:  # Log progress every 10 records
                        self.logger.info(f"Progress: Retrieved {i}/{total} records")
                else:
                    failed_ids.append(mms_id)
                    self.logger.warning(f"No record found for MMS ID: {mms_id}")
                    
            except Exception as e:
                failed_ids.append(mms_id)
                self.logger.error(f"Failed to retrieve MMS ID {mms_id}: {str(e)}")
            
            # Call progress callback after each record
            if progress_callback:
                progress_callback(i, total)
        
        self.logger.info(f"Retrieval completed. Successfully retrieved: {len(all_bibs)}, Failed: {len(failed_ids)}")
        if failed_ids:
            self.logger.warning(f"Failed MMS IDs: {', '.join(failed_ids[:10])}{'...' if len(failed_ids) > 10 else ''}")
        
        return all_bibs
    
    @staticmethod
    def read_mms_ids_from_csv(csv_file_path: str) -> List[str]:
        """
        Read MMS IDs from a CSV file.
        
        The CSV file should have a column named 'mms_id', 'MMS_ID', or similar.
        If no header is found, assumes the first column contains MMS IDs.
        
        Args:
            csv_file_path: Path to the CSV file
            
        Returns:
            List of MMS IDs
        """
        logger = logging.getLogger(f"{__name__}.AlmaAPIClient")
        logger.info(f"Reading MMS IDs from CSV file: {csv_file_path}")
        
        mms_ids = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                # Read first line to check for headers
                first_line = csvfile.readline().strip()
                csvfile.seek(0)
                
                # Try to detect delimiter (comma, tab, or semicolon)
                delimiter = ','
                if '\t' in first_line:
                    delimiter = '\t'
                elif ';' in first_line and ',' not in first_line:
                    delimiter = ';'
                
                logger.debug(f"Using delimiter: {repr(delimiter)}")
                
                reader = csv.reader(csvfile, delimiter=delimiter)
                first_row = next(reader)
                
                # Check if first row looks like a header
                # (contains text like "mms", "id", or looks non-numeric)
                has_header = any(
                    not cell.strip().isdigit() and cell.strip() 
                    for cell in first_row
                )
                
                mms_id_col = 0  # Default to first column
                
                if has_header:
                    # Find MMS_ID column (case insensitive, handle spaces)
                    for i, header in enumerate(first_row):
                        header_lower = header.lower().replace(' ', '')
                        if 'mms' in header_lower and 'id' in header_lower:
                            mms_id_col = i
                            logger.info(f"Found MMS ID column: '{header}' at index {i}")
                            break
                    
                    if mms_id_col == 0 and len(first_row) > 0:
                        logger.warning(f"No MMS_ID column found in headers, using first column: '{first_row[0]}'")
                    
                    # Read data rows
                    for row in reader:
                        if row and len(row) > mms_id_col:
                            mms_id = row[mms_id_col].strip()
                            # Skip comments (lines starting with #), empty values, and pure text values
                            if mms_id and not mms_id.startswith('#') and not mms_id.isalpha():
                                mms_ids.append(mms_id)
                            elif mms_id.startswith('#'):
                                logger.debug(f"Skipping comment line: {mms_id[:50]}...")
                else:
                    # First row is data, not header - add it
                    logger.info("No header detected, using first column for MMS IDs")
                    first_val = first_row[0].strip()
                    if first_val and not first_val.startswith('#'):
                        mms_ids.append(first_val)
                    
                    # Read remaining rows
                    for row in reader:
                        if row and row[0].strip():
                            mms_id = row[0].strip()
                            # Skip comments (lines starting with #)
                            if not mms_id.startswith('#'):
                                mms_ids.append(mms_id)
                            else:
                                logger.debug(f"Skipping comment line: {mms_id[:50]}...")
            
            logger.info(f"Successfully read {len(mms_ids)} MMS IDs from CSV file")
            if mms_ids:
                logger.debug(f"First 5 MMS IDs: {mms_ids[:5]}")
                logger.debug(f"First MMS ID details - value: '{mms_ids[0]}', length: {len(mms_ids[0])}, repr: {repr(mms_ids[0])}")
                # Check for any unusual characters
                for i, mms_id in enumerate(mms_ids[:3]):
                    logger.debug(f"MMS ID {i}: has_spaces={' ' in mms_id}, has_newline={'\\n' in mms_id}, has_tab={'\\t' in mms_id}")
            else:
                logger.warning("No MMS IDs found in file")
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file_path}")
            raise Exception(f"CSV file not found: {csv_file_path}")
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}", exc_info=True)
            raise Exception(f"Error reading CSV file: {str(e)}")
        
        return mms_ids


class CSVExporter:
    """Handles CSV export of bibliographic records."""
    
    logger = logging.getLogger(f"{__name__}.CSVExporter")
    
    # CSV column headings as specified in the reference file
    COLUMN_HEADINGS = [
        "group_id", "collection_id", "mms_id", "originating_system_id", "compoundrelationship",
        "dc:title", "dcterms:alternative", "oldalttitle", "dc:identifier",
        "dcterms:identifier.dcterms:URI", "dcterms:tableOfContents", "dc:creator",
        "dc:contributor", "dc:subject", "dcterms:subject.dcterms:LCSH",
        "dcterms:subject.dcterms:LCSH", "dcterms:subject.dcterms:LCSH",
        "dcterms:subject.dcterms:LCSH", "dcterms:subject.dcterms:LCSH",
        "dcterms:subject.dcterms:LCSH", "dcterms:subject.dcterms:LCSH",
        "dcterms:subject.dcterms:LCSH", "dcterms:subject.dcterms:LCSH",
        "dcterms:subject.dcterms:LCSH", "dcterms:subject.dcterms:LCSH",
        "dcterms:subject.dcterms:LCSH", "dc:description", "dcterms:provenance",
        "dcterms:bibliographicCitation", "dcterms:abstract", "dcterms:publisher",
        "dcterms:publisher", "dc:date", "dcterms:created", "dcterms:issued",
        "dcterms:dateSubmitted", "dcterms:dateAccepted", "dc:type", "dc:format",
        "dcterms:extent", "dcterms:extent", "dcterms:medium",
        "dcterms:format.dcterms:IMT", "dcterms:type.dcterms:DCMIType", "dc:language",
        "dc:relation", "dcterms:isPartOf", "dcterms:isPartOf", "dcterms:isPartOf",
        "dc:coverage", "dcterms:spatial", "dcterms:spatial.dcterms:Point",
        "dcterms:temporal", "dc:rights", "dc:source", "bib custom field",
        "rep_label", "rep_public_note", "rep_access_rights", "rep_usage_type",
        "rep_library", "rep_note", "rep_custom field", "file_name_1", "file_label_1",
        "file_name_2", "file_label_2", "googlesheetsource", "dginfo"
    ]
    
    @staticmethod
    def extract_dc_field(record: Dict, element: str, namespace: str = "dc") -> List[str]:
        """
        Extract data from Dublin Core XML in the anies field.
        
        Args:
            record: Bibliographic record
            element: DC element name (e.g., 'title', 'creator', 'subject')
            namespace: Namespace prefix ('dc' or 'dcterms')
            
        Returns:
            List of values for the specified DC element
        """
        import xml.etree.ElementTree as ET
        
        try:
            anies = record.get("anies", [])
            if not anies:
                return []
            
            # anies is a list, take the first element (the DC XML)
            dc_xml = anies[0] if isinstance(anies, list) else anies
            
            # Parse XML
            root = ET.fromstring(dc_xml)
            
            # Define namespaces
            namespaces = {
                'dc': 'http://purl.org/dc/elements/1.1/',
                'dcterms': 'http://purl.org/dc/terms/'
            }
            
            # Find all matching elements
            values = []
            tag = f"{{{namespaces[namespace]}}}{element}"
            for elem in root.findall(f".//{tag}"):
                if elem.text and elem.text.strip():
                    values.append(elem.text.strip())
            
            if values:
                CSVExporter.logger.debug(f"Extracted DC {namespace}:{element}: {len(values)} value(s)")
            return values
            
        except Exception as e:
            CSVExporter.logger.warning(f"Error extracting DC field {namespace}:{element}: {str(e)}")
            return []
    
    @staticmethod
    def extract_custom_field(record: Dict, element: str, namespace_uri: str) -> List[str]:
        """
        Extract data from custom namespace fields in the anies field.
        
        Args:
            record: Bibliographic record
            element: Element name
            namespace_uri: Full namespace URI
            
        Returns:
            List of values for the specified element
        """
        import xml.etree.ElementTree as ET
        
        try:
            anies = record.get("anies", [])
            if not anies:
                return []
            
            dc_xml = anies[0] if isinstance(anies, list) else anies
            root = ET.fromstring(dc_xml)
            
            # Find all matching elements
            values = []
            tag = f"{{{namespace_uri}}}{element}"
            for elem in root.findall(f".//{tag}"):
                if elem.text and elem.text.strip():
                    values.append(elem.text.strip())
            
            if values:
                CSVExporter.logger.debug(f"Extracted custom field {element}: {len(values)} value(s)")
            return values
            
        except Exception as e:
            CSVExporter.logger.warning(f"Error extracting custom field {element}: {str(e)}")
            return []
    
    @staticmethod
    def map_bib_to_csv_row(bib: Dict) -> Dict[str, str]:
        """
        Map a bibliographic record to a CSV row using Dublin Core fields.
        
        Args:
            bib: Bibliographic record from Alma API
            
        Returns:
            Dictionary mapping column headings to values
        """
        mms_id = bib.get("mms_id", "Unknown")
        CSVExporter.logger.debug(f"Mapping bibliographic record {mms_id} to CSV row")
        
        row = {heading: "" for heading in CSVExporter.COLUMN_HEADINGS}
        
        # Custom namespace URI for Grinnell-specific fields
        grinnell_ns = f"http://alma.exlibrisgroup.com/dc/{bib.get('originating_system', '01GCL_INST')}"
        
        # Basic metadata from top-level fields
        row["mms_id"] = bib.get("mms_id", "")
        row["originating_system_id"] = bib.get("originating_system_id", "")
        
        # Extract Dublin Core fields from XML
        # dc:title
        titles = CSVExporter.extract_dc_field(bib, "title", "dc")
        row["dc:title"] = titles[0] if titles else bib.get("title", "")
        
        # dcterms:alternative (alternative title)
        alt_titles = CSVExporter.extract_dc_field(bib, "alternative", "dcterms")
        row["dcterms:alternative"] = "; ".join(alt_titles) if alt_titles else ""
        
        # dc:identifier(s)
        identifiers = CSVExporter.extract_dc_field(bib, "identifier", "dc")
        row["dc:identifier"] = "; ".join(identifiers) if identifiers else ""
        
        # dcterms:identifier.dcterms:URI (often http://hdl.handle.net/...)
        for identifier in identifiers:
            if identifier.startswith("http://") or identifier.startswith("https://"):
                row["dcterms:identifier.dcterms:URI"] = identifier
                break
        
        # dcterms:tableOfContents
        toc = CSVExporter.extract_dc_field(bib, "tableOfContents", "dcterms")
        row["dcterms:tableOfContents"] = "; ".join(toc) if toc else ""
        
        # dc:creator
        creators = CSVExporter.extract_dc_field(bib, "creator", "dc")
        row["dc:creator"] = "; ".join(creators) if creators else bib.get("author", "")
        
        # dc:contributor
        contributors = CSVExporter.extract_dc_field(bib, "contributor", "dc")
        row["dc:contributor"] = "; ".join(contributors) if contributors else ""
        
        # dc:subject and dcterms:subject.dcterms:LCSH (multiple subject columns)
        subjects = CSVExporter.extract_dc_field(bib, "subject", "dc")
        subjects += CSVExporter.extract_dc_field(bib, "subject", "dcterms")
        if subjects:
            row["dc:subject"] = subjects[0]
            # Fill up to 11 additional LCSH columns
            for i in range(1, min(len(subjects), 12)):
                # The COLUMN_HEADINGS has multiple "dcterms:subject.dcterms:LCSH" entries
                # We need to fill them sequentially - they appear at indices 14-24
                pass  # Will be handled by the column heading structure
        
        # dc:description
        descriptions = CSVExporter.extract_dc_field(bib, "description", "dc")
        row["dc:description"] = "; ".join(descriptions) if descriptions else ""
        
        # dcterms:provenance
        provenance = CSVExporter.extract_dc_field(bib, "provenance", "dcterms")
        row["dcterms:provenance"] = "; ".join(provenance) if provenance else ""
        
        # dcterms:bibliographicCitation
        citation = CSVExporter.extract_dc_field(bib, "bibliographicCitation", "dcterms")
        row["dcterms:bibliographicCitation"] = "; ".join(citation) if citation else ""
        
        # dcterms:abstract
        abstract = CSVExporter.extract_dc_field(bib, "abstract", "dcterms")
        row["dcterms:abstract"] = "; ".join(abstract) if abstract else ""
        
        # dcterms:publisher
        publishers = CSVExporter.extract_dc_field(bib, "publisher", "dcterms")
        if publishers:
            row["dcterms:publisher"] = publishers[0]
            if len(publishers) > 1:
                # There are two dcterms:publisher columns at indices 30-31
                pass
        elif bib.get("publisher_const"):
            row["dcterms:publisher"] = bib.get("publisher_const", "")
        
        # dc:date
        dates = CSVExporter.extract_dc_field(bib, "date", "dc")
        row["dc:date"] = dates[0] if dates else bib.get("date_of_publication", "")
        
        # dcterms:created
        created = CSVExporter.extract_dc_field(bib, "created", "dcterms")
        row["dcterms:created"] = created[0] if created else ""
        
        # dcterms:issued
        issued = CSVExporter.extract_dc_field(bib, "issued", "dcterms")
        row["dcterms:issued"] = issued[0] if issued else bib.get("date_of_publication", "")
        
        # dcterms:dateSubmitted
        submitted = CSVExporter.extract_dc_field(bib, "dateSubmitted", "dcterms")
        row["dcterms:dateSubmitted"] = submitted[0] if submitted else ""
        
        # dcterms:dateAccepted
        accepted = CSVExporter.extract_dc_field(bib, "dateAccepted", "dcterms")
        row["dcterms:dateAccepted"] = accepted[0] if accepted else ""
        
        # dc:type
        types = CSVExporter.extract_dc_field(bib, "type", "dc")
        row["dc:type"] = types[0] if types else ""
        
        # dc:format
        formats = CSVExporter.extract_dc_field(bib, "format", "dc")
        row["dc:format"] = formats[0] if formats else ""
        
        # dcterms:extent (can have multiple)
        extents = CSVExporter.extract_dc_field(bib, "extent", "dcterms")
        if extents:
            row["dcterms:extent"] = extents[0]
            if len(extents) > 1:
                # Second extent column exists at index 40
                pass
        
        # dcterms:medium
        medium = CSVExporter.extract_dc_field(bib, "medium", "dcterms")
        row["dcterms:medium"] = medium[0] if medium else ""
        
        # dcterms:format.dcterms:IMT
        # Note: This might need special handling if it has attributes
        
        # dcterms:type.dcterms:DCMIType
        dcmi_types = CSVExporter.extract_dc_field(bib, "type", "dcterms")
        # Could also be in attributes - need to check actual data
        
        # dc:language
        languages = CSVExporter.extract_dc_field(bib, "language", "dc")
        row["dc:language"] = "; ".join(languages) if languages else ""
        
        # dc:relation
        relations = CSVExporter.extract_dc_field(bib, "relation", "dc")
        row["dc:relation"] = "; ".join(relations) if relations else ""
        
        # dcterms:isPartOf (multiple columns: 46-48)
        ispartof = CSVExporter.extract_dc_field(bib, "isPartOf", "dcterms")
        if ispartof:
            row["dcterms:isPartOf"] = ispartof[0]
            # Additional columns exist but we need exact indices
        
        # dc:coverage
        coverage = CSVExporter.extract_dc_field(bib, "coverage", "dc")
        row["dc:coverage"] = "; ".join(coverage) if coverage else ""
        
        # dcterms:spatial
        spatial = CSVExporter.extract_dc_field(bib, "spatial", "dcterms")
        row["dcterms:spatial"] = "; ".join(spatial) if spatial else ""
        
        # dcterms:temporal
        temporal = CSVExporter.extract_dc_field(bib, "temporal", "dcterms")
        row["dcterms:temporal"] = "; ".join(temporal) if temporal else ""
        
        # dc:rights
        rights = CSVExporter.extract_dc_field(bib, "rights", "dc")
        row["dc:rights"] = "; ".join(rights) if rights else ""
        
        # dc:source
        sources = CSVExporter.extract_dc_field(bib, "source", "dc")
        row["dc:source"] = "; ".join(sources) if sources else ""
        
        # Custom fields (Grinnell-specific)
        # compoundrelationship
        compound = CSVExporter.extract_custom_field(bib, "compoundrelationship", grinnell_ns)
        row["compoundrelationship"] = compound[0] if compound else ""
        
        # googlesheetsource
        sheets = CSVExporter.extract_custom_field(bib, "googlesheetsource", grinnell_ns)
        row["googlesheetsource"] = sheets[0] if sheets else ""
        
        # dginfo
        dginfo = CSVExporter.extract_custom_field(bib, "dginfo", grinnell_ns)
        row["dginfo"] = dginfo[0] if dginfo else ""
        
        return row
    
    @staticmethod
    def export_to_csv(bibs: List[Dict], filename: str) -> None:
        """
        Export bibliographic records to CSV.
        Deleted records are written as comment lines (prefixed with #).
        
        Args:
            bibs: List of bibliographic records
            filename: Output CSV filename
        """
        CSVExporter.logger.info(f"Starting CSV export of {len(bibs)} records to: {filename}")
        
        deleted_count = 0
        active_count = 0
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=CSVExporter.COLUMN_HEADINGS)
                writer.writeheader()
                CSVExporter.logger.debug(f"CSV header written with {len(CSVExporter.COLUMN_HEADINGS)} columns")
                
                for i, bib in enumerate(bibs, 1):
                    # Check if record is deleted
                    is_deleted = CSVExporter.is_record_deleted(bib)
                    
                    row = CSVExporter.map_bib_to_csv_row(bib)
                    
                    if is_deleted:
                        # Write as comment line
                        mms_id = bib.get("mms_id", "unknown")
                        comment_line = f"# DELETED RECORD - MMS ID: {mms_id}"
                        csvfile.write(comment_line + "\n")
                        deleted_count += 1
                        CSVExporter.logger.debug(f"Record {mms_id} marked as deleted")
                    else:
                        # Write normal row
                        writer.writerow(row)
                        active_count += 1
                    
                    if i % 10 == 0:  # Log progress every 10 records
                        CSVExporter.logger.debug(f"Exported {i}/{len(bibs)} records")
            
            CSVExporter.logger.info(f"CSV export completed successfully. File size: {os.path.getsize(filename)} bytes")
            CSVExporter.logger.info(f"Active records: {active_count}, Deleted records (commented): {deleted_count}")
            
        except Exception as e:
            CSVExporter.logger.error(f"Failed to export CSV: {str(e)}")
            raise
    
    @staticmethod
    def is_record_deleted(bib: Dict) -> bool:
        """
        Check if a bibliographic record is deleted.
        
        Args:
            bib: Bibliographic record
            
        Returns:
            True if record is deleted, False otherwise
        """
        # Check various indicators of deletion
        # 1. Check if title contains "Deleted" or is empty/minimal
        title = bib.get("title", "").lower()
        if "deleted" in title or title.strip() == "":
            return True
        
        # 2. Check record status fields if they exist
        if bib.get("record_status") == "deleted":
            return True
        
        # 3. Check if cataloging_level indicates deletion
        cataloging_level = bib.get("cataloging_level", {})
        if isinstance(cataloging_level, dict):
            desc = cataloging_level.get("desc", "").lower()
            if "deleted" in desc:
                return True
        
        # 4. Check suppress flags (all suppressed might indicate deletion)
        suppress_publishing = bib.get("suppress_from_publishing", "false").lower()
        suppress_external = bib.get("suppress_from_external_search", "false").lower()
        if suppress_publishing == "true" and suppress_external == "true":
            # Only consider it deleted if also lacks substantial metadata
            if not bib.get("anies") or len(bib.get("anies", [])) == 0:
                return True
        
        return False


class AlmaExportApp:
    """Main Flet application class."""
    
    def __init__(self, page: ft.Page):
        """
        Initialize the application.
        
        Args:
            page: Flet page instance
        """
        self.page = page
        self.page.title = "Alma Digital Title Export to CSV"
        self.page.scroll = "adaptive"
        self.page.padding = 20
        self.page.window.height = 750  # Set window height (default ~700px, now 750px)
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Initializing AlmaExportApp")
        
        # API client
        self.api_client = None
        
        # Selected CSV file path
        self.selected_csv_path = None
        
        # UI Components
        self.api_key_field = ft.TextField(
            label="Alma API Key",
            password=True,
            can_reveal_password=True,
            width=400,
            hint_text="Enter your Alma API key"
        )
        
        # File picker for CSV input
        self.file_picker = ft.FilePicker(
            on_result=self.on_file_picked
        )
        self.page.overlay.append(self.file_picker)
        
        self.csv_file_display = ft.TextField(
            label="MMS ID CSV File",
            width=400,
            read_only=True,
            hint_text="No file selected"
        )
        
        self.file_pick_button = ft.ElevatedButton(
            "Select CSV File",
            icon=ft.Icons.FOLDER_OPEN,
            on_click=lambda _: self.file_picker.pick_files(
                allowed_extensions=["csv"],
                dialog_title="Select CSV file with MMS IDs"
            )
        )
        
        # Row limit controls
        self.limit_rows_checkbox = ft.Checkbox(
            label="Limit number of rows to process",
            value=False,
            on_change=self.on_limit_checkbox_change
        )
        
        self.row_limit_field = ft.TextField(
            label="Number of rows",
            width=150,
            value="10",
            keyboard_type=ft.KeyboardType.NUMBER,
            disabled=True,
            hint_text="Enter number"
        )
        
        self.status_text = ft.Text(
            "",
            size=14,
            color=ft.Colors.BLUE_700
        )
        
        self.progress_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_700
        )
        
        self.results_text = ft.Text(
            "",
            size=14,
            selectable=True
        )
        
        self.progress_bar = ft.ProgressBar(
            visible=False,
            width=400,
            value=0
        )
        
        self.export_button = ft.ElevatedButton(
            "Export Records",
            icon=ft.Icons.DOWNLOAD,
            on_click=self.export_records
        )
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Load API key from environment if available
        env_api_key = os.getenv("ALMA_API_KEY", "")
        if env_api_key:
            self.api_key_field.value = env_api_key
        
        # Build the page layout
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Alma Digital Title Export to CSV",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_900
                        ),
                        ft.Divider(height=20, color=ft.Colors.BLUE_200),
                        ft.Text(
                            "Load MMS IDs from CSV file and export metadata to CSV",
                            size=14,
                            color=ft.Colors.GREY_700
                        ),
                        ft.Container(height=20),
                        self.api_key_field,
                        ft.Container(height=10),
                        ft.Row(
                            [
                                self.csv_file_display,
                                self.file_pick_button,
                            ],
                            spacing=10,
                        ),
                        ft.Container(height=10),
                        self.limit_rows_checkbox,
                        ft.Row(
                            [
                                self.row_limit_field,
                                ft.Text("(Leave unchecked to process all rows)", size=12, color=ft.Colors.GREY_600),
                            ],
                            spacing=10,
                        ),
                        ft.Container(height=10),
                        self.export_button,
                        self.progress_bar,
                        self.progress_text,
                        ft.Container(height=20),
                        self.status_text,
                        self.results_text,
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
                padding=20,
            )
        )
    
    def on_limit_checkbox_change(self, e):
        """Handle limit checkbox change."""
        self.row_limit_field.disabled = not e.control.value
        self.page.update()
    
    def on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file picker result."""
        if e.files:
            self.selected_csv_path = e.files[0].path
            self.csv_file_display.value = e.files[0].name
            self.logger.info(f"CSV file selected: {self.selected_csv_path}")
            self.show_info(f"Selected file: {e.files[0].name}")
        else:
            self.selected_csv_path = None
            self.csv_file_display.value = ""
            self.logger.debug("File selection cancelled")
        self.page.update()
    
    def export_records(self, e):
        """Handle export button click."""
        self.logger.info("Export operation started")
        
        # Validate inputs
        api_key = self.api_key_field.value.strip()
        
        self.logger.debug(f"Input validation - API key length: {len(api_key)}, CSV file: {self.selected_csv_path}")
        
        if not api_key:
            self.logger.warning("Export aborted: No API key provided")
            self.show_error("Please enter an Alma API key")
            return
        
        if not self.selected_csv_path:
            self.logger.warning("Export aborted: No CSV file selected")
            self.show_error("Please select a CSV file with MMS IDs")
            return
        
        # Initialize API client
        self.logger.info("Initializing Alma API client")
        self.api_client = AlmaAPIClient(api_key)
        
        # Show progress
        self.progress_bar.visible = True
        self.export_button.disabled = True
        self.file_pick_button.disabled = True
        self.status_text.value = "Reading MMS IDs from CSV file..."
        self.status_text.color = ft.Colors.BLUE_700
        self.results_text.value = ""
        self.page.update()
        
        start_time = datetime.now()
        self.logger.info(f"Starting export operation at {start_time}")
        
        try:
            # Read MMS IDs from CSV
            self.logger.info(f"Reading MMS IDs from: {self.selected_csv_path}")
            mms_ids = AlmaAPIClient.read_mms_ids_from_csv(self.selected_csv_path)
            
            if not mms_ids:
                self.logger.warning("No MMS IDs found in CSV file")
                self.show_error("No MMS IDs found in the CSV file")
                return
            
            self.logger.info(f"Found {len(mms_ids)} MMS IDs in CSV file")
            
            # Apply row limit if enabled
            if self.limit_rows_checkbox.value:
                try:
                    row_limit = int(self.row_limit_field.value)
                    if row_limit > 0 and row_limit < len(mms_ids):
                        mms_ids = mms_ids[:row_limit]
                        self.logger.info(f"Limiting to first {row_limit} rows")
                        self.status_text.value = f"Processing first {row_limit} of {len(mms_ids)} MMS IDs..."
                        self.page.update()
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid row limit value: {self.row_limit_field.value}, processing all rows")
            
            self.logger.info(f"Processing {len(mms_ids)} MMS IDs")
            
            # Update status
            self.status_text.value = f"Retrieving {len(mms_ids)} records from Alma..."
            self.progress_bar.value = 0
            self.progress_text.value = "0%"
            self.page.update()
            
            # Define progress callback
            def update_progress(current, total):
                progress = current / total
                self.progress_bar.value = progress
                percentage = int(progress * 100)
                self.progress_text.value = f"{percentage}% ({current}/{total} records)"
                self.page.update()
            
            # Retrieve bibliographic records with progress updates
            self.logger.info(f"Retrieving bibliographic records for {len(mms_ids)} MMS IDs")
            bibs = self.api_client.get_bibs_from_mms_ids(mms_ids, progress_callback=update_progress)
            
            if not bibs:
                self.logger.warning("No records retrieved from Alma")
                self.show_error("No records could be retrieved from Alma")
                return
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"alma_export_{timestamp}.csv"
            self.logger.info(f"Generated output filename: {filename}")
            
            # Update status
            self.status_text.value = f"Retrieved {len(bibs)} record(s). Exporting to CSV..."
            self.page.update()
            
            # Export to CSV
            self.logger.info(f"Starting CSV export of {len(bibs)} records")
            CSVExporter.export_to_csv(bibs, filename)
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time = end_time - start_time
            self.logger.info(f"Export completed in {execution_time.total_seconds():.2f} seconds")
            
            # Show success
            success_message = f"Successfully exported {len(bibs)} record(s) to:\n{os.path.abspath(filename)}"
            self.logger.info(f"Export successful: {os.path.abspath(filename)}")
            self.show_success(success_message)
            
        except Exception as ex:
            self.logger.error(f"Export failed: {str(ex)}", exc_info=True)
            self.show_error(f"Error: {str(ex)}")
        
        finally:
            self.progress_bar.visible = False
            self.progress_bar.value = 0
            self.progress_text.value = ""
            self.export_button.disabled = False
            self.file_pick_button.disabled = False
            self.page.update()
            self.logger.debug("UI reset completed")
    
    def show_error(self, message: str):
        """Display error message."""
        self.logger.error(f"Displaying error to user: {message}")
        self.status_text.value = "❌ " + message
        self.status_text.color = ft.Colors.RED_700
        self.page.update()
    
    def show_success(self, message: str):
        """Display success message."""
        self.logger.info(f"Displaying success to user: {message}")
        self.status_text.value = "✅ " + message
        self.status_text.color = ft.Colors.GREEN_700
        self.results_text.value = ""
        self.page.update()
    
    def show_info(self, message: str):
        """Display info message."""
        self.logger.info(f"Displaying info to user: {message}")
        self.status_text.value = "ℹ️ " + message
        self.status_text.color = ft.Colors.BLUE_700
        self.results_text.value = ""
        self.page.update()


def main(page: ft.Page):
    """Main entry point for the Flet application."""
    logger.info("Starting Flet application")
    logger.debug(f"Page details - title: {page.title}, theme: {page.theme_mode}")
    
    try:
        AlmaExportApp(page)
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    logger.info("Application startup")
    logger.info(f"Log file location: {LOG_FILE}")
    
    try:
        ft.app(target=main)
    except Exception as e:
        logger.error(f"Application crashed: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("Application shutdown")
        logging.info("="*50)
