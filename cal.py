import tkinter as tk
from tkinter import messagebox

class FancyCalculator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Fancy Calculator")
        self.result_var = tk.StringVar()

        self.display = tk.Entry(self.root, textvariable=self.result_var, font=("Arial", 18), justify="right")
        self.display.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

        buttons = [
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("=", 4, 2), ("+", 4, 3),
            ("C", 5, 0) 
        ]

        for (text, row, col) in buttons:
            button = tk.Button(self.root, text=text, font=("Arial", 16), command=lambda t=text: self.on_button_click(t))
            button.grid(row=row, column=col, padx=10, pady=10)

    def on_button_click(self, value):
        if value == "=":
            try:
                result = eval(self.result_var.get())
                self.result_var.set(str(result))
            except Exception as e:
                messagebox.showerror("Error", f"Invalid expression: {e}")
        elif value == "C":
            self.result_var.set("") 
        else:
            current_text = self.result_var.get()
            self.result_var.set(current_text + value)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    calculator = FancyCalculator()
    calculator.run()
