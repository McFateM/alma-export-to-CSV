# Alma Export to CSV - Program Flow Diagram

## Application Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION STARTUP                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Load .env file  │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Setup Logging    │
                    │ - File (DEBUG)   │
                    │ - Console (INFO) │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Start Flet App  │
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (Flet)                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  1. API Key Field (TextField)                           │    │
│  │     - Password field with reveal option                 │    │
│  │     - Auto-filled from ALMA_API_KEY env var if present  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  2. CSV File Selection                                  │    │
│  │     ┌──────────────┐  ┌─────────────────────-┐          │    │
│  │     │ File Display │  │ "Select CSV File"    │          │    │
│  │     │ (TextField)  │  │  Button (FilePicker) │          │    │
│  │     └──────────────┘  └─────────────────────-┘          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  3. Row Limit Options                                   │    │
│  │     ┌────────────────────────────────────┐              │    │
│  │     │ ☐ Limit number of rows to process  │              │    │
│  │     └────────────────────────────────────┘              │    │
│  │     ┌──────────────┐                                    │    │
│  │     │ Number Field │ (default: 10)                      │    │
│  │     └──────────────┘                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  4. Export Button                                       │    │
│  │     ┌─────────────────────┐                             │    │
│  │     │ "Export Records" 📥 │                             │    │
│  │     └─────────────────────┘                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  5. Status Display                                      │    │
│  │     - Progress bar                                      │    │
│  │     - Status text (colored messages)                    │    │
│  │     - Results text                                      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXPORT PROCESS FLOW                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Validate Inputs  │
                    │ - API Key exists │
                    │ - CSV file set   │
                    └──────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                NO  ▼                   ▼  YES
            ┌────────────┐      ┌──────────────-┐
            │ Show Error │      │  Initialize   │
            │   Return   │      │ AlmaAPIClient │
            └────────────┘      └──────────────-┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │   Read CSV File  │
                              └──────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CSV READING PROCESS                          │
│                                                                 │
│  1. Detect delimiter (comma, tab, semicolon)                    │
│  2. Read first row                                              │
│  3. Determine if header row exists                              │
│  4. Find MMS ID column (looks for "mms" + "id" in header)       │
│  5. Read all data rows:                                         │
│     ┌────────────────────────────────────────────-─┐            │
│     │ For each row:                                │            │
│     │   - Get value from MMS ID column             │            │
│     │   - Strip whitespace                         │            │
│     │   - Skip if starts with # (comment)          │            │
│     │   - Skip if empty or pure text               │            │
│     │   - Add valid MMS IDs to list                │            │
│     └─────────────────────────────────────────────-┘            │
│  6. Log count and first few MMS IDs                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Apply Row Limit? │
                    └──────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                NO  ▼                   ▼  YES
         ┌──────────────┐      ┌──────────────┐
         │ Use All IDs  │      │ Limit to X   │
         └──────────────┘      │ First IDs    │
                               └──────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              BIBLIOGRAPHIC RECORD RETRIEVAL                     │
│                                                                 │
│  For each MMS ID in list:                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. Clean MMS ID (strip whitespace)                      │   │
│  │                                                          │   │
│  │  2. Call Alma API via almapipy                           │   │
│  │     ┌──────────────────────────────────────────┐         │   │
│  │     │ self.cnxn.bibs.catalog.get(              │         │   │
│  │     │     mms_id                               │         │   │
│  │     │ )                                        │         │   │
│  │     │                                          │         │   │
│  │     │ Returns Dublin Core (DC) format record   │         │   │
│  │     │ with DC XML in 'anies' field             │         │   │
│  │     └──────────────────────────────────────────┘         │   │
│  │                                                          │   │
│  │  3. Check response:                                      │   │
│  │     ┌─────────────┴─────────────┐                        │   │
│  │     │                           │                        │   │
│  │  SUCCESS                      FAIL                       │   │
│  │     │                           │                        │   │
│  │     ▼                           ▼                        │   │
│  │  ┌─────────┐            ┌──────────────┐                 │   │
│  │  │ Add to  │            │ Log warning  │                 │   │
│  │  │all_bibs │            │ Add to failed│                 │   │
│  │  │  list   │            │     list     │                 │   │
│  │  └─────────┘            └──────────────┘                 │   │
│  │                                                          │   │
│  │  4. Log progress every 10 records                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Final: Log total success/fail counts                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Any records    │
                    │   retrieved?     │
                    └──────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                NO  ▼                   ▼  YES
            ┌────────────┐      ┌─────────────-─┐
            │ Show Error │      │ Export to CSV │
            │   Return   │      └─────────────-─┘
            └────────────┘              │
                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CSV EXPORT PROCESS                           │
