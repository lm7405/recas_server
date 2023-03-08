from typing import Union, Dict, Tuple
import re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
port = 1234
origins = [
    "http://127.0.0.1:" + str(port),
    "http://localhost:" + str(port)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/calculator/{text}")
async def calculator_api(text):
    result = calculator(text)
    return HTMLResponse(content=result, status_code=200)


class CalculatorOperate:
    n1: float
    n2: float
    message: str

    def __call__(self, first_number, second_number) -> Tuple[Union[None, float], str]:
        self.n1 = first_number
        self.n2 = second_number
        self.message = ""
        if self.is_not_error():
            return self.calculate(), self.message
        return None, self.message

    def calculate(self) -> float:
        raise

    def is_not_error(self) -> bool:
        raise

    def print_message(self, text):
        # print(text)
        self.message += text


class Plus(CalculatorOperate):
    def calculate(self):
        return self.n1 + self.n2

    def is_not_error(self):
        return True


class Minus(CalculatorOperate):
    def calculate(self):
        return self.n1 - self.n2

    def is_not_error(self):
        return True


class Multiply(CalculatorOperate):
    def calculate(self):
        return self.n1 * self.n2

    def is_not_error(self):
        return True


class Divide(CalculatorOperate):
    def calculate(self):
        return self.n1 / self.n2

    def is_not_error(self):
        if self.n2 == 0:
            self.print_message("0으로 나눌 수 없습니다.\n")
            return False
        return True


class Square(CalculatorOperate):
    def calculate(self):
        return self.n1 ** self.n2

    def is_not_error(self):
        if self.n2 == 0:
            self.print_message("0으로 나눌 수 없습니다.\n")
            return False
        return True


def calculator(text):
    output_text = ""
    operator_table: Dict[str, CalculatorOperate] = {
        "+": Plus(),
        "-": Minus(),
        "*": Multiply(),
        "/": Divide(),
        "^": Square(),
    }

    p = re.compile('\s?(\S+)\s+(\S+)\s+(\S+)\s?')

    input_text = text
    m = p.search(input_text)
    if m is None:
        output_text += "\"숫자 연산자 숫자\"의 형태로 입력되어야 합니다.\n"
        return output_text

    operator = m.group(2)

    if operator not in operator_table:
        output_text += operator + "는 적합한 연산자가 아닙니다.\n"
        output_text += "지원 연산자는 다음과 같습니다.\n"
        output_text += " ".join(operator_table.keys()) + "\n"
        return output_text

    try:
        n1 = float(m.group(1))
    except:
        output_text += m.group(1) + "는 숫자가 아닙니다." + "\n"
        return output_text

    try:
        n2 = float(m.group(3))
    except:
        output_text += m.group(3) + "는 숫자가 아닙니다." + "\n"
        return output_text

    result, message = operator_table[operator](n1, n2)
    output_text += message
    if result is not None:
        if result % 1 == 0:
            result_text = str(int(result))
        else:
            result = round(result, 10)
            result_text = str(result)
        output_text += input_text + "\n = " + result_text + "\n"

        return output_text
    output_text += "something wrong at calculating\n"
    return output_text


if __name__ is "__main__":
    run_mode = 1
    if run_mode is 0:

        while True:
            input_text = input()
            print(calculator(input_text))

    elif run_mode is 1:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=port)
