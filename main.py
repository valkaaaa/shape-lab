import ast
import math
import operator
import re
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog


# ═══════════════════════════════════════════════════════════════════
# 1. БЕЗОПАСНЫЙ ВЫЧИСЛИТЕЛЬ ВЫРАЖЕНИЙ
# ═══════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════
# 2. TOOLTIP
# ═══════════════════════════════════════════════════════════════════
class Tooltip:
    def __init__(self, root, offset=(16, 16)):
        self.root = root
        self.offset = offset
        self.win = None
        self.label = None
        self._last_text = None

    def show(self, x_root, y_root, text):
        if self.win is None:
            self.win = tk.Toplevel(self.root)
            self.win.wm_overrideredirect(True)
            try:
                self.win.attributes("-topmost", True)
            except tk.TclError:
                pass
            self.label = tk.Label(
                self.win, background="#fffde7", foreground="#222",
                relief="solid", borderwidth=1,
                font=("Consolas", 9), justify="left", padx=6, pady=4)
            self.label.pack()
        if text != self._last_text:
            self.label.config(text=text)
            self._last_text = text
        self.win.wm_geometry(f"+{x_root + self.offset[0]}+{y_root + self.offset[1]}")

    def hide(self):
        if self.win is not None:
            self.win.destroy()
            self.win = None
            self.label = None
            self._last_text = None


# ═══════════════════════════════════════════════════════════════════
# 3. МОДЕЛИ ФИГУР
# ═══════════════════════════════════════════════════════════════════
class Shape:
    name = "Фигура"
    FIELDS = []
    fill_color = "#b0bec5"
    outline_color = "#37474f"

    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.rotation = 0.0

    def set_position(self, x, y):
        self.x, self.y = float(x), float(y)

    def _rp(self, lx, ly):
        rot = getattr(self, "rotation", 0.0)
        if not rot:
            return lx, ly
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        return lx * ca - ly * sa, lx * sa + ly * ca

    def area(self):                raise NotImplementedError
    def perimeter(self):           raise NotImplementedError
    def formula_area(self):        raise NotImplementedError
    def formula_perimeter(self):   raise NotImplementedError
    def extra_stats(self):         return {}
    def get_params(self):          raise NotImplementedError
    def max_dim(self):             return 1.0
    def scale_by(self, factor):    raise NotImplementedError
    def draw(self, canvas, sx, sy, scale): raise NotImplementedError
    def get_key_points(self):
        return [("Центр", 0.0, 0.0)]

    def bounding_box(self):
        half = self.max_dim() / 2
        return (self.x - half, self.y - half, self.x + half, self.y + half)


def _fmt_world(canvas, value):
    f = getattr(canvas, "_formatter", None)
    return f(value) if f else f"{value:g}"


class Circle(Shape):
    name = "Круг"
    FIELDS = [("Радиус (r)", "r")]
    fill_color = "#bbdefb"; outline_color = "#1976d2"

    @classmethod
    def from_values(cls, get):
        return cls(get("r", "Радиус"))

    def __init__(self, r):
        super().__init__(); self.r = float(r)
    def area(self):                 return math.pi * self.r ** 2
    def perimeter(self):            return 2 * math.pi * self.r
    def formula_area(self):         return "S = π·r²"
    def formula_perimeter(self):    return "C = 2·π·r   (длина окружности)"
    def extra_stats(self):
        return {"Радиус (r)": self.r, "Диаметр (d = 2r)": 2 * self.r}
    def get_params(self):           return {"r": self.r}
    def max_dim(self):              return 2 * self.r
    def scale_by(self, factor):     self.r *= factor
    def draw(self, canvas, sx, sy, scale):
        r = self.r * scale
        canvas.create_oval(sx - r, sy - r, sx + r, sy + r,
                           outline=self.outline_color, width=2, fill=self.fill_color)
        canvas.create_line(sx, sy, sx + r, sy, fill=self.outline_color,
                           arrow="last", width=2)
        canvas.create_oval(sx - 3, sy - 3, sx + 3, sy + 3,
                           fill=self.outline_color, outline="")
        canvas.create_text(sx + r / 2, sy - 12,
                           text=f"r = {_fmt_world(canvas, self.r)}",
                           fill=self.outline_color)


class Square(Shape):
    name = "Квадрат"
    FIELDS = [("Сторона (a)", "a")]
    fill_color = "#c8e6c9"; outline_color = "#2e7d32"

    @classmethod
    def from_values(cls, get):
        return cls(get("a", "Сторона"))

    def __init__(self, a):
        super().__init__(); self.a = float(a)
    def area(self):                 return self.a ** 2
    def perimeter(self):            return 4 * self.a
    def formula_area(self):         return "S = a²"
    def formula_perimeter(self):    return "P = 4·a"
    def extra_stats(self):          return {"Сторона (a)": self.a}
    def get_params(self):           return {"a": self.a}
    def max_dim(self):              return self.a * math.sqrt(2)
    def scale_by(self, factor):     self.a *= factor
    def get_key_points(self):
        h = self.a / 2
        return [("Угол 1", -h, -h), ("Угол 2", h, -h),
                ("Угол 3", h, h), ("Угол 4", -h, h), ("Центр", 0.0, 0.0)]
    def draw(self, canvas, sx, sy, scale):
        h = self.a * scale / 2
        corners = [(-h, -h), (h, -h), (h, h), (-h, h)]
        pts = [self._rp(x, y) for x, y in corners]
        coords = []
        for x, y in pts:
            coords.extend([sx + x, sy + y])
        canvas.create_polygon(coords, outline=self.outline_color,
                              width=2, fill=self.fill_color)
        cx, cy = self._rp(0, h + 15 * scale)
        canvas.create_text(sx + cx, sy + cy,
                           text=f"a = {_fmt_world(canvas, self.a)}",
                           fill=self.outline_color)


class Rectangle(Shape):
    name = "Прямоугольник"
    FIELDS = [("Ширина (a)", "a"), ("Высота (b)", "b")]
    fill_color = "#ffe0b2"; outline_color = "#ef6c00"

    @classmethod
    def from_values(cls, get):
        return cls(get("a", "Ширина"), get("b", "Высота"))

    def __init__(self, a, b):
        super().__init__(); self.a, self.b = float(a), float(b)
    def area(self):                 return self.a * self.b
    def perimeter(self):            return 2 * (self.a + self.b)
    def formula_area(self):         return "S = a·b"
    def formula_perimeter(self):    return "P = 2·(a + b)"
    def extra_stats(self):
        return {"Ширина (a)": self.a, "Высота (b)": self.b}
    def get_params(self):           return {"a": self.a, "b": self.b}
    def max_dim(self):              return math.hypot(self.a, self.b)
    def scale_by(self, factor):     self.a *= factor; self.b *= factor
    def get_key_points(self):
        w, h = self.a / 2, self.b / 2
        return [("Угол 1", -w, -h), ("Угол 2", w, -h),
                ("Угол 3", w, h), ("Угол 4", -w, h), ("Центр", 0.0, 0.0)]
    def draw(self, canvas, sx, sy, scale):
        w, h = self.a * scale / 2, self.b * scale / 2
        corners = [(-w, -h), (w, -h), (w, h), (-w, h)]
        pts = [self._rp(x, y) for x, y in corners]
        coords = []
        for x, y in pts:
            coords.extend([sx + x, sy + y])
        canvas.create_polygon(coords, outline=self.outline_color,
                              width=2, fill=self.fill_color)


class Triangle(Shape):
    name = "Треугольник"
    FIELDS = [("Сторона a", "a"), ("Сторона b", "b"), ("Сторона c", "c")]
    fill_color = "#e1bee7"; outline_color = "#6a1b9a"

    @classmethod
    def from_values(cls, get):
        a = get("a", "Сторона a")
        b = get("b", "Сторона b")
        c = get("c", "Сторона c")
        if a + b <= c or a + c <= b or b + c <= a:
            raise ValueError("Треугольник с такими сторонами не существует")
        return cls(a, b, c)

    def __init__(self, a, b, c):
        super().__init__(); self.a, self.b, self.c = float(a), float(b), float(c)
    def perimeter(self):            return self.a + self.b + self.c
    def area(self):
        p = self.perimeter() / 2
        return math.sqrt(p * (p - self.a) * (p - self.b) * (p - self.c))
    def formula_area(self):         return "S = √(p·(p-a)·(p-b)·(p-c)), p = P/2"
    def formula_perimeter(self):    return "P = a + b + c"
    def extra_stats(self):
        return {"Сторона a": self.a, "Сторона b": self.b, "Сторона c": self.c}
    def get_params(self):
        return {"a": self.a, "b": self.b, "c": self.c}
    def max_dim(self):              return max(self.a, self.b, self.c)
    def scale_by(self, factor):
        self.a *= factor; self.b *= factor; self.c *= factor
    def _pts(self):
        a, b, c = self.a, self.b, self.c
        xa = (b * b - a * a + c * c) / (2 * c)
        ya = math.sqrt(max(0.0, b * b - xa * xa))
        pts = [(0.0, 0.0), (c, 0.0), (xa, -ya)]
        gx = sum(p[0] for p in pts) / 3
        gy = sum(p[1] for p in pts) / 3
        return [(x - gx, y - gy) for x, y in pts]
    def get_key_points(self):
        pts = self._pts()
        return [("Вершина A", *pts[0]), ("Вершина B", *pts[1]),
                ("Вершина C", *pts[2])]
    def draw(self, canvas, sx, sy, scale):
        pts = [self._rp(x * scale, y * scale) for x, y in self._pts()]
        coords = []
        for x, y in pts:
            coords.extend([sx + x, sy + y])
        canvas.create_polygon(coords, outline=self.outline_color,
                              width=2, fill=self.fill_color)


class RightTriangle(Shape):
    name = "Прямоугольный треугольник"
    FIELDS = [("Катет (a)", "a"), ("Катет (b)", "b")]
    fill_color = "#b2ebf2"; outline_color = "#00838f"

    @classmethod
    def from_values(cls, get):
        return cls(get("a", "Катет a"), get("b", "Катет b"))

    def __init__(self, a, b):
        super().__init__(); self.a, self.b = float(a), float(b)
    def _hypot(self):               return math.hypot(self.a, self.b)
    def area(self):                 return self.a * self.b / 2
    def perimeter(self):            return self.a + self.b + self._hypot()
    def formula_area(self):         return "S = a·b / 2"
    def formula_perimeter(self):    return "P = a + b + √(a² + b²)"
    def extra_stats(self):
        return {"Катет a": self.a, "Катет b": self.b,
                "Гипотенуза c": self._hypot()}
    def get_params(self):           return {"a": self.a, "b": self.b}
    def max_dim(self):              return self._hypot()
    def scale_by(self, factor):     self.a *= factor; self.b *= factor
    def _pts(self):
        a, b = self.a, self.b
        return [(-a/2, b/2), (a/2, b/2), (-a/2, -b/2)]
    def get_key_points(self):
        a, b = self.a, self.b
        return [("Прямой угол", -a/2, b/2),
                ("Острый угол 1", a/2, b/2),
                ("Острый угол 2", -a/2, -b/2)]
    def draw(self, canvas, sx, sy, scale):
        pts = [self._rp(x * scale, y * scale) for x, y in self._pts()]
        coords = []
        for x, y in pts:
            coords.extend([sx + x, sy + y])
        canvas.create_polygon(coords, outline=self.outline_color,
                              width=2, fill=self.fill_color)


class EquilateralTriangle(Shape):
    name = "Равносторонний треугольник"
    FIELDS = [("Сторона (a)", "a")]
    fill_color = "#d1c4e9"; outline_color = "#4a148c"

    @classmethod
    def from_values(cls, get):
        return cls(get("a", "Сторона"))

    def __init__(self, a):
        super().__init__(); self.a = float(a)
    def _h(self):                   return self.a * math.sqrt(3) / 2
    def area(self):                 return math.sqrt(3) / 4 * self.a ** 2
    def perimeter(self):            return 3 * self.a
    def formula_area(self):         return "S = √3/4 · a²"
    def formula_perimeter(self):    return "P = 3·a"
    def extra_stats(self):
        return {"Сторона a": self.a, "Высота h": self._h()}
    def get_params(self):           return {"a": self.a}
    def max_dim(self):              return max(self.a, self._h())
    def scale_by(self, factor):     self.a *= factor
    def get_key_points(self):
        a, h = self.a, self._h()
        return [("Вершина A", -a/2, h/2), ("Вершина B", a/2, h/2),
                ("Вершина C", 0.0, -h/2), ("Центр", 0.0, 0.0)]
    def draw(self, canvas, sx, sy, scale):
        a, h = self.a * scale, self._h() * scale
        pts = [(-a/2, h/2), (a/2, h/2), (0, -h/2)]
        pts = [self._rp(x, y) for x, y in pts]
        coords = []
        for x, y in pts:
            coords.extend([sx + x, sy + y])
        canvas.create_polygon(coords, outline=self.outline_color,
                              width=2, fill=self.fill_color)


class Ellipse(Shape):
    name = "Эллипс"
    FIELDS = [("Полуось a", "a"), ("Полуось b", "b")]
    fill_color = "#f8bbd0"; outline_color = "#c2185b"

    @classmethod
    def from_values(cls, get):
        return cls(get("a", "Полуось a"), get("b", "Полуось b"))

    def __init__(self, a, b):
        super().__init__(); self.a, self.b = float(a), float(b)
    def area(self):                 return math.pi * self.a * self.b
    def perimeter(self):
        a, b = self.a, self.b
        return math.pi * (3*(a+b) - math.sqrt((3*a+b)*(a+3*b)))
    def formula_area(self):         return "S = π·a·b"
    def formula_perimeter(self):
        return "P ≈ π·(3(a+b) − √((3a+b)(a+3b)))   [Рамануджан]"
    def extra_stats(self):
        return {"Полуось a": self.a, "Полуось b": self.b,
                "Диаметр 2a": 2*self.a, "Диаметр 2b": 2*self.b}
    def get_params(self):           return {"a": self.a, "b": self.b}
    def max_dim(self):              return 2 * max(self.a, self.b)
    def scale_by(self, factor):     self.a *= factor; self.b *= factor
    def get_key_points(self):
        return [("Центр", 0.0, 0.0),
                ("Правая", self.a, 0.0), ("Левая", -self.a, 0.0),
                ("Верхняя", 0.0, -self.b), ("Нижняя", 0.0, self.b)]
    def bounding_box(self):
        m = max(self.a, self.b)
        return (self.x - m, self.y - m, self.x + m, self.y + m)
    def draw(self, canvas, sx, sy, scale):
        wa, wb = self.a * scale, self.b * scale
        rot = getattr(self, "rotation", 0.0)
        if not rot:
            canvas.create_oval(sx-wa, sy-wb, sx+wa, sy+wb,
                               outline=self.outline_color, width=2,
                               fill=self.fill_color)
            canvas.create_line(sx-wa, sy, sx+wa, sy, fill=self.outline_color,
                               dash=(3, 3))
            canvas.create_line(sx, sy-wb, sx, sy+wb, fill=self.outline_color,
                               dash=(3, 3))
        else:
            pts = []
            for i in range(36):
                t = 2 * math.pi * i / 36
                px, py = math.cos(t) * wa, math.sin(t) * wb
                rx, ry = self._rp(px, py)
                pts.extend([sx + rx, sy + ry])
            canvas.create_polygon(pts, outline=self.outline_color,
                                  width=2, fill=self.fill_color)


