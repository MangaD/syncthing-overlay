import tkinter as tk

class OverlayWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Syncthing Status")
        self.root.attributes("-alpha", 0.7)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        self.status_label = tk.Label(self.root, text="Fetching Syncthing status...", 
                                     font=("Arial", 10, "bold"), bg="black", fg="white", 
                                     justify="left", anchor="nw", padx=10, pady=10)
        self.status_label.pack(fill="both", expand=True)

        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag)

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def toggle(self):
        if self.root.state() == "withdrawn":
            self.root.deiconify()
        else:
            self.root.withdraw()

    def run(self):
        self.root.withdraw()  # Start with the overlay hidden
        self.root.mainloop()

    def stop(self):
        self.root.quit()
