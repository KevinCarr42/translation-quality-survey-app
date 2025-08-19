# Translation Quality Survey App

A simple GUI application for ranking translation quality across multiple translation models.

## Prerequisites

- Python 3.7 or higher
- Git (for cloning the repository)
- Windows, macOS, or Linux

## Features

- **Random question order**: Questions are presented in random order each session
- **Randomized translation order**: Translation outputs are shuffled for each question
- **Clean interface**: Rankings always start blank (no memory of previous answers)
- **Flexible ranking**: Choose from: good, bad, best, unknown, or leave blank
- **Immediate saving**: Each save creates a new row (allows re-ranking same questions)
- **Progress tracking**: Shows current position and question ID
- **Cross-platform**: Works on Windows, macOS, and Linux

## Quick Start

### Option 1: Run the Pre-built Executable (Recommended)
1. Download `TranslationSurvey.exe` and `merged_translation_data.csv`
2. Place both files in the same folder
3. Double-click `TranslationSurvey.exe`
4. Results are saved to `translation_quality_results.csv` in the same folder

### Option 2: Run from Source
```bash
# Clone the repository
git clone <your-repo-url>
cd translation-quality-survey-app

# Install dependencies
pip install -r requirements.txt

# Run the application
python survey_app.py
```

### Option 3: Build from Source
```bash
# Clone the repository
git clone <your-repo-url>
cd translation-quality-survey-app

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build executable
python build_exe.py

# Find your executable in:
# dist/TranslationSurvey.exe
```

## Usage

1. **Source Text**: The original text to be translated appears at the top
2. **Translations**: Multiple translation outputs are shown in random order
3. **Ranking**: Select from dropdown: good, bad, best, unknown, or leave blank
4. **Auto-save**: Rankings are automatically saved when you click Next/Previous (if any rankings were made)
5. **Manual Save**: Click "Save Rankings" to immediately save current rankings to CSV

## Output Format

Results are saved to `translation_quality_results.csv` with the same structure as `merged_translation_data.csv`:
- `source`: Original source text
- `translation_bureau`, `m2m100_418m_base`, `m2m100_418m_finetuned`, etc.: Ranking for each model (good/bad/best/unknown or blank)
- `corpus_type`: Type of corpus
- Each time you save, a new row is added (duplicates allowed for re-ranking)

## Development

### Building from Another Computer

To build this project on a different machine:

1. **Clone and setup:**
   ```bash
   git clone <your-repo-url>
   cd translation-quality-survey-app
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Mac/Linux
   ```

2. **Install and build:**
   ```bash
   pip install -r requirements.txt
   python build_exe.py
   ```

3. **Alternative direct build:**
   ```bash
   pyinstaller --onefile --windowed --name=TranslationSurvey --add-data=merged_translation_data.csv;. survey_app.py
   ```

### Required Files for Building
- `survey_app.py` - Main application code
- `merged_translation_data.csv` - Translation data
- `requirements.txt` - Python dependencies
- `build_exe.py` - Build script

### Output Structure
After building:
- Executable: `dist/TranslationSurvey.exe`
- Distribute with: `merged_translation_data.csv`
- Results saved to: `translation_quality_results.csv`

## Data Format

Input file `merged_translation_data.csv` should have:
- `source`: Source text column
- Translation model columns (e.g., `translation_bureau`, `m2m100_418m_base`, etc.)
- `corpus_type`: Type of corpus (optional)