class Rhombus(Shape):
    name = "Ромб"
    FIELDS = [("Сторона (a)", "a"), ("Угол α, °", "alpha")]
    fill_color = "#f8bbd0"; outline_color = "#ad1457"

    @classmethod
    def from_values(cls, get):
        a = get("a", "Сторона"); alpha = get("alpha", "Угол α")
        if not (0 < alpha < 180):
            raise ValueError("Угол α должен быть в диапазоне (0; 180)")
        return cls(a, alpha)

    def __init__(self, a, angle_deg):
        super().__init__(); self.a = float(a)
        self.alpha = math.radians(float(angle_deg))
    def area(self):                 return self.a ** 2 * math.sin(self.alpha)
    def perimeter(self):            return 4 * self.a
    def formula_area(self):         return "S = a²·sin α"
    def formula_perimeter(self):    return "P = 4·a"
    def extra_stats(self):
        d1 = 2*self.a*math.sin(self.alpha/2)
        d2 = 2*self.a*math.cos(self.alpha/2)
        return {"Сторона a": self.a, "Угол α, °": math.degrees(self.alpha),
                "Диагональ d₁": d1, "Диагональ d₂": d2}
    def get_params(self):
        return {"a": self.a, "alpha": math.degrees(self.alpha)}
    def max_dim(self):
        return max(2*self.a*math.sin(self.alpha/2),
                   2*self.a*math.cos(self.alpha/2))
    def scale_by(self, factor):     self.a *= factor
    def get_key_points(self):
        d1 = 2*self.a*math.sin(self.alpha/2)
        d2 = 2*self.a*math.cos(self.alpha/2)
        return [("Верхняя", 0.0, -d1/2), ("Правая", d2/2, 0.0),
                ("Нижняя", 0.0, d1/2), ("Левая", -d2/2, 0.0),
                ("Центр", 0.0, 0.0)]
    def draw(self, canvas, sx, sy, scale):
        d1 = 2*self.a*math.sin(self.alpha/2)*scale
        d2 = 2*self.a*math.cos(self.alpha/2)*scale
        pts = [self._rp(x, y) for x, y in
               [(0, -d1/2), (d2/2, 0), (0, d1/2), (-d2/2, 0)]]
        coords = []
        for x, y in pts:
            coords.extend([sx + x, sy + y])
        canvas.create_polygon(coords, outline=self.outline_color,
                              width=2, fill=self.fill_color)


class Parallelogram(Shape):
    name = "Параллелограмм"
    FIELDS = [("Сторона (a)", "a"), ("Сторона (b)", "b"),
              ("Угол α, °", "alpha")]
    fill_color = "#c5cae9"; outline_color = "#283593"

    @classmethod
    def from_values(cls, get):
        a = get("a", "Сторона a"); b = get("b", "Сторона b")
        alpha = get("alpha", "Угол α")
        if not (0 < alpha < 180):
            raise ValueError("Угол α должен быть в диапазоне (0; 180)")
        return cls(a, b, alpha)

    def __init__(self, a, b, angle_deg):
        super().__init__(); self.a, self.b = float(a), float(b)
        self.alpha = math.radians(float(angle_deg))
    def area(self):                 return self.a * self.b * math.sin(self.alpha)
    def perimeter(self):            return 2 * (self.a + self.b)
    def formula_area(self):         return "S = a·b·sin α"
    def formula_perimeter(self):    return "P = 2·(a + b)"
    def extra_stats(self):
        return {"Сторона a": self.a, "Сторона b": self.b,
                "Угол α, °": math.degrees(self.alpha),
                "Высота к a": abs(self.b * math.sin(self.alpha))}
    def get_params(self):
        return {"a": self.a, "b": self.b, "alpha": math.degrees(self.alpha)}
    def max_dim(self):
        h = abs(self.b * math.sin(self.alpha))
        w = self.a + abs(self.b * math.cos(self.alpha))
        return math.hypot(w, h)
    def scale_by(self, factor):     self.a *= factor; self.b *= factor
    def _pts(self):
        h = self.b * math.sin(self.alpha)
        dx = self.b * math.cos(self.alpha)
        pts = [(-self.a/2, h/2), (self.a/2, h/2),
               (self.a/2 + dx, -h/2), (-self.a/2 + dx, -h/2)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cx = (min(xs)+max(xs))/2; cy = (min(ys)+max(ys))/2
        return [(x-cx, y-cy) for x, y in pts]
    def get_key_points(self):
        pts = self._pts()
        return [(f"Угол {i+1}", *pts[i]) for i in range(4)] + [("Центр", 0.0, 0.0)]
    def draw(self, canvas, sx, sy, scale):
        pts = [self._rp(x * scale, y * scale) for x, y in self._pts()]
        coords = []
        for x, y in pts:
            coords.extend([sx + x, sy + y])
        canvas.create_polygon(coords, outline=self.outline_color,
                              width=2, fill=self.fill_color)


class Trapezoid(Shape):
    name = "Равнобедренная трапеция"
    FIELDS = [("Нижнее основание (a)", "a"),
              ("Верхнее основание (b)", "b"),
              ("Высота (h)", "h")]
    fill_color = "#d7ccc8"; outline_color = "#5d4037"

    @classmethod
    def from_values(cls, get):
        a = get("a", "Нижнее основание")
        b = get("b", "Верхнее основание")
        h = get("h", "Высота")
        if a == b:
            raise ValueError("Основания равны — это прямоугольник")
        if b > a:
            a, b = b, a
        return cls(a, b, h)

    def __init__(self, a, b, h):
        super().__init__(); self.a, self.b, self.h = float(a), float(b), float(h)
    def _slant(self):               return math.hypot((self.a - self.b) / 2, self.h)
    def area(self):                 return (self.a + self.b) / 2 * self.h
    def perimeter(self):            return self.a + self.b + 2 * self._slant()
    def formula_area(self):         return "S = (a + b)/2 · h"
    def formula_perimeter(self):
        return "P = a + b + 2·√(((a−b)/2)² + h²)"
    def extra_stats(self):
        return {"Основание a (нижнее)": self.a,
                "Основание b (верхнее)": self.b,
                "Высота h": self.h, "Боковая сторона": self._slant()}
    def get_params(self):
        return {"a": self.a, "b": self.b, "h": self.h}
    def max_dim(self):              return math.hypot(self.a, self.h)
    def scale_by(self, factor):
        self.a *= factor; self.b *= factor; self.h *= factor
    def get_key_points(self):
        a, b, h = self.a, self.b, self.h
        return [("Низ-лево", -a/2, h/2), ("Низ-право", a/2, h/2),
                ("Верх-право", b/2, -h/2), ("Верх-лево", -b/2, -h/2),
                ("Центр", 0.0, 0.0)]
    def bounding_box(self):
        return (self.x - self.a/2, self.y - self.h/2,
                self.x + self.a/2, self.y + self.h/2)
    def draw(self, canvas, sx, sy, scale):
        a, b, h = self.a*scale, self.b*scale, self.h*scale
        top, bot = -h/2, h/2
        pts = [(-a/2, bot), (a/2, bot), (b/2, top), (-b/2, top)]
        pts = [self._rp(x, y) for x, y in pts]
        coords = []
        for x, y in pts:
            coords.extend([sx + x, sy + y])
        canvas.create_polygon(coords, outline=self.outline_color,
                              width=2, fill=self.fill_color)


class Semicircle(Shape):
    name = "Полукруг"
    FIELDS = [("Радиус (r)", "r")]
    fill_color = "#b2dfdb"; outline_color = "#00695c"

    @classmethod
    def from_values(cls, get):
        return cls(get("r", "Радиус"))

    def __init__(self, r):
        super().__init__(); self.r = float(r)
    def area(self):                 return math.pi * self.r ** 2 / 2
    def perimeter(self):            return math.pi * self.r + 2 * self.r
    def formula_area(self):         return "S = π·r² / 2"
    def formula_perimeter(self):    return "P = π·r + 2·r  (дуга + диаметр)"
    def extra_stats(self):
        return {"Радиус r": self.r, "Диаметр d": 2*self.r,
                "Длина дуги": math.pi * self.r}
    def get_params(self):           return {"r": self.r}
    def max_dim(self):              return 2 * self.r
    def scale_by(self, factor):     self.r *= factor
    def get_key_points(self):
        return [("Левая", -self.r, 0.0), ("Правая", self.r, 0.0),
                ("Верх дуги", 0.0, -self.r), ("Центр", 0.0, 0.0)]
    def bounding_box(self):
        return (self.x - self.r, self.y - self.r,
                self.x + self.r, self.y + self.r)
    def draw(self, canvas, sx, sy, scale):
        r = self.r * scale
        rot = getattr(self, "rotation", 0.0)
        if not rot:
            canvas.create_arc(sx-r, sy-r, sx+r, sy+r, start=0, extent=180,
                              style="chord", outline=self.outline_color,
                              fill=self.fill_color, width=2)
        else:
            pts = []
            for i in range(19):
                t = math.pi * i / 18
                px, py = r*math.cos(t), -r*math.sin(t)
                rx, ry = self._rp(px, py)
                pts.extend([sx + rx, sy + ry])
            canvas.create_polygon(pts, outline=self.outline_color,
                                  width=2, fill=self.fill_color)


class Ring(Shape):
    name = "Кольцо"
    FIELDS = [("Внешний радиус (R)", "R"), ("Внутренний радиус (r)", "r")]
    fill_color = "#cfd8dc"; outline_color = "#37474f"

    @classmethod
    def from_values(cls, get):
        R = get("R", "Внешний радиус")
        r = get("r", "Внутренний радиус")
        if r >= R:
            raise ValueError("Внутренний радиус должен быть меньше внешнего")
        return cls(R, r)

    def __init__(self, R, r):
        super().__init__(); self.R, self.r = float(R), float(r)
    def area(self):                 return math.pi * (self.R**2 - self.r**2)
    def perimeter(self):            return 2 * math.pi * (self.R + self.r)
    def formula_area(self):         return "S = π·(R² − r²)"
    def formula_perimeter(self):
        return "P = 2π·(R + r)   (сумма двух окружностей)"
    def extra_stats(self):
        return {"Внешний R": self.R, "Внутренний r": self.r,
                "Длина внешней окр.": 2*math.pi*self.R,
                "Длина внутренней окр.": 2*math.pi*self.r}
    def get_params(self):           return {"R": self.R, "r": self.r}
    def max_dim(self):              return 2 * self.R
    def scale_by(self, factor):     self.R *= factor; self.r *= factor
    def get_key_points(self):
        R = self.R
        return [("Центр", 0.0, 0.0), ("Внеш. верх", 0.0, -R),
                ("Внеш. низ", 0.0, R), ("Внеш. лево", -R, 0.0),
                ("Внеш. право", R, 0.0)]
    def bounding_box(self):
        return (self.x - self.R, self.y - self.R,
                self.x + self.R, self.y + self.R)
    def draw(self, canvas, sx, sy, scale):
        R, r = self.R*scale, self.r*scale
        canvas.create_oval(sx-R, sy-R, sx+R, sy+R,
                           outline=self.outline_color, width=2,
                           fill=self.fill_color)
        canvas.create_oval(sx-r, sy-r, sx+r, sy+r,
                           outline=self.outline_color, width=2, fill="white")


class Star(Shape):
    name = "Звезда"
    FIELDS = [("Внешний радиус (R)", "R"),
              ("Внутренний радиус (r)", "r"),
              ("Число концов (n)", "n")]
    fill_color = "#d1c4e9"; outline_color = "#4527a0"

    @classmethod
    def from_values(cls, get):
        R = get("R", "Внешний радиус"); r = get("r", "Внутренний радиус")
        n = get("n", "Число концов")
        if r >= R:
            raise ValueError("Внутренний радиус должен быть меньше внешнего")
        if n != int(n) or not (3 <= n <= 50):
            raise ValueError("n — целое число от 3 до 50")
        return cls(R, r, int(n))

    def __init__(self, R, r, n):
        super().__init__(); self.R, self.r = float(R), float(r)
        self.n = int(n)
    def area(self):
        return self.n * self.R * self.r * math.sin(math.pi / self.n)
    def perimeter(self):
        side = math.sqrt(self.R**2 + self.r**2 -
                         2*self.R*self.r*math.cos(math.pi / self.n))
        return 2 * self.n * side
    def formula_area(self):         return "S = n·R·r·sin(π/n)"
    def formula_perimeter(self):
        return "P = 2n·√(R² + r² − 2Rr·cos(π/n))"
    def extra_stats(self):
        return {"Внешний R": self.R, "Внутренний r": self.r,
                "Число концов n": self.n}
    def get_params(self):           return {"R": self.R, "r": self.r, "n": self.n}
    def max_dim(self):              return 2 * self.R
    def scale_by(self, factor):     self.R *= factor; self.r *= factor
    def _pts(self):
        pts = []
        for i in range(2 * self.n):
            angle = -math.pi/2 + i * math.pi / self.n
            radius = self.R if i % 2 == 0 else self.r
            pts.append((radius * math.cos(angle), radius * math.sin(angle)))
        return pts
    def get_key_points(self):
        res = [("Центр", 0.0, 0.0)]
        for i, (x, y) in enumerate(self._pts()):
            label = f"Остриё {i//2 + 1}" if i % 2 == 0 else f"Впадина {i//2 + 1}"
            res.append((label, x, y))
        return res
    def bounding_box(self):
        return (self.x - self.R, self.y - self.R,
                self.x + self.R, self.y + self.R)
    def draw(self, canvas, sx, sy, scale):
        coords = []
        for x, y in self._pts():
            rx, ry = self._rp(x * scale, y * scale)
            coords.extend([sx + rx, sy + ry])
        canvas.create_polygon(coords, outline=self.outline_color,
                              width=2, fill=self.fill_color)


class Capsule(Shape):
    name = "Капсула"
    FIELDS = [("Длина прямой части (a)", "a"), ("Радиус (r)", "r")]
    fill_color = "#d7ccc8"; outline_color = "#4e342e"

    @classmethod
    def from_values(cls, get):
        return cls(get("a", "Длина прямой части"), get("r", "Радиус"))

    def __init__(self, a, r):
        super().__init__(); self.a, self.r = float(a), float(r)
    def area(self):                 return self.a * 2*self.r + math.pi * self.r**2
    def perimeter(self):            return 2*self.a + 2*math.pi*self.r
    def formula_area(self):         return "S = 2·a·r + π·r²"
    def formula_perimeter(self):    return "P = 2·a + 2π·r"
    def extra_stats(self):
        return {"Прямая часть a": self.a, "Радиус r": self.r,
                "Диаметр 2r": 2*self.r}
    def get_params(self):           return {"a": self.a, "r": self.r}
    def max_dim(self):              return self.a + 2*self.r
    def scale_by(self, factor):     self.a *= factor; self.r *= factor
    def get_key_points(self):
        a, r = self.a, self.r
        return [("Центр", 0.0, 0.0),
                ("Верх-лево", -a/2, -r), ("Верх-право", a/2, -r),
                ("Низ-лево", -a/2, r), ("Низ-право", a/2, r),
                ("Левый конец", -a/2 - r, 0.0),
                ("Правый конец", a/2 + r, 0.0)]
    def bounding_box(self):
        hw = self.a/2 + self.r
        return (self.x - hw, self.y - self.r,
                self.x + hw, self.y + self.r)
    def draw(self, canvas, sx, sy, scale):
        a, r = self.a*scale, self.r*scale
        cx_l, cx_r = -a/2, a/2
        pts = []
        for i in range(21):
            t = -math.pi/2 + i * math.pi / 20
            pts.append((cx_r + r*math.cos(t), r*math.sin(t)))
        for i in range(21):
            t = math.pi/2 + i * math.pi / 20
            pts.append((cx_l + r*math.cos(t), r*math.sin(t)))
        coords = []
        for x, y in pts:
            rx, ry = self._rp(x, y)
            coords.extend([sx + rx, sy + ry])
        canvas.create_polygon(coords, outline=self.outline_color,
                              width=2, fill=self.fill_color)


class Polygon(Shape):
    name = "Многоугольник по точкам"
    FIELDS = []
    fill_color = "#b0bec5"; outline_color = "#37474f"

    @classmethod
    def from_values(cls, get):
        raise NotImplementedError

    def __init__(self, points):
        super().__init__()
        self.points = [(float(x), float(y)) for x, y in points]

    def normalize(self):
        if not self.points:
            return
        xs = [p[0] for p in self.points]; ys = [p[1] for p in self.points]
        cx = (min(xs) + max(xs)) / 2; cy = (min(ys) + max(ys)) / 2
        self.points = [(x - cx, y - cy) for x, y in self.points]

    def area(self):
        if len(self.points) < 3:
            return 0.0
        n = len(self.points); s = 0.0
        for i in range(n):
            x1, y1 = self.points[i]
            x2, y2 = self.points[(i+1) % n]
            s += x1*y2 - x2*y1
        return abs(s) / 2
    def perimeter(self):
        if len(self.points) < 2:
            return 0.0
        n = len(self.points); p = 0.0
        for i in range(n):
            x1, y1 = self.points[i]
            x2, y2 = self.points[(i+1) % n]
            p += math.hypot(x2-x1, y2-y1)
        return p
    def formula_area(self):
        return "S = ½·|Σ(xᵢ·yᵢ₊₁ − xᵢ₊₁·yᵢ)|   [шнуровка]"
    def formula_perimeter(self):
        return "P = Σ √((xᵢ₊₁−xᵢ)² + (yᵢ₊₁−yᵢ)²)"
    def extra_stats(self):
        return {"Число вершин": len(self.points)}
    def get_params(self):           return {}
    def max_dim(self):
        if not self.points:
            return 1.0
        xs = [p[0] for p in self.points]; ys = [p[1] for p in self.points]
        return math.hypot(max(xs)-min(xs), max(ys)-min(ys)) or 1e-6
    def scale_by(self, factor):
        self.points = [(x * factor, y * factor) for x, y in self.points]
    def get_key_points(self):
        res = [(f"P{i+1}", x, y) for i, (x, y) in enumerate(self.points)]
        res.append(("Центр bbox", 0.0, 0.0))
        return res
    def bounding_box(self):
        if not self.points:
            return (self.x, self.y, self.x, self.y)
        xs = [p[0]+self.x for p in self.points]
        ys = [p[1]+self.y for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))
    def draw(self, canvas, sx, sy, scale):
        if len(self.points) < 2:
            return
        coords = []
        for x, y in self.points:
            rx, ry = self._rp(x * scale, y * scale)
            coords.extend([sx + rx, sy + ry])
        if len(self.points) >= 3:
            canvas.create_polygon(coords, outline=self.outline_color,
                                  width=2, fill=self.fill_color)
        else:
            canvas.create_line(coords, fill=self.outline_color, width=2)


