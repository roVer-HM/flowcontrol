from typing import Union, List

from flowcontrol.strategy.controlaction.json import JsonRepresentation
from shapely.geometry import Polygon as polygon_
import numpy as np

PRECISION = 0.001

class Shape(JsonRepresentation):
    pass


class Rectangle(Shape):

    SHAPETYPE = "RECTANGLE"

    def __init__(self, x=0, y=0, width=1, height=1):
        self.x = x
        self.y = y
        self._width = width
        self._height = height
        self.type = Rectangle.SHAPETYPE

    @property
    def _height(self):
        return self.height

    @_height.setter
    def _height(self, value):
        if value <= 0.0:
            raise ValueError(f"Height = {value} not allowed. Height must be > 0.")
        self.height = value

    @property
    def _width(self):
        return self.width

    @_width.setter
    def _width(self, value):
        if value <= 0.0:
            raise ValueError(f"Width = {value} not allowed. Width must be > 0.")
        self.width = value

    def set_width(self, value):
        self._width = value

    def set_height(self, value):
        self._height = value


class Point:


    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def to_list(self):
        return [self.x, self.y]

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Polygon(Shape):

    SHAPETYPE = "POLYGON"


    def __init__(self, points: List[Point] = None):
        self.type = Polygon.SHAPETYPE

        if points == None:
            points = self.get_default()

        self._points = points

    @classmethod
    def get_default(self) -> List[Point]:
        # unit square
        return [Point(0,0), Point(1,0), Point(1,1), Point(0,1)]

    def check_polygon(self, pointList):
        points = self.to_list(pointList)

        if points[0] == points[-1]:
            points = points[:-1] # start point != end point
            print("Warning: removed duplicate point.")

        # does not work with set, use OrderedDict instead
        if len(np.unique(np.array(points), axis=0)) != len(points):
            raise ValueError(f"Polygon {points} contains duplicate points. Not allowed.")


        p = polygon_(points)
        if p.area == 0:
            raise ValueError(f"Polygon {points} has area = 0. Not allowed.")

        if p.minimum_clearance <= PRECISION:
            raise ValueError(f"Points of the polygon {points} are overlapping (precision = {PRECISION}).")

    def to_list(self, pointList):
        points = [p.to_list() for p in pointList]
        return points

    @property
    def _points(self):
        return self.points

    @_points.setter
    def _points(self, pointlist):

        self.check_polygon(pointlist)
        self.points = pointlist

    def set_points(self, points):
        self._points = points

    def set_point(self, index : int, x=None, y=None):
        point = self.points[index]
        if x != None:
            point.set_x(x=x)
        if y != None:
            point.set_y(y=y)
        self.check_polygon(self.points)





class Circle(Shape):

    SHAPETYPE = "CIRCLE"

    def __init__(self, x : float = 0.0 , y : float = 0.0 , radius : float = 1.0):
        self._radius = radius
        self.center = Point(x = x, y = y)
        self.type = Circle.SHAPETYPE

    @property
    def _radius(self):
       return self.radius

    @_radius.setter
    def _radius(self, value):
        if value <= 0.0:
            raise ValueError(f"Radius = {value} not allowed. Radius must be > 0.")
        self.radius = value

    def set_x(self, x):
        self.center.x = x

    def set_y(self, y):
        self.center.y = y

    def get_x(self):
        return self.center.x

    def get_y(self):
        return self.center.y

    def set_radius(self, value):
        self._radius = value


if __name__ == "__main__":

    r = Rectangle(0, 1, 6, 6)
    r.toJSON()
