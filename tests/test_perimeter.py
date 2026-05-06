#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import unittest
from pathlib import Path
import sys

# Убедитесь, что путь к модулю Polyedr соответствует вашей структуре проекта
from shadow.polyedr import Polyedr

class TestPerimeterCalculation(unittest.TestCase):
    """Тесты для проверки корректности подсчёта суммы периметров проекций"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path("test_geom_files")
        cls.test_dir.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        for f in cls.test_dir.glob("*.geom"):
            f.unlink()
        cls.test_dir.rmdir()

    def _write_geom(self, filename, content):
        path = self.test_dir / filename
        path.write_text(content.strip() + "\n")
        return str(path)

    def test_01_fully_invisible_inside_sphere(self):
        """Тест 1: Грань полностью невидима и внутри сферы.
           Ожидается: периметр проекции = 4.0 (квадрат 1x1 в XY)"""
        geom = """1.0 0.0 0.0 0.0
8 2 8
-2.0 -2.0 1.5
 2.0 -2.0 1.5
 2.0  2.0 1.5
-2.0  2.0 1.5
-0.5 -0.5 0.5
 0.5 -0.5 0.5
 0.5  0.5 0.5
-0.5  0.5 0.5
4 1 2 3 4
4 5 6 7 8"""
        path = self._write_geom("test_invis.geom", geom)
        p = Polyedr(path)
        result = p.calc_invisible_faces_perimeter_sum()
        self.assertAlmostEqual(result, 4.0, places=5,
                               msg="Периметр полностью невидимой грани внутри сферы должен быть 4.0")

    def test_02_invisible_outside_sphere(self):
        """Тест 2: Грань полностью невидима, но центр вне сферы (z=3.0 -> r²=9 > 4).
           Ожидается: 0.0"""
        geom = """1.0 0.0 0.0 0.0
8 2 8
-2.0 -2.0 1.5
 2.0 -2.0 1.5
 2.0  2.0 1.5
-2.0  2.0 1.5
-0.5 -0.5 3.0
 0.5 -0.5 3.0
 0.5  0.5 3.0
-0.5  0.5 3.0
4 1 2 3 4
4 5 6 7 8"""
        path = self._write_geom("test_outside.geom", geom)
        p = Polyedr(path)
        result = p.calc_invisible_faces_perimeter_sum()
        self.assertAlmostEqual(result, 0.0, places=5,
                               msg="Грань вне сферы не должна учитываться, даже если невидима")

    def test_03_partially_visible_inside_sphere(self):
        """Тест 3: Грань частично видима (выступает за контур передней) и внутри сферы.
           Ожидается: 0.0"""
        geom = """1.0 0.0 0.0 0.0
8 2 8
-1.0 -1.0 2.0
 1.0 -1.0 2.0
 1.0  1.0 2.0
-1.0  1.0 2.0
-1.5 -0.5 1.0
 1.5 -0.5 1.0
 1.5  0.5 1.0
-1.5  0.5 1.0
4 1 2 3 4
4 5 6 7 8"""
        path = self._write_geom("test_partial.geom", geom)
        p = Polyedr(path)
        result = p.calc_invisible_faces_perimeter_sum()
        self.assertAlmostEqual(result, 0.0, places=5,
                               msg="Частично видимая грань не должна учитываться")

    def test_04_completely_visible(self):
        """Тест 4: Две непересекающиеся грани. Обе полностью видны.
           Ожидается: 0.0"""
        geom = """1.0 0.0 0.0 0.0
8 2 8
-1.0 -1.0 2.0
 1.0 -1.0 2.0
 1.0  1.0 2.0
-1.0  1.0 2.0
-1.0 -1.0 0.0
 1.0 -1.0 0.0
 1.0  1.0 0.0
-1.0  1.0 0.0
4 1 2 3 4
4 5 6 7 8"""
        path = self._write_geom("test_visible.geom", geom)
        p = Polyedr(path)
        result = p.calc_invisible_faces_perimeter_sum()
        self.assertAlmostEqual(result, 0.0, places=5,
                               msg="Видимая грань не должна учитываться")

if __name__ == "__main__":
    unittest.main(verbosity=2)