class Composite(Shape):
    """Группа фигур. children[i].x/y — смещение относительно центра группы."""
    name = "Группа"
    FIELDS = []
    fill_color = "#e0e0e0"; outline_color = "#616161"

    @classmethod
    def from_values(cls, get):
        raise NotImplementedError

    def __init__(self, children):
        super().__init__()
        self.children = list(children)

    def area(self):         return sum(c.area() for c in self.children)
    def perimeter(self):    return sum(c.perimeter() for c in self.children)
    def formula_area(self):
        return f"Сумма площадей ({len(self.children)} фигур)"
    def formula_perimeter(self):
        return f"Сумма периметров ({len(self.children)} фигур)"
    def extra_stats(self):
        from collections import Counter
        d = {"Фигур в группе": len(self.children)}
        for name, cnt in Counter(c.name for c in self.children).items():
            d[f"  • {name}"] = cnt
        return d
    def get_params(self):   return {}
    def max_dim(self):
        if not self.children:
            return 1.0
        boxes = [c.bounding_box() for c in self.children]
        w = max(b[2] for b in boxes) - min(b[0] for b in boxes)
        h = max(b[3] for b in boxes) - min(b[1] for b in boxes)
        return math.hypot(w, h) or 1e-6
    def scale_by(self, factor):
        for c in self.children:
            c.set_position(c.x * factor, c.y * factor)
            c.scale_by(factor)
    def bounding_box(self):
        if not self.children:
            return (self.x, self.y, self.x, self.y)
        boxes = []
        for c in self.children:
            x1, y1, x2, y2 = c.bounding_box()
            boxes.append((x1 + self.x, y1 + self.y,
                          x2 + self.x, y2 + self.y))
        return (min(b[0] for b in boxes), min(b[1] for b in boxes),
                max(b[2] for b in boxes), max(b[3] for b in boxes))
    def get_key_points(self):
        pts = [("Центр группы", 0.0, 0.0)]
        for ci, c in enumerate(self.children):
            for label, lx, ly in c.get_key_points():
                rlx, rly = c._rp(lx, ly)
                pts.append((f"#{ci+1} {c.name}: {label}",
                            c.x + rlx, c.y + rly))
        return pts
    def draw(self, canvas, sx, sy, scale):
        for c in self.children:
            c.draw(canvas, sx + c.x * scale, sy + c.y * scale, scale)


