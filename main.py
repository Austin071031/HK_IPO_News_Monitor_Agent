import sys
import os
import tkinter as tk

# Ensure the current directory is in sys.path so we can import src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.gui import CombinedApp

def main():
    root = tk.Tk()
    app = CombinedApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
