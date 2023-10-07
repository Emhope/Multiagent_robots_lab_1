from typing import List, Tuple

import numpy as np
import pygame


# Окрестность достижения объекта
EPS_DIST = 20.0


def calcDistance(point1: List[float], point2: List[float]) -> np.float64:
    """
    Расчёт расстояния между точками

    :param point1: точка 1
    :param point2: точка 2
    :return: расстояние между точками
    """
    
    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]
    return np.sqrt(dx ** 2 + dy ** 2)


class SimObject:
    """
    Объект симуляции МАРС
    """

    def __init__(self, x: float, y: float, r: float, rgb: Tuple[int]) -> None:
        """
        Инициализация экземпляра класса

        :param x: исходная координата объекта на оси X
        :param y: исходная координата объекта на оси Y
        :param r: радиус объекта
        :param color: цвет объекта
        :return: нет
        """
        
        self.x = x     # Координата X
        self.y = y     # Координата Y
        self.r = r     # Радиус объекта
        self.rgb = rgb # Цвет объекта RGB
    
    def drawObject(self, screen: pygame.Surface) -> None:
        """
        Отрисовка объекта

        :param screen: сцена симуляции
        :return: нет
        """
        
        pygame.draw.ellipse(screen, self.rgb,
                            [self.x - self.r, self.y - self.r, 
                             self.r * 2, self.r * 2], 2)
        
    def getPosition(self) -> Tuple[float]:
        """
        Координаты объекта на сцене

        :return: нет
        """

        return self.x, self.y


class GoalPoint(SimObject):
    """
    Целевая точка
    """

    def __init__(self, x: float, y: float) -> None:
        """
        Инициализация экземпляра класса

        :param x: исходная координата объекта на оси X
        :param y: исходная координата объекта на оси Y
        :return: нет
        """

        super().__init__(x, y, 10, (0, 0, 255))


class Block(SimObject):
    """
    Блок
    """
    
    def __init__(self, x: float, y: float) -> None:
        """
        Инициализация экземпляра класса

        :param x: исходная координата объекта на оси X
        :param y: исходная координата объекта на оси Y
        :return: нет
        """

        super().__init__(x, y, 10, (0, 255, 0))
        self.reservedRobot = None # Зарезирвированный за блоком робот
        self.finish = False       # Признак доставки блока в целевую точку



class Robot(SimObject):
    """
    Робот
    """

    def __init__(self, x: float, y: float, range: float = 2000) -> None:
        """
        Инициализация экземпляра класса

        :param x: исходная координата объекта на оси X
        :param y: исходная координата объекта на оси Y
        :return: нет
        """

        super().__init__(x, y, 20, (255, 0, 0))
        self.attachedObject = None # Закрепленный блок
        self.target = None         # Цель движения робота
        self.range = range         # Область видимости робота
    
    def simulate(self) -> None:
        """
        Симуляция движения робота

        :return: нет
        """

        if self.target is not None:
            point1 = self.target.getPosition()
            point2 = self.getPosition()

            v = [c1 - c2 for c1, c2 in zip(point1, point2)]
            dist = calcDistance(point1, point2)

            if dist > 0.0:
                v = v / dist

            self.x += v[0] * 5
            self.y += v[1] * 5
        
        if self.attachedObject is not None:
            self.attachedObject.x = self.x
            self.attachedObject.y = self.y
    
    def findNearest(self, blocks: List[Block]) -> Block:
        """
        Поиск ближайшего блока
        
        :param blocks: список блоков на сцене
        :return: ближайший блок
        """

        res = None
        minDist = np.inf
        
        for block in blocks:
            if block.reservedRobot is not None and \
                block.reservedRobot is not self or \
                    block.finish is True:
                continue

            dist = calcDistance(block.getPosition(), self.getPosition())
            if dist < minDist and dist < self.range:
                minDist = dist
                res = block
        
        return res
    
    def takeObject(self, obj: Block) -> None:
        """
        Подбор блока
        
        :param obj: подбираемый блок
        :return: нет
        """

        if obj is not None and calcDistance(self.getPosition(), obj.getPosition()) < EPS_DIST:
            self.attachedObject = obj