# ═══════════════════════════════════════════════════════════════════
# 4. ПРИЛОЖЕНИЕ
# ═══════════════════════════════════════════════════════════════════
class App:
    SHAPE_CLASSES = [Circle, Square, Rectangle, Triangle,
                     RightTriangle, EquilateralTriangle,
                     Ellipse, Rhombus, Parallelogram, Trapezoid,
                     Semicircle, Ring, Star, Capsule, Polygon]
    UNITS = {"мм": 0.001, "см": 0.01, "дм": 0.1, "м": 1.0, "км": 1000.0}

    def __init__(self, root):
        self.root = root
        self.shapes = []
        self.selected_index = None
        self.zoom = 20.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._pan_start = None
        self._pan_origin = None
        self._fitted_once = False
        self._updating_list = False
        self.entries = {}
        self.point_entries = []
        self._visible_indices = []

        # drag
        self._drag_idx = None
        self._drag_start_screen = None
        self._drag_start_world = {}
        self._drag_shapes = []
        self._drag_moved = False
        self._pre_drag_snapshot = None

        # resize
        self._resize_handle = None
        self._resize_start_box = None
        self._resize_start_mouse = None
        self._resize_shape_idx = None
        self._resize_pre_snapshot = None

        # undo
        self.undo_stack = []
        self.redo_stack = []
        self._clipboard = []

        # view
        self.dark_theme = tk.BooleanVar(value=False)
        self.grid_fixed_step = 0.0
        self.font_family = "Consolas"
        self.font_size = 11
        self.show_axes = tk.BooleanVar(value=True)
        self.show_grid = tk.BooleanVar(value=True)
        self.show_vertices = tk.BooleanVar(value=True)
        self.snap_to_grid = tk.BooleanVar(value=False)
        self._hover_vertex = None
        self._last_mouse_world = None

        # units
        self.unit_name = tk.StringVar(value="см")
        self.unit_factor = 0.01

        # tools
        self.tool = tk.StringVar(value="select")
        self._ruler_p1 = None
        self._ruler_p2 = None
        self._protractor_p1 = None
        self._protractor_p2 = None
        self._protractor_p3 = None
        self._box_selecting = False
        self._box_start = None
        self._box_end = None
        self._box_additive = False

        # multi
        self._multi_selected = set()
        self.search_var = tk.StringVar(value="")

        # scenes
        self.scenes = [{"name": "Сцена 1", "shapes": [], "undo": [],
                        "redo": [], "pan_x": 0.0, "pan_y": 0.0, "zoom": 20.0}]
        self.current_scene = 0
        self.shapes = self.scenes[0]["shapes"]
        self.undo_stack = self.scenes[0]["undo"]
        self.redo_stack = self.scenes[0]["redo"]

        self.SHAPES = [cls.name for cls in self.SHAPE_CLASSES]
        self._shape_map = {cls.name: cls for cls in self.SHAPE_CLASSES}
        self.shape_var = tk.StringVar(value=self.SHAPES[0])

        self.tooltip = Tooltip(root)

        root.title("ShapeLab v1.2")
        root.geometry("1280x820")

        self.main_paned = ttk.PanedWindow(root, orient="horizontal")
        self.main_paned.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(self.main_paned)
        self.main_paned.add(self.notebook, weight=0)
        self.creation_tab = tk.Frame(self.notebook)
        self.objects_tab = tk.Frame(self.notebook)
        self.stats_tab = tk.Frame(self.notebook)
        self.notebook.add(self.creation_tab, text="  Создание  ")
        self.notebook.add(self.objects_tab, text="  Объекты  ")
        self.notebook.add(self.stats_tab, text="  Статистика  ")

        canvas_panel = tk.Frame(self.main_paned)
        self.main_paned.add(canvas_panel, weight=1)

        self._build_canvas_panel(canvas_panel)
        self._build_creation_tab()
        self._build_objects_tab()
        self._build_stats_tab()
        self._build_menu()
        self._bind_shortcuts()

        self.root.after(50, lambda: self.main_paned.sashpos(0, 340))

    # ─────────────────────────────────────────────────────────────
    # Меню и горячие клавиши
    # ─────────────────────────────────────────────────────────────
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Новая сцена", accelerator="Ctrl+N",
                           command=self.new_scene)
        m_file.add_separator()
        m_file.add_command(label="Импорт JSON…", accelerator="Ctrl+O",
                           command=self.import_json)
        m_file.add_command(label="Экспорт JSON…", accelerator="Ctrl+S",
                           command=self.export_json)
        m_file.add_separator()
        m_file.add_command(label="Экспорт SVG…", command=self.export_svg)
        m_file.add_command(label="Экспорт PNG…", command=self.export_png)
        m_file.add_command(label="Экспорт PDF-отчёта…",
                           command=self.export_pdf_report)
        m_file.add_separator()
        m_file.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=m_file)

        m_edit = tk.Menu(menubar, tearoff=0)
        m_edit.add_command(label="Отменить", accelerator="Ctrl+Z",
                           command=self.undo)
        m_edit.add_command(label="Повторить", accelerator="Ctrl+Y",
                           command=self.redo)
        m_edit.add_separator()
        m_edit.add_command(label="Копировать", accelerator="Ctrl+C",
                           command=self.copy_selected)
        m_edit.add_command(label="Вставить", accelerator="Ctrl+V",
                           command=self.paste_from_clipboard)
        m_edit.add_command(label="Дублировать", accelerator="Ctrl+D",
                           command=self.duplicate_selected)
        m_edit.add_command(label="Выделить всё", accelerator="Ctrl+A",
                           command=self.select_all)
        m_edit.add_separator()
        m_edit.add_command(label="Удалить выбранную",
                           command=self.delete_selected)
        m_edit.add_command(label="Очистить всё", command=self.clear_all)
        m_edit.add_separator()
        m_edit.add_command(label="Группировать", accelerator="Ctrl+G",
                           command=self.group_selected)
        m_edit.add_command(label="Разгруппировать", accelerator="Ctrl+Shift+G",
                           command=self.ungroup_selected)
        m_edit.add_separator()
        m_edit.add_command(label="На передний план",
                           accelerator="Ctrl+Shift+]",
                           command=self.bring_to_front)
        m_edit.add_command(label="На задний план",
                           accelerator="Ctrl+Shift+[",
                           command=self.send_to_back)
        m_edit.add_command(label="Выше на слой", accelerator="Ctrl+]",
                           command=self.raise_one)
        m_edit.add_command(label="Ниже на слой", accelerator="Ctrl+[",
                           command=self.lower_one)
        m_edit.add_separator()
        m_edit.add_command(label="Увеличить ×1.1", accelerator="Ctrl+=",
                           command=lambda: self._resize_selected(1.1))
        m_edit.add_command(label="Уменьшить ×0.9", accelerator="Ctrl+-",
                           command=lambda: self._resize_selected(0.9))
        menubar.add_cascade(label="Правка", menu=m_edit)

        m_tools = tk.Menu(menubar, tearoff=0)
        m_tools.add_radiobutton(label="Выбор", variable=self.tool,
                                value="select", accelerator="1",
                                command=self._on_tool_change)
        m_tools.add_radiobutton(label="Линейка", variable=self.tool,
                                value="ruler", accelerator="2",
                                command=self._on_tool_change)
        m_tools.add_radiobutton(label="Транспортир", variable=self.tool,
                                value="protractor", accelerator="3",
                                command=self._on_tool_change)
        m_tools.add_radiobutton(label="Рамка выделения", variable=self.tool,
                                value="box", accelerator="4",
                                command=self._on_tool_change)
        m_tools.add_separator()
        m_tools.add_command(label="Сбросить измерение", accelerator="Esc",
                            command=self._cancel_tool)
        m_tools.add_separator()
        m_tools.add_command(label="Единицы измерения…",
                            accelerator="Ctrl+U",
                            command=self.dialog_units)
        menubar.add_cascade(label="Инструменты", menu=m_tools)

        m_view = tk.Menu(menubar, tearoff=0)
        m_view.add_checkbutton(label="Сетка", variable=self.show_grid,
                               command=self.render_all)
        m_view.add_checkbutton(label="Оси", variable=self.show_axes,
                               command=self.render_all)
        m_view.add_checkbutton(label="Точки", variable=self.show_vertices,
                               command=self.render_all)
        m_view.add_checkbutton(label="Snap к сетке",
                               variable=self.snap_to_grid)
        m_view.add_separator()
        m_view.add_command(label="Вписать всё", accelerator="F5",
                           command=self.fit_view)
        m_view.add_command(label="Настроить сетку…",
                           command=self.dialog_grid)
        m_view.add_command(label="Настроить шрифт…",
                           command=self.dialog_font)
        m_view.add_command(label="Стиль выбранной…",
                           command=self.dialog_style)
        m_view.add_separator()
        m_view.add_checkbutton(label="Тёмная тема",
                               variable=self.dark_theme,
                               command=self.apply_theme)
        menubar.add_cascade(label="Вид", menu=m_view)

    def _bind_shortcuts(self):
        r = self.root
        r.bind("<Control-z>", lambda e: self.undo())
        r.bind("<Control-y>", lambda e: self.redo())
        r.bind("<Control-Shift-Z>", lambda e: self.redo())
        r.bind("<Control-s>", lambda e: self.export_json())
        r.bind("<Control-o>", lambda e: self.import_json())
        r.bind("<Control-n>", lambda e: self.new_scene())
        r.bind("<Control-c>", lambda e: self.copy_selected())
        r.bind("<Control-v>", lambda e: self.paste_from_clipboard())
        r.bind("<Control-d>", lambda e: self.duplicate_selected())
        r.bind("<Control-a>", lambda e: self.select_all())
        r.bind("<Delete>", lambda e: self.delete_selected())
        r.bind("<Escape>", lambda e: self._cancel_tool())
        r.bind("<Control-g>", lambda e: self.group_selected())
        r.bind("<Control-Shift-G>", lambda e: self.ungroup_selected())
        r.bind("<Control-equal>", lambda e: self._resize_selected(1.1))
        r.bind("<Control-minus>", lambda e: self._resize_selected(0.9))
        r.bind("<Control-bracketright>", lambda e: self.raise_one())
        r.bind("<Control-bracketleft>", lambda e: self.lower_one())
        r.bind("<Control-Shift-bracketright>", lambda e: self.bring_to_front())
        r.bind("<Control-Shift-bracketleft>", lambda e: self.send_to_back())
        r.bind("<Control-u>", lambda e: self.dialog_units())
        r.bind("<F5>", lambda e: self.fit_view())
        r.bind("1", lambda e: self._switch_tool("select"))
        r.bind("2", lambda e: self._switch_tool("ruler"))
        r.bind("3", lambda e: self._switch_tool("protractor"))
        r.bind("4", lambda e: self._switch_tool("box"))

    def _switch_tool(self, value):
        if self.tool.get() == value:
            return
        self.tool.set(value)
        self._on_tool_change()

    # ─────────────────────────────────────────────────────────────
    # Панель холста
    # ─────────────────────────────────────────────────────────────
    def _build_canvas_panel(self, parent):
        # Строка сцен
        scene_bar = tk.Frame(parent, bg="#e3e3e3")
        scene_bar.pack(fill="x")
        tk.Label(scene_bar, text="Сцены:", bg="#e3e3e3").pack(side="left", padx=6)
        tk.Button(scene_bar, text="+ Новая", command=self.new_scene
                  ).pack(side="left", padx=2)
        self.scene_tabs = tk.StringVar(value="0")
        self._scene_buttons = []
        self._scene_frame = tk.Frame(scene_bar, bg="#e3e3e3")
        self._scene_frame.pack(side="left", fill="x", expand=True)
        self._rebuild_scene_tabs()

        # Тулбар
        toolbar = tk.Frame(parent, bg="#eeeeee")
        toolbar.pack(fill="x")

        tk.Button(toolbar, text="−", width=3,
                  command=lambda: self.zoom_by(1 / 1.3)
                  ).pack(side="left", padx=2, pady=2)
        tk.Button(toolbar, text="+", width=3,
                  command=lambda: self.zoom_by(1.3)
                  ).pack(side="left", padx=2)
        tk.Button(toolbar, text="Вписать всё",
                  command=self.fit_view).pack(side="left", padx=6)

        tk.Label(toolbar, text="│", bg="#eeeeee", fg="#999"
                 ).pack(side="left", padx=4)

        tools_frame = tk.Frame(toolbar, bg="#eeeeee")
        tools_frame.pack(side="left", padx=(0, 6))
        for text, value in [("Выбор", "select"), ("Линейка", "ruler"),
                            ("Транспортир", "protractor"), ("Рамка", "box")]:
            tk.Radiobutton(
                tools_frame, text=text, value=value, variable=self.tool,
                indicatoron=False, width=11, bg="#dddddd",
                selectcolor="#90caf9", activebackground="#cfcfcf",
                relief="raised", bd=1, command=self._on_tool_change
            ).pack(side="left", padx=1, pady=2)

        tk.Checkbutton(toolbar, text="Сетка", variable=self.show_grid,
                       command=self.render_all, bg="#eeeeee",
                       activebackground="#eeeeee"
                       ).pack(side="left", padx=(8, 0))
        tk.Checkbutton(toolbar, text="Оси", variable=self.show_axes,
                       command=self.render_all, bg="#eeeeee",
                       activebackground="#eeeeee").pack(side="left", padx=2)
        tk.Checkbutton(toolbar, text="Точки", variable=self.show_vertices,
                       command=self.render_all, bg="#eeeeee",
                       activebackground="#eeeeee").pack(side="left", padx=2)
        tk.Checkbutton(toolbar, text="Snap", variable=self.snap_to_grid,
                       bg="#eeeeee", activebackground="#eeeeee"
                       ).pack(side="left", padx=(2, 6))

        self.status_label = tk.Label(toolbar, text="Объектов: 0",
                                     bg="#eeeeee", fg="#333",
                                     font=("Arial", 9, "bold"))
        self.status_label.pack(side="right", padx=10)

        self.trig_label = tk.Label(
            toolbar, text="r = —   θ = —   sin = —   cos = —",
            bg="#eeeeee", fg="#333", font=("Consolas", 9))
        self.trig_label.pack(side="right", padx=(10, 0))

        self.canvas = tk.Canvas(parent, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", self._on_wheel)
        self.canvas.bind("<Button-5>", self._on_wheel)
        self.canvas.bind("<ButtonPress-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_end)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_start)
        self.canvas.bind("<B3-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_end)
        self.canvas.bind("<ButtonPress-1>", self._on_left_press)
        self.canvas.bind("<B1-Motion>", self._on_left_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)

    def _rebuild_scene_tabs(self):
        for b in self._scene_buttons:
            b.destroy()
        self._scene_buttons = []
        for i, sc in enumerate(self.scenes):
            b = tk.Radiobutton(
                self._scene_frame, text=sc["name"], value=str(i),
                variable=self.scene_tabs, indicatoron=False,
                command=lambda i=i: self.switch_scene(i),
                width=10, bg="#cfcfcf", selectcolor="#90caf9")
            b.pack(side="left", padx=1)
            self._scene_buttons.append(b)

    def new_scene(self):
        self._save_current_scene()
        self.scenes.append({
            "name": f"Сцена {len(self.scenes)+1}",
            "shapes": [], "undo": [], "redo": [],
            "pan_x": 0.0, "pan_y": 0.0, "zoom": 20.0})
        self._rebuild_scene_tabs()
        self._load_scene(len(self.scenes) - 1)

    def switch_scene(self, idx):
        if idx == self.current_scene or not (0 <= idx < len(self.scenes)):
            return
        self._save_current_scene()
        self._load_scene(idx)

    def _save_current_scene(self):
        sc = self.scenes[self.current_scene]
        sc["shapes"] = self.shapes
        sc["undo"] = self.undo_stack
        sc["redo"] = self.redo_stack
        sc["pan_x"] = self.pan_x
        sc["pan_y"] = self.pan_y
        sc["zoom"] = self.zoom

    def _load_scene(self, idx):
        sc = self.scenes[idx]
        self.current_scene = idx
        self.shapes = sc["shapes"]
        self.undo_stack = sc["undo"]
        self.redo_stack = sc["redo"]
        self.pan_x = sc["pan_x"]
        self.pan_y = sc["pan_y"]
        self.zoom = sc["zoom"]
        self.selected_index = None
        self._multi_selected = set()
        self._refresh_list()
        self.select_shape(None)
        self.render_all()
        self.scene_tabs.set(str(idx))

    # ─────────────────────────────────────────────────────────────
    # Вкладка «Создание»
    # ─────────────────────────────────────────────────────────────
    def _build_creation_tab(self):
        tk.Label(self.creation_tab, text="Создание фигуры",
                 font=("Arial", 12, "bold")).pack(pady=(15, 5))
        tk.Label(self.creation_tab, text="Тип фигуры", anchor="w"
                 ).pack(fill="x", padx=15, pady=4)

        cb = ttk.Combobox(self.creation_tab, textvariable=self.shape_var,
                          values=self.SHAPES, state="readonly")
        cb.pack(fill="x", padx=15, pady=4)
        cb.bind("<<ComboboxSelected>>", lambda e: self.build_inputs())

        self.inputs_frame = tk.Frame(self.creation_tab)
        self.inputs_frame.pack(fill="both", expand=True, padx=15, pady=4)
        self.build_inputs()

        tk.Button(self.creation_tab, text="+ Добавить", bg="#4caf50",
                  fg="white", font=("Arial", 11, "bold"),
                  command=self.calc).pack(fill="x", padx=15, pady=(10, 4))
        tk.Button(self.creation_tab, text="↻ Обновить выбранную",
                  bg="#1976d2", fg="white", font=("Arial", 11, "bold"),
                  command=self.apply_changes).pack(fill="x", padx=15, pady=4)
        tk.Button(self.creation_tab, text="🎨 Стиль выбранной",
                  command=self.dialog_style).pack(fill="x", padx=15, pady=4)

        resize_frame = tk.Frame(self.creation_tab)
        resize_frame.pack(fill="x", padx=15, pady=4)
        tk.Label(resize_frame, text="Размер:").pack(side="left")
        for lbl, val in [("−10%", 0.9), ("+10%", 1.1), ("×2", 2.0), ("÷2", 0.5)]:
            tk.Button(resize_frame, text=lbl, width=5,
                      command=lambda v=val: self._resize_selected(v)
                      ).pack(side="left", padx=1)

        exact_frame = tk.Frame(self.creation_tab)
        exact_frame.pack(fill="x", padx=15, pady=(0, 4))
        tk.Label(exact_frame, text="Коэф.:").pack(side="left")
        self.resize_entry = tk.Entry(exact_frame, width=8)
        self.resize_entry.insert(0, "1.0")
        self.resize_entry.pack(side="left", padx=4)
        tk.Button(exact_frame, text="Применить", width=10,
                  command=self._apply_resize_entry).pack(side="left")

        rot_frame = tk.Frame(self.creation_tab)
        rot_frame.pack(fill="x", padx=15, pady=4)
        tk.Label(rot_frame, text="Поворот, °").pack(side="left")
        self.rotation_var = tk.IntVar(value=0)
        tk.Scale(rot_frame, from_=0, to=360, orient="horizontal",
                 variable=self.rotation_var, showvalue=True
                 ).pack(side="left", fill="x", expand=True)
        tk.Button(rot_frame, text="↺", width=2,
                  command=lambda: self._rotate_selected(-15)
                  ).pack(side="left")
        tk.Button(rot_frame, text="↻", width=2,
                  command=lambda: self._rotate_selected(15)
                  ).pack(side="left")

    def build_inputs(self):
        for w in self.inputs_frame.winfo_children():
            w.destroy()
        self.entries = {}
        cls = self._shape_map[self.shape_var.get()]
        if cls is Polygon:
            self._build_points_editor()
            return
        for label, key in cls.FIELDS:
            tk.Label(self.inputs_frame, text=label, anchor="w"
                     ).pack(fill="x", pady=(5, 0))
            e = tk.Entry(self.inputs_frame, font=("Arial", 10))
            e.pack(fill="x")
            e.bind("<KeyRelease>", lambda ev, w=e: self._validate_field(w))
            self.entries[key] = e

    def _build_points_editor(self):
        self.point_entries = []
        tk.Label(self.inputs_frame, text="Вершины (x, y):",
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 4))
        scroll_frame = tk.Frame(self.inputs_frame)
        scroll_frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(scroll_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.points_canvas = tk.Canvas(scroll_frame, height=180,
                                       yscrollcommand=scrollbar.set,
                                       highlightthickness=0)
        self.points_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.points_canvas.yview)
        self.points_container = tk.Frame(self.points_canvas)
        self.points_canvas.create_window((0, 0), window=self.points_container,
                                         anchor="nw")
        self.points_container.bind(
            "<Configure>",
            lambda e: self.points_canvas.config(
                scrollregion=self.points_canvas.bbox("all")))
        tk.Button(self.inputs_frame, text="+ Добавить точку",
                  command=self._add_point_row).pack(fill="x", pady=(6, 0))

        initial = []
        if self.selected_index is not None:
            sel = self.shapes[self.selected_index]
            if isinstance(sel, Polygon):
                initial = list(sel.points)
        if not initial:
            initial = [(0.0, 0.0), (4.0, 0.0), (2.0, 3.0)]
        for x, y in initial:
            self._add_point_row(x, y)

    def _add_point_row(self, x=0.0, y=0.0):
        row = tk.Frame(self.points_container)
        row.pack(fill="x", pady=1)
        tk.Label(row, text=f"#{len(self.point_entries)+1}", width=3,
                 anchor="w").pack(side="left")
        ex = tk.Entry(row, width=7, font=("Arial", 10))
        ex.insert(0, f"{x:g}")
        ex.pack(side="left", padx=1)
        ex.bind("<KeyRelease>", lambda ev, w=ex: self._validate_field(w))
        tk.Label(row, text=",").pack(side="left")
        ey = tk.Entry(row, width=7, font=("Arial", 10))
        ey.insert(0, f"{y:g}")
        ey.pack(side="left", padx=1)
        ey.bind("<KeyRelease>", lambda ev, w=ey: self._validate_field(w))
        tk.Button(row, text="×", width=2,
                  command=lambda r=row: self._remove_point_row(r)
                  ).pack(side="left", padx=4)
        self.point_entries.append((ex, ey, row))

    def _remove_point_row(self, row):
        for i, (_, _, r) in enumerate(self.point_entries):
            if r is row:
                del self.point_entries[i]
                row.destroy()
                for j, (_, _, r2) in enumerate(self.point_entries):
                    for w in r2.winfo_children():
                        if isinstance(w, tk.Label) and w.cget("width") == 3:
                            w.config(text=f"#{j+1}")
                            break
                self.render_all()
                return

    def _load_polygon_into_editor(self, polygon):
        for _, _, row in self.point_entries:
            row.destroy()
        self.point_entries = []
        for x, y in polygon.points:
            self._add_point_row(x, y)

    def _read_points_from_editor(self):
        points = []
        for i, (ex, ey, _) in enumerate(self.point_entries):
            try:
                x = eval_math(ex.get().strip())
                y = eval_math(ey.get().strip())
            except ValueError as e:
                raise ValueError(f"Точка #{i+1}: {e}")
            points.append((x, y))
        if len(points) < 2:
            raise ValueError("Нужно минимум 2 точки (лучше 3 для площади)")
        return points

    def _validate_field(self, entry):
        text = entry.get().strip()
        if not text:
            entry.config(bg="white")
        else:
            try:
                eval_math(text)
                entry.config(bg="white")
            except ValueError:
                entry.config(bg="#ffe0e0")
        if self.shape_var.get() == Polygon.name:
            self.render_all()

    def read_value(self, key, label=None):
        text = self.entries[key].get().strip()
        try:
            value = eval_math(text)
        except ValueError as e:
            raise ValueError(f"«{label or key}»: {e}\nВвод: {text!r}")
        if value <= 0:
            raise ValueError(f"«{label or key}»: значение должно быть > 0")
        return value

    def _build_shape_from_inputs(self):
        cls = self._shape_map[self.shape_var.get()]
        if cls is Polygon:
            return Polygon(self._read_points_from_editor())
        return cls.from_values(self.read_value)

    # ─────────────────────────────────────────────────────────────
    # Вкладка «Объекты»
    # ─────────────────────────────────────────────────────────────
    def _build_objects_tab(self):
        tk.Label(self.objects_tab, text="Список объектов",
                 font=("Arial", 12, "bold")).pack(pady=(15, 5))
        tk.Label(self.objects_tab,
                 text="Клик — выделить. Shift+клик — добавить.\n"
                      "Двойной — открыть статистику.",
                 fg="#666", font=("Arial", 8, "italic"), justify="left"
                 ).pack(fill="x", padx=15, pady=(0, 8))

        search_frame = tk.Frame(self.objects_tab)
        search_frame.pack(fill="x", padx=15, pady=(0, 5))
        tk.Label(search_frame, text="Поиск:").pack(side="left")
        e = tk.Entry(search_frame, textvariable=self.search_var)
        e.pack(side="left", fill="x", expand=True, padx=(4, 0))
        e.bind("<KeyRelease>", lambda ev: self._refresh_list())

        list_frame = tk.Frame(self.objects_tab)
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)
        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side="right", fill="y")
        self.objects_list = tk.Listbox(list_frame, yscrollcommand=scroll.set,
                                       font=("Consolas", 10),
                                       exportselection=False,
                                       selectmode="extended")
        self.objects_list.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.objects_list.yview)
        self.objects_list.bind("<<ListboxSelect>>", self._on_list_select)
        self.objects_list.bind("<Double-Button-1>", self._on_list_double_click)

        tk.Button(self.objects_tab, text="Редактировать выбранную",
                  command=self._edit_selected).pack(fill="x", padx=15, pady=4)
        tk.Button(self.objects_tab, text="Удалить выбранную",
                  command=self.delete_selected).pack(fill="x", padx=15, pady=4)
        tk.Button(self.objects_tab, text="Очистить всё",
                  command=self.clear_all).pack(fill="x", padx=15, pady=4)

    def _refresh_list(self):
        self._updating_list = True
        try:
            self.objects_list.delete(0, "end")
            q = self.search_var.get().strip().lower()
            self._visible_indices = []
            for i, s in enumerate(self.shapes):
                line = f"#{i+1}  {s.name}"
                if q and q not in line.lower():
                    continue
                self.objects_list.insert("end", line)
                self._visible_indices.append(i)
            # подсветка мультивыделения
            for pos, idx in enumerate(self._visible_indices):
                if idx in self._multi_selected:
                    self.objects_list.selection_set(pos)
        finally:
            self._updating_list = False
        self._update_status()

    def _on_list_select(self, event):
        if self._updating_list:
            return
        sel = self.objects_list.curselection()
        if not sel:
            return
        idx = self._visible_indices[sel[0]]
        self._multi_selected = {self._visible_indices[i] for i in sel
                                if 0 <= i < len(self._visible_indices)}
        self.select_shape(idx)

    def _on_list_double_click(self, event):
        sel = self.objects_list.curselection()
        if sel:
            idx = self._visible_indices[sel[0]]
            self.select_shape(idx)
            self.notebook.select(self.stats_tab)

    def _edit_selected(self):
        if self.selected_index is None:
            messagebox.showinfo("Изменение", "Сначала выберите фигуру.")
            return
        self.notebook.select(self.creation_tab)

    # ─────────────────────────────────────────────────────────────
    # Вкладка «Статистика»
    # ─────────────────────────────────────────────────────────────
    def _build_stats_tab(self):
        self.stats_text = tk.Text(self.stats_tab, font=("Consolas", 11),
                                  bg="#fafafa", wrap="word", padx=15, pady=15)
        self.stats_text.pack(fill="both", expand=True)
        self.stats_text.config(state="disabled")
        self._show_stats_for(None)

    def _show_stats_for(self, shape):
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", "end")
        if shape is None:
            self.stats_text.insert("1.0",
                "Фигура не выбрана.\n\n"
                "Кликните по фигуре на холсте или в «Объектах».\n")
        else:
            n = self.selected_index + 1 if self.selected_index is not None else "?"
            lines = [f"=== {shape.name}  (#{n}) ===", ""]
            for k, v in shape.extra_stats().items():
                if isinstance(v, float):
                    if "°" in k or "Угол" in k:
                        lines.append(f"{k}: {v:.4g}")
                    elif ("Число" in k or "концов" in k or
                          "вершин" in k.lower() or "фигур" in k.lower()):
                        lines.append(f"{k}: {v:.0f}" if v == int(v) else f"{k}: {v}")
                    else:
                        lines.append(f"{k}: {self._fmt_len(v)}")
                else:
                    lines.append(f"{k}: {v}")
            lines += [
                "",
                f"Формула площади:     {shape.formula_area()}",
                f"  S = {self._fmt_area(shape.area())}",
                "",
                f"Формула периметра:   {shape.formula_perimeter()}",
                f"  P = {self._fmt_len(shape.perimeter())}",
                "",
                f"Позиция (x, y): ({self._fmt_coord(shape.x)}, "
                f"{self._fmt_coord(shape.y)})",
                f"Поворот: {getattr(shape, 'rotation', 0):.1f}°",
                f"Единицы: {self.unit_name.get()}",
            ]
            self.stats_text.insert("1.0", "\n".join(lines))
        self.stats_text.config(state="disabled")

    # ─────────────────────────────────────────────────────────────
    # Выбор / создание / изменение / удаление
    # ─────────────────────────────────────────────────────────────
    def select_shape(self, idx):
        if idx is not None and not (0 <= idx < len(self.shapes)):
            idx = None
        self.selected_index = idx

        self._updating_list = True
        try:
            self.objects_list.selection_clear(0, "end")
            if idx is not None and idx in self._visible_indices:
                pos = self._visible_indices.index(idx)
                self.objects_list.selection_set(pos)
                self.objects_list.see(pos)
        finally:
            self._updating_list = False

        if idx is not None:
            shape = self.shapes[idx]
            if isinstance(shape, Polygon):
                if self.shape_var.get() != Polygon.name:
                    self.shape_var.set(Polygon.name)
                    self.build_inputs()
                self._load_polygon_into_editor(shape)
            elif isinstance(shape, Composite):
                pass  # нет полей ввода
            else:
                if self.shape_var.get() != shape.name:
                    self.shape_var.set(shape.name)
                    self.build_inputs()
                params = shape.get_params()
                for key, entry in self.entries.items():
                    entry.delete(0, "end")
                    if key in params:
                        entry.insert(0, f"{params[key]:g}")
                    entry.config(bg="white")
            if hasattr(self, "rotation_var"):
                self.rotation_var.set(int(getattr(shape, "rotation", 0)))
            self._show_stats_for(shape)
        else:
            self._show_stats_for(None)
        self.render_all()

    def calc(self):
        try:
            shape = self._build_shape_from_inputs()
        except ValueError as ex:
            messagebox.showerror("Ошибка ввода", str(ex))
            return
        self._push_undo()
        self._place_shape(shape)
        self.shapes.append(shape)
        self._multi_selected = {len(self.shapes) - 1}
        self._refresh_list()
        self.select_shape(len(self.shapes) - 1)
        self._ensure_visible(shape)
        self.render_all()

    def apply_changes(self):
        if self.selected_index is None:
            messagebox.showinfo("Изменение",
                                "Сначала выберите фигуру на холсте "
                                "или в «Объектах».")
            return
        try:
            new_shape = self._build_shape_from_inputs()
        except ValueError as ex:
            messagebox.showerror("Ошибка ввода", str(ex))
            return

        old = self.shapes[self.selected_index]
        if type(new_shape) is not type(old):
            if not messagebox.askyesno(
                    "Смена типа",
                    f"Тип: «{old.name}» → «{new_shape.name}». Продолжить?"):
                return

        self._push_undo()
        new_shape.set_position(old.x, old.y)
        new_shape.rotation = getattr(old, "rotation", 0.0)
        self.shapes[self.selected_index] = new_shape
        self._multi_selected = {self.selected_index}
        self._refresh_list()
        self.select_shape(self.selected_index)
        self.render_all()

    def _place_shape(self, shape):
        if not self.shapes:
            shape.set_position(0, 0)
            return
        right = max(s.bounding_box()[2] for s in self.shapes)
        if isinstance(shape, Polygon):
            shape.normalize()
        half = shape.max_dim() / 2
        shape.set_position(right + half * 2, 0)

    def _ensure_visible(self, shape):
        x1, y1, x2, y2 = shape.bounding_box()
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if (w <= 1 or h <= 1 or
                x1 * self.zoom + self.pan_x < 20 or
                y1 * self.zoom + self.pan_y < 20 or
                x2 * self.zoom + self.pan_x > w - 20 or
                y2 * self.zoom + self.pan_y > h - 20):
            self.fit_view()

    def delete_selected(self):
        if not self._multi_selected and self.selected_index is None:
            return
        self._push_undo()
        indices = self._multi_selected or {self.selected_index}
        for i in sorted(indices, reverse=True):
            if 0 <= i < len(self.shapes):
                del self.shapes[i]
        self.selected_index = None
        self._multi_selected = set()
        self._refresh_list()
        self.select_shape(None)
        self.render_all()

    def clear_all(self):
        if self.shapes and not messagebox.askyesno(
                "Очистить", "Удалить все фигуры в текущей сцене?"):
            return
        self._push_undo()
        self.shapes = []
        self.scenes[self.current_scene]["shapes"] = self.shapes
        self.selected_index = None
        self._multi_selected = set()
        self._refresh_list()
        self.select_shape(None)
        self.render_all()

    def select_all(self):
        if not self.shapes:
            return
        self._multi_selected = set(range(len(self.shapes)))
        self.select_shape(len(self.shapes) - 1)

    # ─────────────────────────────────────────────────────────────
    # Undo / Redo
    # ─────────────────────────────────────────────────────────────
    def _shape_to_dict(self, s):
        if isinstance(s, Composite):
            return {"type": "Composite",
                    "children": [self._shape_to_dict(c) for c in s.children],
                    "x": s.x, "y": s.y,
                    "fill": getattr(s, "fill_color", None),
                    "outline": getattr(s, "outline_color", None),
                    "rotation": getattr(s, "rotation", 0.0)}
        if isinstance(s, Polygon):
            return {"type": "Polygon", "points": list(s.points),
                    "x": s.x, "y": s.y,
                    "fill": getattr(s, "fill_color", None),
                    "outline": getattr(s, "outline_color", None),
                    "rotation": getattr(s, "rotation", 0.0)}
        return {"type": s.name, "params": dict(s.get_params()),
                "x": s.x, "y": s.y,
                "fill": getattr(s, "fill_color", None),
                "outline": getattr(s, "outline_color", None),
                "rotation": getattr(s, "rotation", 0.0)}

    def _dict_to_shape(self, d):
        t = d["type"]
        if t == "Composite":
            s = Composite([self._dict_to_shape(cd) for cd in d.get("children", [])])
        elif t == "Polygon":
            s = Polygon(d["points"])
        else:
            cls = next((c for c in self.SHAPE_CLASSES if c.name == t), None)
            if cls is None:
                raise ValueError(f"неизвестный тип: {t}")
            params = d.get("params", {})
            s = cls.from_values(lambda key, label=None: params[key])
        s.set_position(d.get("x", 0.0), d.get("y", 0.0))
        if d.get("fill"):
            s.fill_color = d["fill"]
        if d.get("outline"):
            s.outline_color = d["outline"]
        s.rotation = d.get("rotation", 0.0)
        return s

    def _snapshot(self):
        return [self._shape_to_dict(s) for s in self.shapes]

    def _restore(self, snap):
        self.shapes = []
        self.scenes[self.current_scene]["shapes"] = self.shapes
        for d in snap:
            try:
                self.shapes.append(self._dict_to_shape(d))
            except Exception:
                pass
        self.selected_index = None
        self._multi_selected = set()
        self._refresh_list()
        self.select_shape(None)
        self.render_all()

    def _push_undo(self):
        self.undo_stack.append(self._snapshot())
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self._snapshot())
        self._restore(self.undo_stack.pop())

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self._snapshot())
        self._restore(self.redo_stack.pop())

    # ─────────────────────────────────────────────────────────────
    # Клипборд
    # ─────────────────────────────────────────────────────────────
    def copy_selected(self):
        indices = self._multi_selected or (
            {self.selected_index} if self.selected_index is not None else set())
        if not indices:
            return
        self._clipboard = [self._shape_to_dict(self.shapes[i])
                           for i in sorted(indices)
                           if 0 <= i < len(self.shapes)]
        self.status_label.config(text=f"Скопировано: {len(self._clipboard)}")

    def paste_from_clipboard(self):
        if not self._clipboard:
            return
        self._push_undo()
        new_indices = []
        for d in self._clipboard:
            clone = self._dict_to_shape(d)
            clone.set_position(clone.x + 10, clone.y + 10)
            self.shapes.append(clone)
            new_indices.append(len(self.shapes) - 1)
        self._multi_selected = set(new_indices)
        self._refresh_list()
        self.select_shape(new_indices[-1])
        self.render_all()

    def duplicate_selected(self):
        if not (self._multi_selected or self.selected_index is not None):
            return
        self.copy_selected()
        self.paste_from_clipboard()

    # ─────────────────────────────────────────────────────────────
    # Слои
    # ─────────────────────────────────────────────────────────────
    def _reindex_multi(self, lifted):
        idx_map = {id(s): i for i, s in enumerate(self.shapes)}
        self._multi_selected = {idx_map[id(s)] for s in lifted
                                if id(s) in idx_map}

    def bring_to_front(self):
        if not self._multi_selected:
            return
        self._push_undo()
        lifted = [self.shapes[i] for i in sorted(self._multi_selected)
                  if 0 <= i < len(self.shapes)]
        rest = [s for i, s in enumerate(self.shapes)
                if i not in self._multi_selected]
        self.shapes = rest + lifted
        self._reindex_multi(lifted)
        self._refresh_list()
        self.select_shape(max(self._multi_selected))
        self.render_all()

    def send_to_back(self):
        if not self._multi_selected:
            return
        self._push_undo()
        lowered = [self.shapes[i] for i in sorted(self._multi_selected)
                   if 0 <= i < len(self.shapes)]
        rest = [s for i, s in enumerate(self.shapes)
                if i not in self._multi_selected]
        self.shapes = lowered + rest
        self._reindex_multi(lowered)
        self._refresh_list()
        self.select_shape(min(self._multi_selected))
        self.render_all()

    def raise_one(self):
        if not self._multi_selected:
            return
        self._push_undo()
        for i in sorted(self._multi_selected, reverse=True):
            if i < len(self.shapes) - 1 and (i + 1) not in self._multi_selected:
                self.shapes[i], self.shapes[i + 1] = \
                    self.shapes[i + 1], self.shapes[i]
        self._multi_selected = {i + 1 if i < len(self.shapes) - 1 else i
                                for i in self._multi_selected}
        self._refresh_list()
        self.select_shape(max(self._multi_selected))
        self.render_all()

    def lower_one(self):
        if not self._multi_selected:
            return
        self._push_undo()
        for i in sorted(self._multi_selected):
            if i > 0 and (i - 1) not in self._multi_selected:
                self.shapes[i], self.shapes[i - 1] = \
                    self.shapes[i - 1], self.shapes[i]
        self._multi_selected = {i - 1 if i > 0 else i
                                for i in self._multi_selected}
        self._refresh_list()
        self.select_shape(min(self._multi_selected))
        self.render_all()

    # ─────────────────────────────────────────────────────────────
    # Группировка
    # ─────────────────────────────────────────────────────────────
    def group_selected(self):
        if len(self._multi_selected) < 2:
            messagebox.showinfo("Группа", "Выделите две или более фигуры.")
            return
        self._push_undo()
        children = [self.shapes[i] for i in sorted(self._multi_selected)
                    if 0 <= i < len(self.shapes)]
        for i in sorted(self._multi_selected, reverse=True):
            if 0 <= i < len(self.shapes):
                del self.shapes[i]
        comp = Composite(children)
        comp.set_position(0, 0)
        self.shapes.append(comp)
        self._multi_selected = {len(self.shapes) - 1}
        self._refresh_list()
        self.select_shape(len(self.shapes) - 1)
        self.render_all()

    def ungroup_selected(self):
        if not self._multi_selected:
            return
        self._push_undo()
        new_indices = []
        for idx in sorted(self._multi_selected, reverse=True):
            if not (0 <= idx < len(self.shapes)):
                continue
            shape = self.shapes[idx]
            if not isinstance(shape, Composite):
                continue
            for child in shape.children:
                child.set_position(child.x + shape.x, child.y + shape.y)
                self.shapes.append(child)
                new_indices.append(len(self.shapes) - 1)
            del self.shapes[idx]
        self._multi_selected = set(new_indices)
        self._refresh_list()
        self.select_shape(max(new_indices) if new_indices else None)
        self.render_all()

    # ─────────────────────────────────────────────────────────────
    # Поворот и изменение размера
    # ─────────────────────────────────────────────────────────────
    def _rotate_selected(self, delta):
        if self.selected_index is None:
            return
        self._push_undo()
        s = self.shapes[self.selected_index]
        if isinstance(s, Composite):
            rad = math.radians(delta)
            ca, sa = math.cos(rad), math.sin(rad)
            for c in s.children:
                nx = c.x * ca - c.y * sa
                ny = c.x * sa + c.y * ca
                c.set_position(nx, ny)
                c.rotation = (getattr(c, "rotation", 0.0) + delta) % 360
        else:
            s.rotation = (getattr(s, "rotation", 0.0) + delta) % 360
            if hasattr(self, "rotation_var"):
                self.rotation_var.set(int(s.rotation))
        self.render_all()

    def _resize_selected(self, factor):
        if factor <= 0:
            return
        indices = self._multi_selected or (
            {self.selected_index} if self.selected_index is not None else set())
        if not indices:
            return
        self._push_undo()
        for i in indices:
            if 0 <= i < len(self.shapes):
                try:
                    self.shapes[i].scale_by(factor)
                except NotImplementedError:
                    pass
        self.render_all()

    def _apply_resize_entry(self):
        try:
            factor = float(self.resize_entry.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Размер", "Введите число, например 1.5")
            return
        if factor <= 0:
            messagebox.showerror("Размер", "Коэффициент должен быть > 0")
            return
        self._resize_selected(factor)

    # ─────────────────────────────────────────────────────────────
    # JSON
    # ─────────────────────────────────────────────────────────────
    def export_json(self):
        path = filedialog.asksaveasfilename(
            title="Сохранить сцену", defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")])
        if not path:
            return
        data = {"version": 2,
                "units": self.unit_name.get(),
                "shapes": self._snapshot()}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            messagebox.showerror("Экспорт", f"Не удалось сохранить: {e}")
            return
        self.status_label.config(text=f"Сохранено: {path}")

    def import_json(self):
        path = filedialog.askopenfilename(
            title="Загрузить сцену",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            messagebox.showerror("Импорт", f"Не удалось прочитать: {e}")
            return
        if "shapes" not in data:
            messagebox.showerror("Импорт", "Неверный формат файла")
            return
        self._push_undo()
        new_shapes = []
        skipped = 0
        for d in data["shapes"]:
            try:
                new_shapes.append(self._dict_to_shape(d))
            except Exception:
                skipped += 1
        self.shapes = new_shapes
        self.scenes[self.current_scene]["shapes"] = self.shapes
        self.selected_index = None
        self._multi_selected = set()
        self._refresh_list()
        self.select_shape(None)
        self.fit_view()
        self.render_all()
        if skipped:
            self.status_label.config(text=f"Импорт: {skipped} пропущено")

    # ─────────────────────────────────────────────────────────────
    # Экспорт
    # ─────────────────────────────────────────────────────────────
    def export_svg(self):
        path = filedialog.asksaveasfilename(
            title="Экспорт SVG", defaultextension=".svg",
            filetypes=[("SVG", "*.svg")])
        if not path:
            return
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 600
        lines = [f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
                 f'<rect width="{w}" height="{h}" fill="white"/>']
        for shape in self.shapes:
            fill = getattr(shape, "fill_color", "#b0bec5")
            stroke = getattr(shape, "outline_color", "#37474f")

            def P(wx, wy):
                return (wx * self.zoom + self.pan_x,
                        wy * self.zoom + self.pan_y)

            if isinstance(shape, Circle):
                cx, cy = P(shape.x, shape.y)
                lines.append(f'<circle cx="{cx}" cy="{cy}" '
                             f'r="{shape.r*self.zoom}" fill="{fill}" '
                             f'stroke="{stroke}" stroke-width="2"/>')
            elif isinstance(shape, Ring):
                cx, cy = P(shape.x, shape.y)
                R = shape.R * self.zoom; r = shape.r * self.zoom
                lines.append(f'<path d="M {cx-R} {cy} '
                             f'A {R} {R} 0 1 0 {cx+R} {cy} '
                             f'A {R} {R} 0 1 0 {cx-R} {cy} Z '
                             f'M {cx-r} {cy} '
                             f'A {r} {r} 0 1 0 {cx+r} {cy} '
                             f'A {r} {r} 0 1 0 {cx-r} {cy} Z" '
                             f'fill="{fill}" fill-rule="evenodd" '
                             f'stroke="{stroke}" stroke-width="2"/>')
            else:
                pts = shape.get_key_points()
                if len(pts) < 3:
                    continue
                coords = []
                for _, lx, ly in pts:
                    rlx, rly = shape._rp(lx, ly)
                    sx, sy = P(shape.x + rlx, shape.y + rly)
                    coords.append(f"{sx:.2f},{sy:.2f}")
                lines.append(f'<polygon points="{" ".join(coords)}" '
                             f'fill="{fill}" stroke="{stroke}" '
                             f'stroke-width="2"/>')
        lines.append("</svg>")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except OSError as e:
            messagebox.showerror("SVG", f"Не удалось сохранить: {e}")
            return
        self.status_label.config(text=f"SVG: {path}")

    def export_png(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            messagebox.showerror("PNG",
                                 "Установите Pillow:\n  pip install pillow")
            return
        path = filedialog.asksaveasfilename(
            title="Экспорт PNG", defaultextension=".png",
            filetypes=[("PNG", "*.png")])
        if not path:
            return
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 600
        img = Image.new("RGB", (w, h), "white")
        dr = ImageDraw.Draw(img)

        def P(wx, wy):
            return (wx * self.zoom + self.pan_x, wy * self.zoom + self.pan_y)

        for shape in self.shapes:
            fill = getattr(shape, "fill_color", "#b0bec5")
            outline = getattr(shape, "outline_color", "#37474f")
            if isinstance(shape, Circle):
                cx, cy = P(shape.x, shape.y)
                r = shape.r * self.zoom
                dr.ellipse([cx-r, cy-r, cx+r, cy+r], fill=fill,
                           outline=outline, width=2)
            elif isinstance(shape, Ring):
                cx, cy = P(shape.x, shape.y)
                R = shape.R * self.zoom; r = shape.r * self.zoom
                dr.ellipse([cx-R, cy-R, cx+R, cy+R], fill=fill,
                           outline=outline, width=2)
                dr.ellipse([cx-r, cy-r, cx+r, cy+r], fill="white",
                           outline=outline, width=2)
            else:
                pts = shape.get_key_points()
                if len(pts) < 3:
                    continue
                screen = []
                for _, lx, ly in pts:
                    rlx, rly = shape._rp(lx, ly)
                    screen.append(P(shape.x + rlx, shape.y + rly))
                dr.polygon(screen, fill=fill, outline=outline)
        try:
            img.save(path, "PNG")
        except OSError as e:
            messagebox.showerror("PNG", f"Не удалось сохранить: {e}")
            return
        self.status_label.config(text=f"PNG: {path}")

    def export_pdf_report(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas as rl_canvas
            from reportlab.lib.units import cm
        except ImportError:
            messagebox.showerror("PDF",
                                 "Установите reportlab:\n  pip install reportlab")
            return
        path = filedialog.asksaveasfilename(
            title="Экспорт PDF-отчёта", defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        c = rl_canvas.Canvas(path, pagesize=A4)
        W, H = A4
        y = H - 2 * cm

        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * cm, y, "ShapeLab — отчёт по сцене")
        y -= 1 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, f"Фигур: {len(self.shapes)}   "
                                f"Единицы: {self.unit_name.get()}")
        y -= 0.6 * cm
        total_s = sum(s.area() for s in self.shapes)
        total_p = sum(s.perimeter() for s in self.shapes)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, f"Суммарная площадь: {self._fmt_area(total_s)}")
        c.drawString(11 * cm, y, f"Суммарный периметр: {self._fmt_len(total_p)}")
        y -= 1 * cm

        c.setFont("Helvetica-Bold", 10)
        headers = ["#", "Тип", "Площадь", "Периметр", "X", "Y"]
        cols = [2, 3.2, 9, 12.5, 15.5, 17.5]
        for hh, x in zip(headers, cols):
            c.drawString(x * cm, y, hh)
        y -= 0.4 * cm
        c.line(2 * cm, y, 19 * cm, y)
        y -= 0.3 * cm

        c.setFont("Helvetica", 9)
        for i, s in enumerate(self.shapes):
            if y < 3 * cm:
                c.showPage(); y = H - 2 * cm
                c.setFont("Helvetica", 9)
            c.drawString(cols[0] * cm, y, f"{i+1}")
            c.drawString(cols[1] * cm, y, s.name)
            c.drawString(cols[2] * cm, y, self._fmt_area(s.area()))
            c.drawString(cols[3] * cm, y, self._fmt_len(s.perimeter()))
            c.drawString(cols[4] * cm, y, f"{s.x:.2f}")
            c.drawString(cols[5] * cm, y, f"{s.y:.2f}")
            y -= 0.45 * cm
        c.save()
        self.status_label.config(text=f"PDF: {path}")

    # ─────────────────────────────────────────────────────────────
    # Диалоги
    # ─────────────────────────────────────────────────────────────
    def dialog_grid(self):
        val = simpledialog.askfloat(
            "Сетка", "Шаг сетки в единицах (0 = авто):",
            initialvalue=self.grid_fixed_step, minvalue=0.0, parent=self.root)
        if val is None:
            return
        self.grid_fixed_step = float(val)
        self.render_all()

    def dialog_font(self):
        family = simpledialog.askstring("Шрифт", "Семейство шрифта:",
                                        initialvalue=self.font_family,
                                        parent=self.root)
        if not family or not family.strip():
            return
        size = simpledialog.askinteger("Шрифт", "Размер:",
                                       initialvalue=self.font_size,
                                       minvalue=6, maxvalue=48,
                                       parent=self.root)
        if size is None:
            return
        self.font_family = family.strip()
        self.font_size = size
        self._apply_font()

    def dialog_units(self):
        name = simpledialog.askstring(
            "Единицы измерения",
            f"Доступно: {', '.join(self.UNITS)}\nТекущая: {self.unit_name.get()}",
            initialvalue=self.unit_name.get(), parent=self.root)
        if not name or name not in self.UNITS:
            return
        self.unit_name.set(name)
        self.unit_factor = self.UNITS[name]
        if self.selected_index is not None:
            self._show_stats_for(self.shapes[self.selected_index])
        self.render_all()

    def dialog_style(self):
        from tkinter import colorchooser
        if self.selected_index is None:
            messagebox.showinfo("Стиль", "Выберите фигуру.")
            return
        s = self.shapes[self.selected_index]
        fill = colorchooser.askcolor(
            color=getattr(s, "fill_color", "#ffffff"),
            title="Цвет заливки")[1]
        if fill is None:
            return
        outline = colorchooser.askcolor(
            color=getattr(s, "outline_color", "#000000"),
            title="Цвет обводки")[1]
        if outline is None:
            return
        self._push_undo()
        s.fill_color = fill
        s.outline_color = outline
        self.render_all()

    def _apply_font(self):
        try:
            self.stats_text.configure(font=(self.font_family, self.font_size))
            self.objects_list.configure(font=(self.font_family, self.font_size))
        except tk.TclError:
            pass

    # ─────────────────────────────────────────────────────────────
    # Тема
    # ─────────────────────────────────────────────────────────────
    def apply_theme(self):
        if self.dark_theme.get():
            pal = {"bg": "#2b2b2b", "panel": "#3a3a3a", "toolbar": "#2f2f2f",
                   "fg": "#e0e0e0", "canvas": "#1a1a1a",
                   "entry": "#454545", "entry_fg": "#f0f0f0",
                   "text": "#1e1e1e", "text_fg": "#e0e0e0"}
        else:
            pal = {"bg": "#f0f0f0", "panel": "#f5f5f5", "toolbar": "#eeeeee",
                   "fg": "#000000", "canvas": "#ffffff",
                   "entry": "#ffffff", "entry_fg": "#000000",
                   "text": "#fafafa", "text_fg": "#000000"}

        for w in (self.root, self.notebook, self.creation_tab,
                  self.objects_tab, self.stats_tab):
            try:
                w.configure(bg=pal["bg"])
            except tk.TclError:
                pass
        self.canvas.configure(bg=pal["canvas"])
        self.stats_text.configure(bg=pal["text"], fg=pal["text_fg"],
                                  insertbackground=pal["text_fg"])

        def walk(w):
            for child in w.winfo_children():
                try:
                    child.configure(bg=pal["panel"], fg=pal["fg"])
                except tk.TclError:
                    pass
                if isinstance(child, (tk.Entry, tk.Text)):
                    try:
                        child.configure(bg=pal["entry"], fg=pal["entry_fg"],
                                        insertbackground=pal["entry_fg"])
                    except tk.TclError:
                        pass
                walk(child)
        walk(self.root)
        self.render_all()

    # ─────────────────────────────────────────────────────────────
    # Единицы — форматирование
    # ─────────────────────────────────────────────────────────────
    def _to_units(self, value_world):
        return value_world * self.unit_factor / self.UNITS[self.unit_name.get()]

    def _fmt_len(self, value_world):
        return f"{self._to_units(value_world):.4g} {self.unit_name.get()}"

    def _fmt_area(self, value_world):
        return f"{self._to_units(value_world):.4g} {self.unit_name.get()}²"

    def _fmt_coord(self, value_world):
        return f"{self._to_units(value_world):.3f}"

    def _fmt_canvas_label(self, value_world):
        return self._fmt_len(value_world)

    # ─────────────────────────────────────────────────────────────
    # Рендер
    # ─────────────────────────────────────────────────────────────
    def _current_grid_step(self):
        if self.grid_fixed_step > 0:
            return self.grid_fixed_step
        raw = 60.0 / self.zoom
        if raw <= 0:
            return 1.0
        magnitude = 10 ** math.floor(math.log10(raw))
        for mult in (1, 2, 5, 10):
            if magnitude * mult >= raw:
                return magnitude * mult
        return magnitude * 10

    def render_all(self):
        self.canvas.delete("all")
        self.canvas._formatter = self._fmt_canvas_label
        self._draw_axes()

        for i, shape in enumerate(self.shapes):
            sx = shape.x * self.zoom + self.pan_x
            sy = shape.y * self.zoom + self.pan_y
            before = set(self.canvas.find_all())
            shape.draw(self.canvas, sx, sy, self.zoom)
            for item in set(self.canvas.find_all()) - before:
                self.canvas.addtag_withtag(f"shape_{i}", item)

        if self.selected_index is not None and \
               0 <= self.selected_index < len(self.shapes):
            x1, y1, x2, y2 = self.shapes[self.selected_index].bounding_box()
            self.canvas.create_rectangle(
                x1 * self.zoom + self.pan_x, y1 * self.zoom + self.pan_y,
                x2 * self.zoom + self.pan_x, y2 * self.zoom + self.pan_y,
                outline="#d32f2f", width=2, dash=(5, 3))

        for idx in self._multi_selected:
            if idx == self.selected_index:
                continue
            if not (0 <= idx < len(self.shapes)):
                continue
            s = self.shapes[idx]
            x1, y1, x2, y2 = s.bounding_box()
            self.canvas.create_rectangle(
                x1 * self.zoom + self.pan_x, y1 * self.zoom + self.pan_y,
                x2 * self.zoom + self.pan_x, y2 * self.zoom + self.pan_y,
                outline="#ff9800", width=2, dash=(3, 2))

        self._draw_resize_handles()
        self._draw_vertices()
        self._draw_preview()
        self._draw_ruler()
        self._draw_protractor()
        self._draw_selection_box()
        self._update_status()

    def _draw_axes(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        x1 = -self.pan_x / self.zoom
        y1 = -self.pan_y / self.zoom
        x2 = (w - self.pan_x) / self.zoom
        y2 = (h - self.pan_y) / self.zoom
        step = self._current_grid_step()
        i0, i1 = math.ceil(x1 / step), math.floor(x2 / step)
        j0, j1 = math.ceil(y1 / step), math.floor(y2 / step)
        if (i1 - i0) > 500 or (j1 - j0) > 500:
            return
        axis_color = "#ffffff" if self.dark_theme.get() else "#000000"
        grid_color = "#2d2d2d" if self.dark_theme.get() else "#f0f0f0"
        label_color = "#cfcfcf" if self.dark_theme.get() else "#333333"
        if self.show_grid.get():
            for i in range(i0, i1 + 1):
                if i == 0:
                    continue
                sx = (i * step) * self.zoom + self.pan_x
                self.canvas.create_line(sx, 0, sx, h, fill=grid_color)
            for j in range(j0, j1 + 1):
                if j == 0:
                    continue
                sy = (j * step) * self.zoom + self.pan_y
                self.canvas.create_line(0, sy, w, sy, fill=grid_color)
        ox, oy = self.pan_x, self.pan_y
        x_vis = 0 <= oy <= h
        y_vis = 0 <= ox <= w
        if x_vis and self.show_axes.get():
            self.canvas.create_line(0, oy, w, oy, fill=axis_color, width=2)
            for i in range(i0, i1 + 1):
                if i == 0:
                    continue
                sx = (i * step) * self.zoom + self.pan_x
                self.canvas.create_line(sx, oy - 4, sx, oy + 4,
                                        fill=axis_color)
                self.canvas.create_text(sx, oy + 13,
                                        text=f"{self._to_units(i*step):g}",
                                        fill=label_color, font=("Arial", 8))
            self.canvas.create_text(w - 10, oy - 12, text="x",
                                    fill="#d32f2f",
                                    font=("Arial", 11, "bold"))
        if y_vis and self.show_axes.get():
            self.canvas.create_line(ox, 0, ox, h, fill=axis_color, width=2)
            for j in range(j0, j1 + 1):
                if j == 0:
                    continue
                sy = (j * step) * self.zoom + self.pan_y
                self.canvas.create_line(ox - 4, sy, ox + 4, sy,
                                        fill=axis_color)
                self.canvas.create_text(ox - 20, sy,
                                        text=f"{self._to_units(j*step):g}",
                                        fill=label_color, font=("Arial", 8))
            self.canvas.create_text(ox + 12, 10, text="y", fill="#2e7d32",
                                    font=("Arial", 11, "bold"))
        if x_vis and y_vis and self.show_axes.get():
            self.canvas.create_text(ox - 12, oy + 12, text="0",
                                    fill=label_color,
                                    font=("Arial", 8, "bold"))

    def _draw_vertices(self):
        if not self.show_vertices.get():
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        for i, shape in enumerate(self.shapes):
            for j, (label, lx, ly) in enumerate(shape.get_key_points()):
                rlx, rly = shape._rp(lx, ly)
                sx = (shape.x + rlx) * self.zoom + self.pan_x
                sy = (shape.y + rly) * self.zoom + self.pan_y
                if not (-10 <= sx <= w + 10 and -10 <= sy <= h + 10):
                    continue
                is_hover = (i, j) == self._hover_vertex
                r = 4 if is_hover else 3
                fill = "#ff9800" if is_hover else "#e53935"
                self.canvas.create_oval(sx - r, sy - r, sx + r, sy + r,
                                        fill=fill, outline="white", width=1,
                                        tags=("vertex", f"vtx_{i}_{j}"))

    def _draw_resize_handles(self):
        if self.selected_index is None:
            return
        if self._multi_selected and len(self._multi_selected) > 1:
            return
        if self.tool.get() != "select":
            return
        if not (0 <= self.selected_index < len(self.shapes)):
            return
        x1, y1, x2, y2 = self.shapes[self.selected_index].bounding_box()
        for tag, wx, wy in [("tl", x1, y1), ("tr", x2, y1),
                            ("bl", x1, y2), ("br", x2, y2)]:
            sx = wx * self.zoom + self.pan_x
            sy = wy * self.zoom + self.pan_y
            self.canvas.create_rectangle(sx-4, sy-4, sx+4, sy+4,
                                         fill="#2196f3", outline="white",
                                         width=1,
                                         tags=("resize_handle", f"rh_{tag}"))

    def _should_preview(self):
        if self.shape_var.get() != Polygon.name:
            return False
        if self.selected_index is None:
            return True
        sel = self.shapes[self.selected_index]
        if not isinstance(sel, Polygon):
            return True
        try:
            current = self._read_points_from_editor()
        except ValueError:
            return False
        return current != sel.points

    def _draw_preview(self):
        if not self._should_preview():
            return
        try:
            points = self._read_points_from_editor()
        except ValueError:
            return
        if len(points) < 2:
            return
        base_x = base_y = 0.0
        if self.selected_index is not None:
            old = self.shapes[self.selected_index]
            if isinstance(old, Polygon):
                base_x, base_y = old.x, old.y
        coords = []
        for x, y in points:
            coords.extend([(base_x + x) * self.zoom + self.pan_x,
                           (base_y + y) * self.zoom + self.pan_y])
        if len(points) >= 3:
            self.canvas.create_polygon(coords, outline="#ff9800", width=2,
                                       dash=(4, 4), fill="")
        else:
            self.canvas.create_line(coords, fill="#ff9800", width=2,
                                    dash=(4, 4))

    def _draw_ruler(self):
        if self._ruler_p1 is None:
            return
        x1, y1 = self._ruler_p1
        if self._ruler_p2 is not None:
            x2, y2 = self._ruler_p2
        elif self._last_mouse_world is not None:
            x2, y2 = self._last_mouse_world
        else:
            return
        sx1 = x1 * self.zoom + self.pan_x
        sy1 = y1 * self.zoom + self.pan_y
        sx2 = x2 * self.zoom + self.pan_x
        sy2 = y2 * self.zoom + self.pan_y
        self.canvas.create_line(sx1, sy1, sx2, sy2, fill="#e91e63",
                                width=2, dash=(6, 4), tags="ruler")
        for sx, sy in [(sx1, sy1), (sx2, sy2)]:
            self.canvas.create_oval(sx-5, sy-5, sx+5, sy+5,
                                    fill="#e91e63", outline="white",
                                    width=2, tags="ruler")
        dist = math.hypot(x2 - x1, y2 - y1)
        mx, my = (sx1 + sx2) / 2, (sy1 + sy2) / 2
        self.canvas.create_text(mx, my - 14,
                                text=f"d = {self._fmt_len(dist)}",
                                fill="#e91e63",
                                font=("Consolas", 11, "bold"), tags="ruler")

    def _draw_protractor(self):
        if self._protractor_p1 is None or self._protractor_p2 is None:
            return
        ax, ay = self._protractor_p1
        bx, by = self._protractor_p2
        if self._protractor_p3 is not None:
            cx, cy = self._protractor_p3
        elif self._last_mouse_world is not None:
            cx, cy = self._last_mouse_world
        else:
            return
        sax = ax * self.zoom + self.pan_x
        say = ay * self.zoom + self.pan_y
        sbx = bx * self.zoom + self.pan_x
        sby = by * self.zoom + self.pan_y
        scx = cx * self.zoom + self.pan_x
        scy = cy * self.zoom + self.pan_y
        self.canvas.create_line(sbx, sby, sax, say, fill="#00897b",
                                width=2, tags="protractor")
        self.canvas.create_line(sbx, sby, scx, scy, fill="#00897b",
                                width=2, tags="protractor")
        for sx, sy, color in [(sax, say, "#00897b"),
                              (sbx, sby, "#d32f2f"),
                              (scx, scy, "#00897b")]:
            self.canvas.create_oval(sx-5, sy-5, sx+5, sy+5, fill=color,
                                    outline="white", width=2, tags="protractor")
        v1 = (ax - bx, ay - by); v2 = (cx - bx, cy - by)
        n1 = math.hypot(*v1); n2 = math.hypot(*v2)
        if n1 < 1e-9 or n2 < 1e-9:
            return
        dot = max(-1.0, min(1.0, (v1[0]*v2[0] + v1[1]*v2[1]) / (n1*n2)))
        angle_deg = math.degrees(math.acos(dot))
        self.canvas.create_text((sbx + scx) / 2 + 12, (sby + scy) / 2 - 12,
                                text=f"{angle_deg:.2f}°", fill="#ff6f00",
                                font=("Consolas", 11, "bold"),
                                tags="protractor")

    def _draw_selection_box(self):
        if not self._box_selecting or self._box_start is None \
                or self._box_end is None:
            return
        x1, y1 = self._box_start; x2, y2 = self._box_end
        sx1 = x1 * self.zoom + self.pan_x
        sy1 = y1 * self.zoom + self.pan_y
        sx2 = x2 * self.zoom + self.pan_x
        sy2 = y2 * self.zoom + self.pan_y
        self.canvas.create_rectangle(min(sx1, sx2), min(sy1, sy2),
                                     max(sx1, sx2), max(sy1, sy2),
                                     outline="#1565c0", width=2, dash=(4, 3))

    def _update_status(self):
        self.status_label.config(
            text=f"Объектов: {len(self.shapes)}   "
                 f"Масштаб: {self._to_units(self.zoom):.2f} px/"
                 f"{self.unit_name.get()}   "
                 f"Выделено: {len(self._multi_selected)}")

    def _update_trig_readout(self, wx, wy):
        r = math.hypot(wx, wy)
        if r < 1e-9:
            self.trig_label.config(
                text="r = 0   θ = —   sin = —   cos = —")
            return
        theta = math.degrees(math.atan2(-wy, wx))
        sin_t = -wy / r
        cos_t = wx / r
        self.trig_label.config(
            text=f"r = {self._fmt_len(r)}   θ = {theta:+7.2f}°   "
                 f"sin = {sin_t:+.4f}   cos = {cos_t:+.4f}")

    # ─────────────────────────────────────────────────────────────
    # Zoom / Pan / Fit
    # ─────────────────────────────────────────────────────────────
    def _on_wheel(self, event):
        factor = 1.2 if (getattr(event, "num", 0) == 4 or
                         getattr(event, "delta", 0) > 0) else 1 / 1.2
        wx = (event.x - self.pan_x) / self.zoom
        wy = (event.y - self.pan_y) / self.zoom
        self.zoom *= factor
        self.pan_x = event.x - wx * self.zoom
        self.pan_y = event.y - wy * self.zoom
        self.render_all()

    def zoom_by(self, factor):
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2
        wx = (cx - self.pan_x) / self.zoom
        wy = (cy - self.pan_y) / self.zoom
        self.zoom *= factor
        self.pan_x = cx - wx * self.zoom
        self.pan_y = cy - wy * self.zoom
        self.render_all()

    def _on_pan_start(self, event):
        self._pan_start = (event.x, event.y)
        self._pan_origin = (self.pan_x, self.pan_y)
        try:
            self.canvas.config(cursor="fleur")
        except tk.TclError:
            pass

    def _on_pan_move(self, event):
        if self._pan_start is None:
            return
        dx = event.x - self._pan_start[0]
        dy = event.y - self._pan_start[1]
        self.pan_x = self._pan_origin[0] + dx
        self.pan_y = self._pan_origin[1] + dy
        self.render_all()

    def _on_pan_end(self, event):
        self._pan_start = None
        self._pan_origin = None
        try:
            self.canvas.config(cursor="")
        except tk.TclError:
            pass

    def fit_view(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        if not self.shapes:
            self.zoom = 20.0
            self.pan_x = w / 2
            self.pan_y = h / 2
            self.render_all()
            return
        bboxes = [s.bounding_box() for s in self.shapes]
        x1 = min(b[0] for b in bboxes); y1 = min(b[1] for b in bboxes)
        x2 = max(b[2] for b in bboxes); y2 = max(b[3] for b in bboxes)
        ww = max(x2 - x1, 1e-6); wh = max(y2 - y1, 1e-6)
        pad = 40
        self.zoom = min((w - 2*pad) / ww, (h - 2*pad) / wh)
        cxw = (x1 + x2) / 2; cyw = (y1 + y2) / 2
        self.pan_x = w / 2 - cxw * self.zoom
        self.pan_y = h / 2 - cyw * self.zoom
        self.render_all()

    def _on_canvas_configure(self, event):
        if not self._fitted_once:
            self._fitted_once = True
            self.fit_view()

    # ─────────────────────────────────────────────────────────────
    # Поиск фигур и вершин
    # ─────────────────────────────────────────────────────────────
    def _find_shape_at(self, x, y):
        items = self.canvas.find_overlapping(x - 2, y - 2, x + 2, y + 2)
        for item in reversed(items):
            for tag in self.canvas.gettags(item):
                if tag.startswith("shape_"):
                    try:
                        return int(tag[6:])
                    except ValueError:
                        pass
        return None

    def _find_point_at(self, x, y, threshold=8):
        best = None
        best_d2 = threshold * threshold
        for si, shape in enumerate(self.shapes):
            for pi, (label, lx, ly) in enumerate(shape.get_key_points()):
                rlx, rly = shape._rp(lx, ly)
                wx = shape.x + rlx; wy = shape.y + rly
                sx = wx * self.zoom + self.pan_x
                sy = wy * self.zoom + self.pan_y
                d2 = (sx - x) ** 2 + (sy - y) ** 2
                if d2 <= best_d2:
                    best_d2 = d2
                    best = (si, pi, label, wx, wy)
        return best

    def _find_resize_handle(self, x, y, threshold=8):
        if self.selected_index is None:
            return None
        if self.tool.get() != "select":
            return None
        if self._multi_selected and len(self._multi_selected) > 1:
            return None
        if not (0 <= self.selected_index < len(self.shapes)):
            return None
        x1, y1, x2, y2 = self.shapes[self.selected_index].bounding_box()
        best = None
        best_d2 = threshold * threshold
        for tag, wx, wy in [("tl", x1, y1), ("tr", x2, y1),
                            ("bl", x1, y2), ("br", x2, y2)]:
            sx = wx * self.zoom + self.pan_x
            sy = wy * self.zoom + self.pan_y
            d2 = (sx - x) ** 2 + (sy - y) ** 2
            if d2 <= best_d2:
                best_d2 = d2
                best = tag
        return best

    # ─────────────────────────────────────────────────────────────
    # Мышь
    # ─────────────────────────────────────────────────────────────
    def _on_left_press(self, event):
        wx = (event.x - self.pan_x) / self.zoom
        wy = (event.y - self.pan_y) / self.zoom
        tool = self.tool.get()

        if tool == "ruler":
            if self._ruler_p1 is None or self._ruler_p2 is not None:
                self._ruler_p1 = (wx, wy)
                self._ruler_p2 = None
            else:
                self._ruler_p2 = (wx, wy)
            self.render_all(); return
        if tool == "protractor":
            if self._protractor_p1 is None:
                self._protractor_p1 = (wx, wy)
            elif self._protractor_p2 is None:
                self._protractor_p2 = (wx, wy)
            elif self._protractor_p3 is None:
                self._protractor_p3 = (wx, wy)
            else:
                self._protractor_p1 = (wx, wy)
                self._protractor_p2 = None
                self._protractor_p3 = None
            self.render_all(); return
        if tool == "box":
            self._box_start = (wx, wy)
            self._box_end = (wx, wy)
            self._box_selecting = True
            self._box_additive = (event.state & 0x0001) != 0
            self.render_all(); return

        # resize handle?
        handle = self._find_resize_handle(event.x, event.y)
        if handle is not None and self.selected_index is not None:
            self._resize_handle = handle
            self._resize_shape_idx = self.selected_index
            self._resize_start_box = self.shapes[self.selected_index].bounding_box()
            self._resize_start_mouse = (event.x, event.y)
            self._resize_pre_snapshot = self._snapshot()
            return

        # обычный выбор
        idx = self._find_shape_at(event.x, event.y)
        shift = (event.state & 0x0001) != 0
        if idx is None:
            if not shift:
                self._multi_selected.clear()
                self.select_shape(None)
            return
        if shift:
            if idx in self._multi_selected:
                self._multi_selected.discard(idx)
            else:
                self._multi_selected.add(idx)
            if self._multi_selected:
                self.select_shape(max(self._multi_selected))
            else:
                self.select_shape(None)
            return
        if idx in self._multi_selected and len(self._multi_selected) > 1:
            self.select_shape(idx)
        else:
            self._multi_selected = {idx}
            self.select_shape(idx)

        self._pre_drag_snapshot = self._snapshot()
        self._drag_idx = idx
        self._drag_shapes = list(self._multi_selected) if self._multi_selected else [idx]
        self._drag_start_screen = (event.x, event.y)
        self._drag_start_world = {i: (self.shapes[i].x, self.shapes[i].y)
                                  for i in self._drag_shapes}
        self._drag_moved = False

    def _on_left_motion(self, event):
        tool = self.tool.get()
        if tool == "box":
            if self._box_selecting:
                self._box_end = ((event.x - self.pan_x) / self.zoom,
                                 (event.y - self.pan_y) / self.zoom)
                self.render_all()
            return
        if tool in ("ruler", "protractor"):
            return

        if self._resize_handle is not None:
            self._do_resize_drag(event)
            return

        if self._drag_idx is None:
            return
        dx = event.x - self._drag_start_screen[0]
        dy = event.y - self._drag_start_screen[1]
        if not self._drag_moved and abs(dx) + abs(dy) < 4:
            return
        if not self._drag_moved:
            self._drag_moved = True
            if self._pre_drag_snapshot is not None:
                self.undo_stack.append(self._pre_drag_snapshot)
                if len(self.undo_stack) > 100:
                    self.undo_stack.pop(0)
                self.redo_stack.clear()
            try:
                self.canvas.config(cursor="fleur")
            except tk.TclError:
                pass
        step = self._current_grid_step() if self.snap_to_grid.get() else None
        for i in self._drag_shapes:
            x0, y0 = self._drag_start_world[i]
            new_x = x0 + dx / self.zoom
            new_y = y0 + dy / self.zoom
            if step:
                new_x = round(new_x / step) * step
                new_y = round(new_y / step) * step
            self.shapes[i].set_position(new_x, new_y)
        self.render_all()

    def _do_resize_drag(self, event):
        x1, y1, x2, y2 = self._resize_start_box
        mx0, my0 = self._resize_start_mouse
        dx = (event.x - mx0) / self.zoom
        dy = (event.y - my0) / self.zoom
        w0 = max(x2 - x1, 1e-6); h0 = max(y2 - y1, 1e-6)
        h = self._resize_handle
        if h == "br":
            fx, fy = (w0 + dx) / w0, (h0 + dy) / h0
        elif h == "tr":
            fx, fy = (w0 + dx) / w0, (h0 - dy) / h0
        elif h == "bl":
            fx, fy = (w0 - dx) / w0, (h0 + dy) / h0
        else:
            fx, fy = (w0 - dx) / w0, (h0 - dy) / h0
        factor = max(0.05, min(20.0, (fx + fy) / 2))
        if self._resize_pre_snapshot is not None:
            self.shapes[self._resize_shape_idx] = \
                self._dict_to_shape(self._resize_pre_snapshot[self._resize_shape_idx])
        try:
            self.shapes[self._resize_shape_idx].scale_by(factor)
        except NotImplementedError:
            pass
        self.render_all()

    def _on_left_release(self, event):
        if self.tool.get() == "box":
            if self._box_selecting:
                self._finish_box_select()
            return
        if self._resize_handle is not None:
            if self._resize_pre_snapshot is not None:
                self.undo_stack.append(self._resize_pre_snapshot)
                if len(self.undo_stack) > 100:
                    self.undo_stack.pop(0)
                self.redo_stack.clear()
            self._resize_handle = None
            self._resize_start_box = None
            self._resize_start_mouse = None
            self._resize_shape_idx = None
            self._resize_pre_snapshot = None
            try:
                self.canvas.config(cursor="")
            except tk.TclError:
                pass
            return
        if self._drag_moved and self._drag_idx is not None:
            self._show_stats_for(self.shapes[self._drag_idx])
        self._drag_idx = None
        self._drag_shapes = []
        self._drag_start_world = {}
        self._drag_start_screen = None
        self._drag_moved = False
        self._pre_drag_snapshot = None
        try:
            self.canvas.config(cursor="")
        except tk.TclError:
            pass

    def _finish_box_select(self):
        if self._box_start is None or self._box_end is None:
            self._box_selecting = False
            return
        x1, y1 = self._box_start; x2, y2 = self._box_end
        bx1, bx2 = min(x1, x2), max(x1, x2)
        by1, by2 = min(y1, y2), max(y1, y2)
        selected = set()
        for i, s in enumerate(self.shapes):
            sxb1, syb1, sxb2, syb2 = s.bounding_box()
            if not (sxb2 < bx1 or sxb1 > bx2 or syb2 < by1 or syb1 > by2):
                selected.add(i)
        if self._box_additive:
            self._multi_selected |= selected
        else:
            self._multi_selected = selected
        self._box_selecting = False
        self._box_start = None
        self._box_end = None
        if self._multi_selected:
            self.select_shape(max(self._multi_selected))
        else:
            self.select_shape(None)

    def _on_double_click(self, event):
        idx = self._find_shape_at(event.x, event.y)
        if idx is not None:
            self._multi_selected = {idx}
            self.select_shape(idx)
            self.notebook.select(self.stats_tab)

    def _on_motion(self, event):
        wx_mouse = (event.x - self.pan_x) / self.zoom
        wy_mouse = (event.y - self.pan_y) / self.zoom
        self._last_mouse_world = (wx_mouse, wy_mouse)
        tool = self.tool.get()

        if tool in ("ruler", "protractor"):
            try:
                if self.canvas.cget("cursor") != "crosshair":
                    self.canvas.config(cursor="crosshair")
            except tk.TclError:
                pass
            self.tooltip.hide()
            self._update_trig_readout(wx_mouse, wy_mouse)
            self.render_all()
            return
        if tool == "box":
            try:
                if self.canvas.cget("cursor") != "crosshair":
                    self.canvas.config(cursor="crosshair")
            except tk.TclError:
                pass
            self.tooltip.hide()
            self._update_trig_readout(wx_mouse, wy_mouse)
            return

        if self._pan_start is not None or self._drag_idx is not None \
                or self._resize_handle is not None:
            self.tooltip.hide()
            self._update_trig_readout(wx_mouse, wy_mouse)
            return

        handle = self._find_resize_handle(event.x, event.y)
        if handle is not None:
            cursors = {"tl": "top_left_corner", "tr": "top_right_corner",
                       "bl": "bottom_left_corner", "br": "bottom_right_corner"}
            try:
                c = cursors.get(handle, "sizing")
                if self.canvas.cget("cursor") != c:
                    self.canvas.config(cursor=c)
            except tk.TclError:
                pass
            self.tooltip.hide()
            self._update_trig_readout(wx_mouse, wy_mouse)
            return

        found = self._find_point_at(event.x, event.y)
        if found is not None:
            si, pi, label, wx, wy = found
            if self._hover_vertex != (si, pi):
                self._hover_vertex = (si, pi)
                self.render_all()
            shape = self.shapes[si]
            text = (f"{label}\n"
                    f"X = {self._fmt_coord(wx)}   Y = {self._fmt_coord(wy)}\n"
                    f"{shape.name}  #{si + 1}")
            self.tooltip.show(event.x_root, event.y_root, text)
            try:
                self.canvas.config(cursor="crosshair")
            except tk.TclError:
                pass
            self._update_trig_readout(wx, wy)
            return

        if self._hover_vertex is not None:
            self._hover_vertex = None
            self.render_all()
        self.tooltip.hide()
        cursor = "hand2" if self._find_shape_at(event.x, event.y) is not None else ""
        try:
            if self.canvas.cget("cursor") != cursor:
                self.canvas.config(cursor=cursor)
        except tk.TclError:
            pass
        self._update_trig_readout(wx_mouse, wy_mouse)

    def _on_leave(self, event):
        self.tooltip.hide()
        if self._hover_vertex is not None:
            self._hover_vertex = None
            self.render_all()
        self.trig_label.config(text="r = —   θ = —   sin = —   cos = —")

    # ─────────────────────────────────────────────────────────────
    # Инструменты — смена
    # ─────────────────────────────────────────────────────────────
    def _on_tool_change(self):
        self._ruler_p1 = None
        self._ruler_p2 = None
        self._protractor_p1 = None
        self._protractor_p2 = None
        self._protractor_p3 = None
        self._box_selecting = False
        self._box_start = None
        self._box_end = None
        self._multi_selected.clear()
        self.tooltip.hide()
        try:
            self.canvas.config(
                cursor="" if self.tool.get() == "select" else "crosshair")
        except tk.TclError:
            pass
        self.render_all()

    def _cancel_tool(self):
        self._ruler_p1 = None
        self._ruler_p2 = None
        self._protractor_p1 = None
        self._protractor_p2 = None
        self._protractor_p3 = None
        self._box_selecting = False
        self._box_start = None
        self._box_end = None
        self.render_all()


# ═══════════════════════════════════════════════════════════════════
# 5. ЗАПУСК
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()