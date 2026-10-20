import ast
import operator
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

load_dotenv()
client = genai.Client()
MODEL = "gemini-3.5-flash-lite"
MAX_STEPS = 5

# ---------- Tool ----------
OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg,
}

def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")

def calculator(expression: str):
    return _eval(ast.parse(expression, mode="eval").body)

TOOLS = {"calculator": calculator}

calc_decl = types.FunctionDeclaration(
    name="calculator",
    description="Evaluate a math expression like '12*(3+4)'. Supports + - * / ** and parentheses.",
    parameters=types.Schema(
        type="OBJECT",
        properties={"expression": types.Schema(type="STRING", description="Math expression")},
        required=["expression"],
    ),
)
config = types.GenerateContentConfig(
    tools=[types.Tool(function_declarations=[calc_decl])],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)

# ---------- Model call with retry ----------
def call_model(contents):
    for attempt in range(4):
        try:
            return client.models.generate_content(model=MODEL, contents=contents, config=config)
        except errors.ServerError as e:
            wait = 2 ** attempt * 3
            print(f"Server busy ({e.code}), {wait}s baad retry...")
            time.sleep(wait)
    raise RuntimeError("Model baar-baar fail hua")

# ---------- Agent loop ----------
def run_agent(question: str):
    contents = [types.Content(role="user", parts=[types.Part(text=question)])]
    for step in range(1, MAX_STEPS + 1):
        response = call_model(contents)
        content = response.candidates[0].content
        calls = [p.function_call for p in (content.parts or []) if p.function_call]

        if not calls:                       # koi tool nahi maanga = final answer
            print("FINAL:", response.text)
            return response.text

        contents.append(content)            # model ka tool-call message history me
        parts = []
        for call in calls:
            print(f"[step {step}] TOOL CALL: {call.name}({dict(call.args)})")
            try:
                result = {"result": TOOLS[call.name](**call.args)}
            except Exception as e:
                print(f"[step {step}] TOOL ERROR: {e}")
                result = {"error": str(e)}
            parts.append(types.Part.from_function_response(name=call.name, response=result))
        contents.append(types.Content(role="user", parts=parts))

    raise RuntimeError(f"{MAX_STEPS} steps me final answer nahi mila")

if __name__ == "__main__":
       run_agent("(125 * 48) + 17 ka answer kya hai? Phir usko 3 se divide karo.")