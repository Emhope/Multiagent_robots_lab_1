#! /usr/bin/env python3.8

import sys
import time
from typing import List, Dict

import pygame
import random
import pickle

from mars_sim import *


def create_plan(robots: List[Block], blocks: List[Block], goal: GoalPoint) -> Dict[Robot, List[Block]]:
    plan = {robot: [] for robot in robots}
    free_blocks = blocks.copy()
    robots_queue = robots.copy()

    while free_blocks:
        current_sprint = []
        for robot in robots_queue:
            if free_blocks:
                nearest_block = min(free_blocks, key=lambda b: calcDistance(robot.getPosition(), b.getPosition()))
                plan[robot].append(nearest_block)
                free_blocks.remove(nearest_block)
                current_sprint.append((robot, nearest_block))
        robots_queue = sorted(current_sprint, key=lambda i: calcDistance(i[1].getPosition(), goal.getPosition()))
        robots_queue = map(lambda i :i[0], robots_queue)
    return plan


def work_by_plan(plan: Dict[Robot, List[Block]], goal: GoalPoint) -> None:
    for robot in plan:
        if robot.target is goal and calcDistance(robot.getPosition(), goal.getPosition()) < EPS_DIST:
            if robot.attachedObject is not None:
                plan[robot].remove(robot.attachedObject)
                robot.attachedObject.finish = True
                robot.attachedObject = None
                if plan[robot]:
                    robot.target = plan[robot][0]
                    robot.target.reservedRobot = robot
                else:
                    robot.target = None
        
        elif robot.target is not None and calcDistance(robot.getPosition(), robot.target.getPosition()) < EPS_DIST:
            robot.takeObject(robot.target)
            robot.target = goal
        
        elif robot.target is None and plan[robot]:
            robot.target = plan[robot][0]
            robot.target.reservedRobot = robot

            

        

def auction(robots: List[Robot], block: Block) -> Robot:
    """
    Выбор самого выгодного робота для блока
    """
    best_price = np.inf
    best_robot = None

    for robot in robots:
        price = calcDistance(robot.getPosition(), block.getPosition())
        if price < best_price:
            best_price = price
            best_robot = robot
    
    return (best_robot, best_price)




def distributeTasks_auction(robots: List[Robot], blocks: List[Block], goal: Block) -> None:
    
    for robot in robots:
        if robot.target is goal:
            if calcDistance(robot.getPosition(), goal.getPosition()) < EPS_DIST:
                if robot.attachedObject is not None:
                    robot.attachedObject.finish = True
                    robot.attachedObject = None
                    robot.target = None
                else:
                    robot.target = None

        elif robot.target is not None:
            if calcDistance(robot.getPosition(), robot.target.getPosition()) < EPS_DIST:
                robot.takeObject(robot.target)
                robot.target = goal
        

        if robot.attachedObject and robot.target is None:
            robot.target = goal

    free_robots = [robot for robot in robots if robot.target is None]
    free_blocks = [block for block in blocks if block.reservedRobot is None]


    
    while free_robots:
        if not free_blocks:
            for robot in free_robots:
                if calcDistance(robot.getPosition(), goal.getPosition()) >= EPS_DIST:
                    robot.target = goal
                return

        prices = [(auction(free_robots, block), block) for block in free_blocks]
        (best_robot, best_price), best_block = min(prices, key=lambda i: i[0][1])
        best_robot.target = best_block
        best_block.reservedRobot = best_robot

        free_robots = [robot for robot in robots if robot.target is None and robot.attachedObject is None]
        free_blocks = [block for block in blocks if not block.finish and block.reservedRobot is None]



def distributeTasks(robots: List[Robot], blocks: List[Block], goal: Block) -> None:
    """
    Распределение задач (целей) между роботами

    :param robots: список роботов на сцене
    :param blocks: список блоков на сцене
    :param goal: целевая точка на сцене
    :return: нет
    """

    for robot in robots:
        if not (robot.attachedObject is None) and \
            calcDistance(robot.getPosition(), goal.getPosition()) <= EPS_DIST:
            robot.attachedObject.finish = True
            robot.attachedObject = None
            robot.target = None

        elif robot.attachedObject is None:
            block = robot.findNearest(blocks)

            if block is not None and \
                calcDistance(robot.getPosition(), block.getPosition()) <= EPS_DIST:
                robot.takeObject(block)
                robot.target = goal
                return
            
        if robot.target is None and robot.attachedObject is None:
            block = robot.findNearest(blocks)

            if block is None or block.reservedRobot is not None:
                continue
                
            robot.target = block
            block.reservedRobot = robot


