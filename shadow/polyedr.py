from math import pi
from functools import reduce
from operator import add
from common.r3 import R3
from common.tk_drawer import TkDrawer


class Segment:
    """ Одномерный отрезок """
    # Параметры конструктора: начало и конец отрезка (числа)

    def __init__(self, beg, fin):
        self.beg, self.fin = beg, fin

    # Отрезок вырожден?
    def is_degenerate(self):
        return self.beg >= self.fin

    # Пересечение с отрезком
    def intersect(self, other):
        if other.beg > self.beg:
            self.beg = other.beg
        if other.fin < self.fin:
            self.fin = other.fin
        return self

    # Разность отрезков
    # Разность двух отрезков всегда является списком из двух отрезков!
    def subtraction(self, other):
        return [Segment(
            self.beg, self.fin if self.fin < other.beg else other.beg),
            Segment(self.beg if self.beg > other.fin else other.fin, self.fin)]


class Edge:
    """ Ребро полиэдра """
    # Начало и конец стандартного одномерного отрезка
    SBEG, SFIN = 0.0, 1.0

    # Параметры конструктора: начало и конец ребра (точки в R3)
    def __init__(self, beg, fin):
        self.beg, self.fin = beg, fin
        # Список «просветов»
        self.gaps = [Segment(Edge.SBEG, Edge.SFIN)]

    # Учёт тени от одной грани
    def shadow(self, facet):
        # «Вертикальная» грань не затеняет ничего
        if facet.is_vertical():
            return
        # Нахождение одномерной тени на ребре
        shade = Segment(Edge.SBEG, Edge.SFIN)
        for u, v in zip(facet.vertexes, facet.v_normals()):
            shade.intersect(self.intersect_edge_with_normal(u, v))
            if shade.is_degenerate():
                return

        shade.intersect(
            self.intersect_edge_with_normal(
                facet.vertexes[0], facet.h_normal()))
        if shade.is_degenerate():
            return
        # Преобразование списка «просветов», если тень невырождена
        gaps = [s.subtraction(shade) for s in self.gaps]
        self.gaps = [
            s for s in reduce(add, gaps, []) if not s.is_degenerate()]

    # Преобразование одномерных координат в трёхмерные
    def r3(self, t):
        return self.beg * (Edge.SFIN - t) + self.fin * t

    # Пересечение ребра с полупространством, задаваемым точкой (a)
    # на плоскости и вектором внешней нормали (n) к ней
    def intersect_edge_with_normal(self, a, n):
        f0, f1 = n.dot(self.beg - a), n.dot(self.fin - a)
        if f0 >= 0.0 and f1 >= 0.0:
            return Segment(Edge.SFIN, Edge.SBEG)
        if f0 < 0.0 and f1 < 0.0:
            return Segment(Edge.SBEG, Edge.SFIN)
        x = - f0 / (f1 - f0)
        return Segment(Edge.SBEG, x) if f0 < 0.0 else Segment(x, Edge.SFIN)

    def visibility(self):
        eps = 1e-9
        visible_len = sum(g.fin - g.beg for g in self.gaps)

        if visible_len < eps:
            return "not_seen"
        if visible_len > 1.0 - eps:
            return "seen"
        return "half_seen"

class Facet:
    """ Грань полиэдра """
    # Параметры конструктора: список вершин

    def __init__(self, vertexes, orig_vertexes = None, edges = None):
        self.vertexes = vertexes
        self.orig_vertexes = orig_vertexes if orig_vertexes is not None else []
        self.edges = edges if edges is not None else []

    # «Вертикальна» ли грань?
    def is_vertical(self):
        return self.h_normal().dot(Polyedr.V) == 0.0

    # Нормаль к «горизонтальному» полупространству
    def h_normal(self):
        n = (
            self.vertexes[1] - self.vertexes[0]).cross(
            self.vertexes[2] - self.vertexes[0])
        return n * (-1.0) if n.dot(Polyedr.V) < 0.0 else n

    # Нормали к «вертикальным» полупространствам, причём k-я из них
    # является нормалью к грани, которая содержит ребро, соединяющее
    # вершины с индексами k-1 и k
    def v_normals(self):
        return [self._vert(x) for x in range(len(self.vertexes))]

    # Вспомогательный метод
    def _vert(self, k):
        n = (self.vertexes[k] - self.vertexes[k - 1]).cross(Polyedr.V)
        return n * \
            (-1.0) if n.dot(self.vertexes[k - 1] - self.center()) < 0.0 else n

    # Центр грани
    def center(self):
        return sum(self.vertexes, R3(0.0, 0.0, 0.0)) * \
            (1.0 / len(self.vertexes))

    def proj_perimeter(self):
        p = 0.0
        for e in self.edges:
            # Предполагается стандартная реализация R3 с атрибутами x, y
            dx = e.fin.x - e.beg.x
            dy = e.fin.y - e.beg.y
            p += (dx * dx + dy * dy) ** 0.5
        return p


