import tkinter as tk
from functools import partial


class Calculator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Calculator")
        self.root.geometry("300x400")

        # 수식 입력 및 결과 출력 화면
        self.expression = tk.Entry(self.root, width=20, font=('Arial', 20), bd=5, justify="right")
        self.expression.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

        # 계산기 버튼
        self.buttons = [
            "C", "DEL", "/", "*",
            "7", "8", "9", "-",
            "4", "5", "6", "+",
            "1", "2", "3", "=",
            "0", ".", "+/-"
        ]
        self.create_buttons()

    def create_buttons(self):
        row, col = 1, 0
        for button_text in self.buttons:
            if col == 4:
                col = 0
                row += 1
            button = tk.Button(self.root, text=button_text, font=('Arial', 15), width=5, height=2, bd=5)
            button.grid(row=row, column=col, padx=5, pady=5)
            button.bind('<Button-1>', partial(self.button_click, button_text))
            col += 1

    def button_click(self, button_text, event):
        if button_text == "C":
            self.expression.delete(0, tk.END)
        elif button_text == "DEL":
            self.expression.delete(len(self.expression.get())-1, tk.END)
        elif button_text == "=":
            result = self.calculate(self.expression.get())
            self.expression.delete(0, tk.END)
            self.expression.insert(0, str(result))
        else:
            self.expression.insert(tk.END, button_text)

    def calculate(self, expression):
        try:
            return str(eval(expression))
        except:
            return "ERROR"

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    calc = Calculator()
    calc.run()