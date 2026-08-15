import tkinter as tk
from gui import ArrowAutomationGUI

def main():
    root = tk.Tk()
    app = ArrowAutomationGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
