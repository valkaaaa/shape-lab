"""Модели геометрических фигур."""
import math

__all__ = [
    "Shape", "Circle", "Square", "Rectangle", "Triangle",
    "RightTriangle", "EquilateralTriangle", "Ellipse", "Rhombus",
    "Parallelogram", "Trapezoid", "Semicircle", "Ring", "Star",
    "Capsule", "Polygon", "Composite",
]


def _fmt_world(canvas, value):
    """Форматирует мировое значение через formatter, установленный App."""
    f = getattr(canvas, "_formatter", None)
    return f(value) if f else f"{value:g}"


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