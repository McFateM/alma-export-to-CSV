# Alma Digital Title Export to CSV

A Flet-based desktop application that retrieves bibliographic records from Alma API using MMS IDs from a CSV file and exports metadata to CSV files with standardized column headings.

## Features

- � **CSV Input**: Load MMS IDs from a CSV file for batch processing
- 📊 **CSV Export**: Export bibliographic metadata with 67 standardized column headings
- 🎨 **User-Friendly GUI**: Simple single-page interface built with Flet
- 🔒 **Secure**: API key support with optional environment variable configuration
- � **Comprehensive Logging**: Detailed file and console logging for debugging and auditing
- �📦 **Easy Setup**: Virtual environment and quick-launch script included
- 🚀 **Powered by almapipy**: Uses the official almapipy library from UC Davis Library

## Requirements

- Python 3.8 or higher
- Alma API key (read-only access to bibliographic records)
- Internet connection
- CSV file containing MMS IDs (with header row)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/McFateM/alma-export-to-CSV.git
cd alma-export-to-CSV
```

2. (Optional) Create a `.env` file with your API key:
```bash
cp .env.example .env
# Edit .env and add your ALMA_API_KEY
```

## CSV Input File Format

Your input CSV file should contain MMS IDs. The application will automatically detect a column with "mms" and "id" in the header name (case-insensitive). If no such header is found, it will use the first column.

Example `sample_mms_ids.csv`:
```csv
mms_id
991234567890104641
991234567890204641
991234567890304641
```

## Usage

### Quick Launch (Recommended)

Simply run the provided bash script:

```bash
./run.sh
```

This script will:
- Create a virtual environment (`.venv`) if it doesn't exist
- Install all required dependencies
- Launch the Flet application

### Manual Launch

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# OR
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 app.py
```

## Using the Application

1. **Enter API Key**: 
   - Enter your Alma API key in the "Alma API Key" field
   - Or set `ALMA_API_KEY` in your `.env` file to pre-fill this field

2. **Select CSV File**:
   - Click "Select CSV File" button
   - Choose a CSV file containing MMS IDs
   - The file name will appear in the text field

3. **Export**:
   - Click "Export Records" button
   - The app will retrieve all records from Alma for the given MMS IDs
   - Results will be exported to a CSV file with timestamp: `alma_export_YYYYMMDD_HHMMSS.csv`
   - Check the status messages for progress updates

## Logging

The application creates detailed logs in the `logs/` directory:
- Each run creates a new log file: `logs/alma_export_YYYYMMDD_HHMMSS.log`
- Console output shows INFO level and above
- Log files contain DEBUG level details including:
  - API requests and responses
  - MARC field extraction
  - CSV export progress
  - Error details with stack traces

## CSV Output Format

The exported CSV files include 67 columns with standardized headings compatible with digital repository workflows:

- Basic metadata: `mms_id`, `dc:title`, `dc:creator`, `dc:contributor`
- Subjects: `dc:subject`, multiple `dcterms:subject.dcterms:LCSH` fields
- Descriptive: `dc:description`, `dcterms:abstract`, `dcterms:extent`
- Publishing: `dcterms:publisher`, `dc:date`, `dcterms:issued`
- Technical: `dc:format`, `dc:language`, `dcterms:identifier.dcterms:URI`
- And many more fields for comprehensive metadata export

See the full column structure: [verified_CSV_headings_for_Alma-D.csv](https://github.com/McFateM/manage-digital-ingest-flet-oo/blob/main/_data/verified_CSV_headings_for_Alma-D.csv)

## Getting an Alma API Key

1. Log in to the Ex Libris Developer Network: https://developers.exlibrisgroup.com/
2. Navigate to your institution's API management
3. Create a new API key with read access to bibliographic records
4. Copy the API key for use in the application

## Troubleshooting

### "API request failed" error
- Verify your API key is correct and has proper permissions
- Check your internet connection
- Ensure the Alma API base URL is correct for your region

### No results found
- Try a broader search query
- Verify that your institution has digital titles in Alma
- Check that the records are not suppressed

### Dependencies installation fails
- Ensure you have Python 3.8 or higher installed
- Try upgrading pip: `pip install --upgrade pip`
- Check your internet connection

## Project Structure

```
alma-export-to-CSV/
├── app.py              # Main Flet application
├── run.sh              # Quick launch script
├── requirements.txt    # Python dependencies
├── .env.example        # Example environment configuration
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Dependencies

- **flet**: Modern GUI framework for Python
- **requests**: HTTP library for API calls
- **python-dotenv**: Environment variable management

## License

[Add your license information here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on GitHub.