def checkMission(robots: List[Robot], blocks: List[Block], goal: Block) -> bool:
    """
    Проверка завершения миссии

    :param robots: список роботов на сцене
    :param blocks: список блоков на сцене
    :param goal: целевая точка на сцене
    :return: признак завершения миссии
    """

    for robot in robots:
        if calcDistance(robot.getPosition(), goal.getPosition()) > EPS_DIST:
            return False
        
    for block in blocks:
        if block.reservedRobot is None:
            return False
        
    return True

def create_random_pos(scene_size):
    return random.randint(0, scene_size[0]), random.randint(0, scene_size[1])

def create_new_accepted_pos(all_poses, min_dist, scene_size):
    pos_accepted = False
    while not pos_accepted:
        pos = create_random_pos(scene_size)
        pos_accepted = True
        for p in all_poses:
            if calcDistance(pos, p) < min_dist:
                pos_accepted = False
                break
    return pos

def create_scene(robot_num, blocks_num, goals, scene_size: tuple):

    print(f'''
im creating scene:
          robots: {robot_num},
          blocks: {blocks_num},
          goals: {goals}
''')

    r = {
        'robots': [],
        'blocks': [],
        'goals': []
    }

    all_poses = []
    min_dist = 10

    for i in range(robot_num):
        new_pos = create_new_accepted_pos(all_poses=all_poses, min_dist=min_dist, scene_size=scene_size)
        all_poses.append(new_pos)
        r['robots'].append(Robot(new_pos[0], new_pos[1], name=f'Robot{i+1}'))

    for i in range(blocks_num):
        new_pos = create_new_accepted_pos(all_poses=all_poses, min_dist=min_dist, scene_size=scene_size)
        all_poses.append(new_pos)
        r['blocks'].append(Block(new_pos[0], new_pos[1], name=f'Block{i+1}'))

    for i in range(goals):
        new_pos = create_new_accepted_pos(all_poses=all_poses, min_dist=min_dist, scene_size=scene_size)
        all_poses.append(new_pos)
        r['goals'].append(GoalPoint(new_pos[0], new_pos[1]))

    with open('last_env.pickle', 'wb') as file:
        pickle.dump(r, file)

    return r

    
def load_scene(scene_name='last_env.pickle'):
    with open(scene_name, 'rb') as file:
        r = pickle.load(file)
    return r




def main(scene_name=None, distribute_method='auction'):
    """
    Главная управляющая функция

    :return: нет
    """
    

    # Инициализаця симуляции и сцены
    pygame.init()
    scene_size = (1000, 500)
    screen = pygame.display.set_mode(scene_size)

    # Список роботов на сцене

    if scene_name == None:
        scene = create_scene(robot_num=3, blocks_num=random.randint(3, 10), goals=1, scene_size=scene_size)
    else:
        scene = load_scene(scene_name)

    robots = scene['robots']

    # Список блоков на сцене
    blocks = scene['blocks']

    # Целевая точка на сцене
    goal = scene['goals'][0]

    if distribute_method == 'static':
        plan = create_plan(robots=robots, blocks=blocks, goal=goal)
        for robot in plan:
            print(f'{robot.name}:')
            for i, block in enumerate(plan[robot]):
                print(f'\t{i+1}. {block.name}')
            print()

    start = time.time()
    while True:
        # Проверка заверешения симуляции
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Основная логика МАРС
        if checkMission(robots, blocks, goal) is True:
            break
        
        if distribute_method == 'auction':
            distributeTasks_auction(robots, blocks, goal)
        elif distribute_method == 'static':
            work_by_plan(plan=plan, goal=goal)
        else:
            distributeTasks(robots, blocks, goal)

        # Отрисовка объектов
        screen.fill((255, 255, 255))

        for robot in robots:
            robot.simulate()
            robot.drawObject(screen)

        for block in blocks:
            block.drawObject(screen)

        goal.drawObject(screen)

        pygame.display.update()
        pygame.time.delay(50)
    
    print(f"method: {distribute_method}\nTime: {time.time() - start}\n")


if __name__ == '__main__':
    main(scene_name='last_env.pickle', distribute_method='static')
    main(scene_name='last_env.pickle', distribute_method='auction')

