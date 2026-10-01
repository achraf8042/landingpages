
import PyInstaller.__main__
import os
import sys
# Define base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define arguments
args = [
    'main.py',
    '--name=DigiSpherEMR',
    '--icon=app_icon.ico',
    '--noconsole',
    '--onefile',
    '--clean',
    
    # Hidden imports requested by user
    '--hidden-import=PySide6',
    '--hidden-import=pandas',
    '--hidden-import=reportlab',
    
    # Ensure standard encodings are included (often needed)
    '--hidden-import=encodings',
    
    # PyInstaller accepts source:dest on each supported platform.
    '--add-data=app_icon.ico:.',
    '--add-data=app_icon.png:.',
    '--add-data=dc.ico:.',
    '--add-data=utils/translations/fr.json:utils/translations',
]

# Run PyInstaller
print("Starting build process...")
PyInstaller.__main__.run(args)
print("Build complete. Check 'dist/DigiSpherEMR'")
