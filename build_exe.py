import os
import subprocess
import sys

def build_executable():
    """Build the survey app as a standalone executable"""
    
    print("Building Translation Quality Survey executable...")
    
    # Install requirements if not already installed
    try:
        import pandas
        import tkinter
    except ImportError:
        print("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # PyInstaller command with pandas fixes
    cmd = [
        "pyinstaller",
        "--onefile",           # Create a single executable file
        "--windowed",          # No console window (GUI app)
        "--name=TranslationSurvey",  # Name of the executable
        "--add-data=merged_translation_data.csv;.",  # Include the CSV data file
        "--hidden-import=pandas._libs.window.aggregations",  # Fix pandas DLL import
        "--hidden-import=pandas._libs.reduction",
        "--hidden-import=pandas._libs.groupby",
        "--hidden-import=pandas._libs.ops",
        "--hidden-import=pandas._libs.properties",
        "--hidden-import=pandas._libs.reshape",
        "--hidden-import=pandas._libs.sparse",
        "--hidden-import=pandas._libs.join",
        "--hidden-import=pandas._libs.indexing",
        "--collect-data=pandas",  # Include pandas data files
        "--collect-binaries=pandas",  # Include pandas binary files
        "survey_app.py"
    ]
    
    print("Running PyInstaller...")
    print(" ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        print("\nBuild successful!")
        print("Executable created: dist/TranslationSurvey.exe")
        print("\nTo distribute:")
        print("1. Copy dist/TranslationSurvey.exe to any folder")
        print("2. Copy merged_translation_data.csv to the same folder")
        print("3. Run TranslationSurvey.exe")
        print("4. Results will be saved to translation_quality_results.csv in the same folder")

    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    build_executable()