│                                                                 │
│  1. Generate filename: alma_export_YYYYMMDD_HHMMSS.csv          │
│                                                                 │
│  2. Write CSV file:                                             │
│     ┌─────────────────────────────────────────────┐             │
│     │ - Write 67 column headers                   │             │
│     │                                             │             │
│     │ For each bibliographic record:              │             │
│     │   ┌──────────────────────────────────────┐  │             │
│     │   │ Parse Dublin Core XML from 'anies'   │  │             │
│     │   │ field and extract DC elements:       │  │             │
│     │   │                                      │  │             │
│     │   │ Standard DC fields:                  │  │             │
│     │   │   - dc:title                         │  │             │
│     │   │   - dc:creator                       │  │             │
│     │   │   - dc:contributor                   │  │             │
│     │   │   - dc:subject                       │  │             │
│     │   │   - dc:description                   │  │             │
│     │   │   - dc:identifier                    │  │             │
│     │   │   - dc:date                          │  │             │
│     │   │   - dc:type                          │  │             │
│     │   │   - dc:format                        │  │             │
│     │   │   - dc:language                      │  │             │
│     │   │   - dc:relation                      │  │             │
│     │   │   - dc:coverage                      │  │             │
│     │   │   - dc:rights                        │  │             │
│     │   │   - dc:source                        │  │             │
│     │   │                                      │  │             │
│     │   │ DCTERMS fields:                      │  │             │
│     │   │   - dcterms:alternative              │  │             │
│     │   │   - dcterms:tableOfContents          │  │             │
│     │   │   - dcterms:abstract                 │  │             │
│     │   │   - dcterms:publisher                │  │             │
│     │   │   - dcterms:created                  │  │             │
│     │   │   - dcterms:issued                   │  │             │
│     │   │   - dcterms:dateAccepted             │  │             │
│     │   │   - dcterms:dateSubmitted            │  │             │
│     │   │   - dcterms:extent                   │  │             │
│     │   │   - dcterms:medium                   │  │             │
│     │   │   - dcterms:isPartOf                 │  │             │
│     │   │   - dcterms:spatial                  │  │             │
│     │   │   - dcterms:temporal                 │  │             │
│     │   │   - dcterms:provenance               │  │             │
│     │   │   - dcterms:bibliographicCitation    │  │             │
│     │   │                                      │  │             │
│     │   │ Custom Grinnell fields:              │  │             │
│     │   │   - compoundrelationship             │  │             │
│     │   │   - googlesheetsource                │  │             │
│     │   │   - dginfo                           │  │             │
│     │   │                                      │  │             │
│     │   │ Also uses top-level API fields:      │  │             │
│     │   │   - mms_id                           │  │             │
│     │   │   - originating_system_id            │  │             │
│     │   │   - title                            │  │             │
│     │   │   - author                           │  │             │
│     │   │   - date_of_publication              │  │             │
│     │   │   - publisher_const                  │  │             │
│     │   └──────────────────────────────────────┘  │             │
│     │   │                                         │             │
│     │   ▼                                         │             │
│     │   ┌──────────────────────────────────────┐  │             │
│     │   │ Map to CSV row with 67 columns       │  │             │
│     │   └──────────────────────────────────────┘  │             │
│     │   │                                         │             │
│     │   ▼                                         │             │
│     │   ┌──────────────────────────────────────┐  │             │
│     │   │ Write row to CSV                     │  │             │
│     │   └──────────────────────────────────────┘  │             │
│     │                                             │             │
│     │   Log progress every 10 records             │             │
│     └─────────────────────────────────────────────┘             │
│                                                                 │
│  3. Log file size and completion                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Calculate total  │
                    │ execution time   │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Show Success     │
                    │ Message with:    │
                    │ - Record count   │
                    │ - Output file    │
                    │ - Full path      │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Reset UI         │
                    │ - Hide progress  │
                    │ - Enable buttons │
                    └──────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                        LOGGING SYSTEM                           │
