#!/usr/bin/env python3
"""
Alma Digital Title Export to CSV - Flet Application

This application searches for digital titles in Alma API and exports
bibliographic record metadata to a CSV file with predefined column headings.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Optional

import flet as ft
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AlmaAPIClient:
    """Client for interacting with the Alma API."""
    
    def __init__(self, api_key: str, base_url: str = "https://api-na.hosted.exlibrisgroup.com"):
        """
        Initialize the Alma API client.
        
        Args:
            api_key: Alma API key
            base_url: Base URL for Alma API (default: North America region)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"apikey {api_key}",
            "Accept": "application/json"
        }
    
    def search_bibs(self, query: str, limit: int = 100) -> List[Dict]:
        """
        Search for bibliographic records in Alma.
        
        Args:
            query: Search query (title search)
            limit: Maximum number of records to retrieve per page
            
        Returns:
            List of bibliographic records
        """
        all_bibs = []
        offset = 0
        
        # Construct search query for digital titles
        # Format: title~{query} AND mms_tagSuppressed=false
        search_query = f"title~{query} AND mms_tagSuppressed=false"
        
        while True:
            endpoint = f"{self.base_url}/almaws/v1/bibs"
            params = {
                "q": search_query,
                "limit": limit,
                "offset": offset,
                "expand": "p_avail,e_avail,d_avail"
            }
            
            try:
                response = requests.get(endpoint, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                bibs = data.get("bib", [])
                if not bibs:
                    break
                
                all_bibs.extend(bibs)
                
                # Check if there are more results
                total_record_count = data.get("total_record_count", 0)
                if offset + limit >= total_record_count:
                    break
                    
                offset += limit
                
            except requests.exceptions.RequestException as e:
                raise Exception(f"API request failed: {str(e)}")
        
        return all_bibs
    
    def get_bib_details(self, mms_id: str) -> Optional[Dict]:
        """
        Get detailed bibliographic record.
        
        Args:
            mms_id: MMS ID of the bibliographic record
            
        Returns:
            Detailed bibliographic record or None
        """
        endpoint = f"{self.base_url}/almaws/v1/bibs/{mms_id}"
        params = {"expand": "p_avail,e_avail,d_avail"}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None


class CSVExporter:
    """Handles CSV export of bibliographic records."""
    
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
    def extract_marc_field(record: Dict, tag: str, subfield: Optional[str] = None) -> str:
        """
        Extract data from MARC record.
        
        Args:
            record: Bibliographic record
            tag: MARC tag
            subfield: MARC subfield code (optional)
            
        Returns:
            Extracted data or empty string
        """
        try:
            marc_record = record.get("record", {})
            datafields = marc_record.get("datafield", [])
            
            if not isinstance(datafields, list):
                datafields = [datafields]
            
            values = []
            for field in datafields:
                if field.get("tag") == tag:
                    if subfield:
                        subfields = field.get("subfield", [])
                        if not isinstance(subfields, list):
                            subfields = [subfields]
                        
                        for sf in subfields:
                            if sf.get("code") == subfield:
                                values.append(sf.get("#text", ""))
                    else:
                        # Return entire field if no subfield specified
                        subfields = field.get("subfield", [])
                        if not isinstance(subfields, list):
                            subfields = [subfields]
                        field_text = " ".join([sf.get("#text", "") for sf in subfields])
                        values.append(field_text)
            
            return "; ".join(values) if values else ""
        except Exception:
            return ""
    
    @staticmethod
    def map_bib_to_csv_row(bib: Dict) -> Dict[str, str]:
        """
        Map a bibliographic record to a CSV row.
        
        Args:
            bib: Bibliographic record from Alma API
            
        Returns:
            Dictionary mapping column headings to values
        """
        row = {heading: "" for heading in CSVExporter.COLUMN_HEADINGS}
        
        # Basic fields
        row["mms_id"] = bib.get("mms_id", "")
        row["dc:title"] = bib.get("title", "")
        
        # Extract MARC fields
        # 245$a - Title
        title_245 = CSVExporter.extract_marc_field(bib, "245", "a")
        if title_245:
            row["dc:title"] = title_245
        
        # 100$a or 110$a or 111$a - Creator
        creator = (CSVExporter.extract_marc_field(bib, "100", "a") or
                   CSVExporter.extract_marc_field(bib, "110", "a") or
                   CSVExporter.extract_marc_field(bib, "111", "a"))
        row["dc:creator"] = creator
        
        # 700$a - Contributors
        row["dc:contributor"] = CSVExporter.extract_marc_field(bib, "700", "a")
        
        # 650$a - Subjects (LCSH)
        subjects = CSVExporter.extract_marc_field(bib, "650", "a")
        if subjects:
            subject_list = subjects.split("; ")
            for i, subject in enumerate(subject_list[:12]):  # Max 12 subject columns
                if i == 0:
                    row["dc:subject"] = subject
                else:
                    row["dcterms:subject.dcterms:LCSH"] = subject
        
        # 260$b or 264$b - Publisher
        publisher = (CSVExporter.extract_marc_field(bib, "260", "b") or
                     CSVExporter.extract_marc_field(bib, "264", "b"))
        row["dcterms:publisher"] = publisher
        
        # 260$c or 264$c - Date
        date = (CSVExporter.extract_marc_field(bib, "260", "c") or
                CSVExporter.extract_marc_field(bib, "264", "c"))
        row["dc:date"] = date
        row["dcterms:issued"] = date
        
        # 520$a - Abstract/Description
        abstract = CSVExporter.extract_marc_field(bib, "520", "a")
        row["dc:description"] = abstract
        row["dcterms:abstract"] = abstract
        
        # 300$a - Extent
        extent = CSVExporter.extract_marc_field(bib, "300", "a")
        row["dcterms:extent"] = extent
        
        # 041$a - Language
        row["dc:language"] = CSVExporter.extract_marc_field(bib, "041", "a")
        
        # 856$u - URI
        row["dcterms:identifier.dcterms:URI"] = CSVExporter.extract_marc_field(bib, "856", "u")
        
        # Resource type
        row["dc:type"] = "Text"  # Default type
        row["dcterms:type.dcterms:DCMIType"] = "Text"
        
        return row
    
    @staticmethod
    def export_to_csv(bibs: List[Dict], filename: str) -> None:
        """
        Export bibliographic records to CSV.
        
        Args:
            bibs: List of bibliographic records
            filename: Output CSV filename
        """
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSVExporter.COLUMN_HEADINGS)
            writer.writeheader()
            
            for bib in bibs:
                row = CSVExporter.map_bib_to_csv_row(bib)
                writer.writerow(row)


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
        
        # API client
        self.api_client = None
        
        # UI Components
        self.api_key_field = ft.TextField(
            label="Alma API Key",
            password=True,
            can_reveal_password=True,
            width=400,
            hint_text="Enter your Alma API key"
        )
        
        self.search_field = ft.TextField(
            label="Title Search",
            width=400,
            hint_text="Enter title to search"
        )
        
        self.status_text = ft.Text(
            "",
            size=14,
            color=ft.colors.BLUE_700
        )
        
        self.results_text = ft.Text(
            "",
            size=14,
            selectable=True
        )
        
        self.progress_bar = ft.ProgressBar(
            visible=False,
            width=400
        )
        
        self.search_button = ft.ElevatedButton(
            "Search and Export",
            icon=ft.icons.SEARCH,
            on_click=self.search_and_export
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
                            color=ft.colors.BLUE_900
                        ),
                        ft.Divider(height=20, color=ft.colors.BLUE_200),
                        ft.Text(
                            "Search for digital titles in Alma and export metadata to CSV",
                            size=14,
                            color=ft.colors.GREY_700
                        ),
                        ft.Container(height=20),
                        self.api_key_field,
                        self.search_field,
                        ft.Container(height=10),
                        self.search_button,
                        self.progress_bar,
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
    
    def search_and_export(self, e):
        """Handle search and export button click."""
        # Validate inputs
        api_key = self.api_key_field.value.strip()
        search_query = self.search_field.value.strip()
        
        if not api_key:
            self.show_error("Please enter an Alma API key")
            return
        
        if not search_query:
            self.show_error("Please enter a search query")
            return
        
        # Initialize API client
        self.api_client = AlmaAPIClient(api_key)
        
        # Show progress
        self.progress_bar.visible = True
        self.search_button.disabled = True
        self.status_text.value = "Searching for digital titles..."
        self.status_text.color = ft.colors.BLUE_700
        self.results_text.value = ""
        self.page.update()
        
        try:
            # Search for bibliographic records
            bibs = self.api_client.search_bibs(search_query)
            
            if not bibs:
                self.show_info(f"No digital titles found matching: '{search_query}'")
                return
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"alma_export_{timestamp}.csv"
            
            # Update status
            self.status_text.value = f"Found {len(bibs)} record(s). Exporting to CSV..."
            self.page.update()
            
            # Export to CSV
            CSVExporter.export_to_csv(bibs, filename)
            
            # Show success
            self.show_success(
                f"Successfully exported {len(bibs)} record(s) to:\n{os.path.abspath(filename)}"
            )
            
        except Exception as ex:
            self.show_error(f"Error: {str(ex)}")
        
        finally:
            self.progress_bar.visible = False
            self.search_button.disabled = False
            self.page.update()
    
    def show_error(self, message: str):
        """Display error message."""
        self.status_text.value = "❌ " + message
        self.status_text.color = ft.colors.RED_700
        self.page.update()
    
    def show_success(self, message: str):
        """Display success message."""
        self.status_text.value = "✅ " + message
        self.status_text.color = ft.colors.GREEN_700
        self.results_text.value = ""
        self.page.update()
    
    def show_info(self, message: str):
        """Display info message."""
        self.status_text.value = "ℹ️ " + message
        self.status_text.color = ft.colors.BLUE_700
        self.results_text.value = ""
        self.page.update()


def main(page: ft.Page):
    """Main entry point for the Flet application."""
    AlmaExportApp(page)


if __name__ == "__main__":
    ft.app(target=main)
