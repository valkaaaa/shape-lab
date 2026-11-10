"""Безопасный вычислитель математических выражений."""
import ast
import math
import operator
import re

__all__ = ["eval_math", "SAFE_NAMES", "MAX_LEN", "MAX_DEPTH"]


SAFE_NAMES = {
    "pi": math.pi, "e": math.e, "tau": math.tau,
    "sqrt": math.sqrt, "pow": pow, "hypot": math.hypot,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "atan2": math.atan2,
    "radians": math.radians, "degrees": math.degrees,
    "sin_deg": lambda x: math.sin(math.radians(x)),
    "cos_deg": lambda x: math.cos(math.radians(x)),
    "tan_deg": lambda x: math.tan(math.radians(x)),
    "asin_deg": lambda x: math.degrees(math.asin(x)),
    "acos_deg": lambda x: math.degrees(math.acos(x)),
    "atan_deg": lambda x: math.degrees(math.atan(x)),
    "log": math.log, "log10": math.log10, "log2": math.log2, "exp": math.exp,
    "abs": abs, "round": round, "min": min, "max": max,
    "floor": math.floor, "ceil": math.ceil,
}
BIN_OPS = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.Pow: operator.pow, ast.Mod: operator.mod,
           ast.FloorDiv: operator.floordiv}
UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
MAX_LEN, MAX_DEPTH = 200, 30


def eval_math(expr: str) -> float:
    if not isinstance(expr, str):
        raise ValueError("ожидалась строка")
    expr = expr.strip().replace("^", "**")
    if not expr:
        raise ValueError("пустое выражение")
    if len(expr) > MAX_LEN:
        raise ValueError(f"выражение длиннее {MAX_LEN} символов")
    if re.fullmatch(r"[-+]?\d+,\d+", expr):
        expr = expr.replace(",", ".")
    try:
        tree = ast.parse(expr, mode="eval").body
    except SyntaxError as e:
        raise ValueError(f"синтаксическая ошибка: {e.msg}")
    try:
        result = _eval_node(tree, 0)
    except ZeroDivisionError:
        raise ValueError("деление на ноль")
    except OverflowError:
        raise ValueError("результат слишком велик")
    except ValueError as e:
        if str(e) in ("math domain error", "math range error"):
            raise ValueError("недопустимый аргумент функции")
        raise
    if not isinstance(result, (int, float)) or isinstance(result, bool):
        raise ValueError("результат не является числом")
    if not math.isfinite(result):
        raise ValueError("результат не является конечным числом")
    return float(result)


def _eval_node(node, depth):
    if depth > MAX_DEPTH:
        raise ValueError("выражение слишком сложное")
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError(f"литерал недопустим: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id in SAFE_NAMES:
            return SAFE_NAMES[node.id]
        raise ValueError(f"неизвестное имя: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
        return BIN_OPS[type(node.op)](_eval_node(node.left, depth + 1),
                                      _eval_node(node.right, depth + 1))
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
        return UNARY_OPS[type(node.op)](_eval_node(node.operand, depth + 1))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("можно вызывать только простые функции")
        fn = SAFE_NAMES.get(node.func.id)
        if not callable(fn):
            raise ValueError(f"неизвестная функция: {node.func.id}")
        if node.keywords:
            raise ValueError("именованные аргументы не поддерживаются")
        return fn(*[_eval_node(a, depth + 1) for a in node.args])
    raise ValueError("недопустимая конструкция в выражении")