│                                                                 │
│  File Logging (DEBUG level):                                    │
│    Location: logs/alma_export_YYYYMMDD_HHMMSS.log               │
│    ┌──────────────────────────────────────────┐                 │
│    │ - Detailed API interactions              │                 │
│    │ - MMS ID processing details              │                 │
│    │ - Dublin Core XML parsing                │                 │
│    │ - DC field extraction                    │                 │
│    │ - CSV row mapping                        │                 │
│    │ - Error stack traces                     │                 │
│    │ - Performance metrics                    │                 │
│    └──────────────────────────────────────────┘                 │
│                                                                 │
│  Console Logging (INFO level):                                  │
│    ┌──────────────────────────────────────────┐                 │
│    │ - Application lifecycle events           │                 │
│    │ - User actions                           │                 │
│    │ - Progress updates                       │                 │
│    │ - Success/error summaries                │                 │
│    └──────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                     KEY COMPONENTS                              │
│                                                                 │
│  AlmaAPIClient:                                                 │
│    - Manages Alma API connection via almapipy                   │
│    - Retrieves bibliographic records in DC format               │
│    - Handles pagination and errors                              │
│                                                                 │
│  CSVExporter:                                                   │
│    - Defines 67 standard columns                                │
│    - Parses Dublin Core XML from 'anies' field                  │
│    - Extracts DC and DCTERMS elements                           │
│    - Extracts custom namespace fields                           │
│    - Maps data to standardized CSV format                       │
│    - Writes output files                                        │
│                                                                 │
│  AlmaExportApp:                                                 │
│    - Main Flet UI controller                                    │
│    - Handles user interactions                                  │
│    - Orchestrates export workflow                               │
│    - Manages UI state and feedback                              │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│              DUBLIN CORE XML STRUCTURE                          │
│                                                                 │
│  Records are in Dublin Core (DC) format, NOT MARC               │
│                                                                 │
│  API Response Structure:                                        │
│  ┌────────────────────────────────────────────────────────--──┐ │
│  │ {                                                          │ │
│  │   "mms_id": "991011506418804641",                          │ │
│  │   "record_format": "dcap01",                               │ │
│  │   "title": "Data Repository...",                           │ │
│  │   "author": "Weinman, Jerod J.",                           │ │
│  │   "date_of_publication": "2014-10-21",                     │ │
│  │   "publisher_const": "Grinnell College",                   │ │
│  │   "originating_system_id": "991011506418804641",           │ │
│  │   ...                                                      │ │
│  │   "anies": [                                               │ │
│  │     "<record xmlns:dc=\"http://purl.org/dc/elements/1.1/\" │ │
│  │              xmlns:dcterms=\"http://purl.org/dc/terms/\"   │ │
│  │              xmlns:ns0=\"http://alma.exlibrisgroup.com/dc  │ │
│  │                                 /01GCL_INST\">             │ │
│  │       <dc:title>...</dc:title>                             │ │
│  │       <dc:creator>...</dc:creator>                         │ │
│  │       <dc:subject>...</dc:subject>                         │ │
│  │       <dcterms:abstract>...</dcterms:abstract>             │ │
│  │       <ns0:compoundrelationship>...</ns0:...>              │ │
│  │       ...                                                  │ │
│  │     </record>"                                             │ │
│  │   ]                                                        │ │
│  │ }                                                          │ │
│  └─────────────────────────────────────────────────────────--─┘ │
│                                                                 │
│  DC Extraction Process:                                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. Extract XML string from 'anies' array                 │   │
│  │ 2. Parse XML with ElementTree                            │   │
│  │ 3. Register namespaces:                                  │   │
│  │    - dc: http://purl.org/dc/elements/1.1/                │   │
│  │    - dcterms: http://purl.org/dc/terms/                  │   │
│  │    - ns0: http://alma.exlibrisgroup.com/dc/{inst}        │   │
│  │ 4. Find all elements matching namespace:element          │   │
│  │ 5. Extract text content from each element                │   │
│  │ 6. Return as list (for multi-valued fields)              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Example DC Element Extraction:                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ dc:subject → Search for:                                 │   │
│  │   {http://purl.org/dc/elements/1.1/}subject              │   │
│  │                                                          │   │
│  │ dcterms:abstract → Search for:                           │   │
│  │   {http://purl.org/dc/terms/}abstract                    │   │
│  │                                                          │   │
│  │ ns0:compoundrelationship → Search for:                   │   │
│  │   {http://alma.exlibrisgroup.com/dc/01GCL_INST}compound  │   │
│  │                                      relationship        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING                               │
│                                                                 │
│  ┌────────────────────┬──────────────────────────────────────┐  │
│  │ Error Type         │ Handling Strategy                    │  │
│  ├────────────────────┼──────────────────────────────────────┤  │
│  │ Missing API Key    │ Show error, prevent export           │  │
│  │ No CSV file        │ Show error, prevent export           │  │
│  │ Invalid CSV format │ Log error with details, abort        │  │
│  │ No MMS IDs found   │ Show error, abort export             │  │
│  │ API errors (404)   │ Log warning, continue with next      │  │
│  │ API errors (400)   │ Log warning, continue with next      │  │
│  │ Network errors     │ Log error, add to failed list        │  │
│  │ CSV write error    │ Log error, show to user, abort       │  │
│  └────────────────────┴──────────────────────────────────────┘  │
│                                                                 │
│  All errors are:                                                │
│    - Logged with full details                                   │
│    - Shown to user with clear messages                          │
│    - Handled gracefully without crashing                        │
└─────────────────────────────────────────────────────────────────┘