class Polyedr:
    """ Полиэдр """
    # вектор проектирования
    V = R3(0.0, 0.0, 1.0)

    # Параметры конструктора: файл, задающий полиэдр
    def __init__(self, file):
        # списки вершин, исходных вершин, рёбер и граней полиэдра
        self.vertexes, self.orig_vertexes, self.edges, self.facets = [], [], [], []
        self.edge_map = {}

        # Читаем все строки, убираем пустые, чтобы нумерация не сбивалась
        with open(file) as f:
            lines = [line.strip() for line in f if line.strip()]

        # 1. Первая строка: коэффициент гомотетии и углы Эйлера
        buf = lines[0].split()
        c = float(buf.pop(0))
        alpha, beta, gamma = (float(x) * pi / 180.0 for x in buf)

        # 2. Вторая строка: число вершин, граней и рёбер
        nv, nf, ne = (int(x) for x in lines[1].split())

        # 3. Задание всех вершин полиэдра
        for line in lines[2:2 + nv]:
            x, y, z = (float(x) for x in line.split())
            # Исходные координаты (БЕЗ трансформации) для проверки сферы
            self.orig_vertexes.append(R3(x, y, z))
            # Преобразованные координаты для отрисовки и расчёта теней
            self.vertexes.append(R3(x, y, z).rz(alpha).ry(beta).rz(gamma) * c)

        # 4. Задание граней и рёбер
        for line in lines[2 + nv:]:
            buf = line.split()
            size = int(buf.pop(0))
            # массив индексов вершин этой грани (0-based)
            v_indices = [int(n) - 1 for n in buf]

            # массивы точек вершин (преобразованных и исходных)
            facet_verts = [self.vertexes[i] for i in v_indices]
            orig_facet_verts = [self.orig_vertexes[i] for i in v_indices]

            facet_edges = []
            for k in range(size):
                i1, i2 = v_indices[k - 1], v_indices[k]
                # Ключ ребра не зависит от порядка вершин: (0,1) == (1,0)
                key = tuple(sorted((i1, i2)))
                if key not in self.edge_map:
                    new_edge = Edge(self.vertexes[i1], self.vertexes[i2])
                    self.edge_map[key] = new_edge
                    self.edges.append(new_edge)
                facet_edges.append(self.edge_map[key])

            # задание самой грани (передаём оба списка вершин + рёбра)
            self.facets.append(Facet(facet_verts, orig_facet_verts, facet_edges))

    # Метод изображения полиэдра
    def draw(self, tk):  # pragma: no cover
        tk.clean()
        for e in self.edges:
            for f in self.facets:
                e.shadow(f)
            for s in e.gaps:
                tk.draw_line(e.r3(s.beg), e.r3(s.fin))

    # Метод вычисления требуемой характеристики
    def calc_invisible_faces_perimeter_sum(self):
        # 1. Сброс и расчёт теней для всех рёбер
        for e in self.edges:
            e.gaps = [Segment(Edge.SBEG, Edge.SFIN)]  # обязательный сброс просветов
            for f in self.facets:
                e.shadow(f)

        total_perim = 0.0
        for facet in self.facets:
            # Проверяем, что все рёбра грани полностью невидимы
            if all(e.visibility() == "not_seen" for e in facet.edges):
                # Центр грани считаем по ИСХОДНЫМ координатам (до гомотетии и поворота)
                c = sum(facet.orig_vertexes, R3(0.0, 0.0, 0.0)) * (1.0 / len(facet.orig_vertexes))

                # Проверка строгого попадания в сферу радиуса 2 (r^2 < 4)
                if c.dot(c) < 4.0:
                    total_perim += facet.proj_perimeter()

        print(f"Сумма периметров проекций: {total_perim:.6f}")
        return total_perim