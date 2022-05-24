from unittest import TestCase, expectedFailure
from flowcontrol.strategy.controlaction.area import *


class TestPoint(TestCase):

    def test__compare_points(self):
        p1 = Point()
        p2 = Point()
        self.assertEqual(p1, p2)


class TestCircle(TestCase):

    def test__center(self):
        c = Circle()
        assert c.get_x() == 0.0 and c.get_y() == 0.0

    def test__center_update(self):
        x_exp = -1
        y_exp = 10000

        c = Circle()
        c.set_x(x_exp)
        c.set_y(y_exp)
        assert c.get_x() == x_exp and c.get_y() == y_exp

    def test__json_representation(self):
        c = Circle(x=-1.0, y=2.00000001, radius=2.1)
        expected = '{\n    "radius": 2.1,\n    "center": {\n        "x": -1.0,\n        "y": 2.00000001\n    },\n    "type": "CIRCLE"\n}'
        assert expected == c.toJSON()

    def test__radius(self):
        c = Circle()
        r_val = 2.0
        c.set_radius(r_val)

        assert c.radius == r_val

    @expectedFailure
    def test__radius_not_allowed(self):
        c = Circle()
        r_val = 0.0
        c.set_radius(r_val)
        assert c.radius == r_val

    def test__type(self):
        assert Circle.SHAPETYPE == "CIRCLE"


class TestPolygon(TestCase):

    def test__polygon(self):
        p = Polygon()
        square = Polygon.get_default()
        assert square == p.points  # compare elementwise

    def test__polygon_update_point(self):
        p = Polygon()
        new_x = 3.0
        index = 1
        p.set_point(index=index, x=new_x)
        assert p.points[index].x == new_x

    @expectedFailure
    def test__non_allowed_update(self):
        p = Polygon([Point(0, 0), Point(1, 0), Point(1, 1), Point(0.5, 2)])
        y_ = 1.0  # point 2 = point 3
        p.set_point(index=1, y=y_)

    def test__json_representation(self):
        p = Polygon([Point(-5, 0), Point(5, 0), Point(0, 3)])
        expected = '{\n    "type": "POLYGON",\n    "points": [\n        {\n            "x": -5,\n            "y": 0\n        },\n        {\n            "x": 5,\n            "y": 0\n        },\n        {\n            "x": 0,\n            "y": 3\n        }\n    ]\n}'
        actual = p.toJSON()
        assert expected == actual


    def test__type(self):
        assert Polygon.SHAPETYPE == "POLYGON"

class TestRectangle(TestCase):

    def test__default_parameter(self):
        r = Rectangle()
        assert r.x == 0
        assert r.y == 0
        assert r.width == 1
        assert r.height == 1

    def test__type(self):
        assert Rectangle.SHAPETYPE == "RECTANGLE"

    def test__allowed_height(self):
        r = Rectangle()
        h = 2.0
        r.set_height(h)
        assert r.height == h

    @expectedFailure
    def test__unallowed_height(self):
        r = Rectangle()
        h = 0.0
        r.set_height(h)
        assert r.height == h

    def test__allowed_width(self):
        r = Rectangle()
        w = 2.0
        r.set_width(w)
        assert r.width == w

    @expectedFailure
    def test__unallowed_width(self):
        r = Rectangle()
        w = 0.0
        r.set_width(w)
        assert r.width == w

    def test__json_representation(self):
        p = Rectangle(width=2.22)
        expected = '{\n    "x": 0,\n    "y": 0,\n    "width": 2.22,\n    "height": 1,\n    "type": "RECTANGLE"\n}'
        actual = p.toJSON()
        assert expected == actual






