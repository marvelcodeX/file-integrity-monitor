"""
File Integrity Monitor - Entry Point
Launches the CustomTkinter UI application.
"""
 
import sys
import os
 
# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from ui.app import FIMApp
 
 
def main():
    app = FIMApp()
    app.mainloop()
 
 
if __name__ == "__main__":
    main()
 