import random
from typing import List
from enum import Enum, auto
import random
import math
import pygame as pg


#  Program to simulate segregation.
#  See : http:#nifty.stanford.edu/2014/mccown-schelling-model-segregation/

# Enumeration type for the Actors
class Actor(Enum):
    BLUE = auto()
    RED = auto()
    NONE = auto()  # NONE used for empty locations


World = List[List[Actor]]  # Type alias

SIZE = 80


def neighbours():
    pg.init()
    model = NeighborsModel(SIZE)
    _view = NeighboursView(model)
    model.run()


class NeighborsModel:
    FRAME_RATE = 20  # Increase number to speed simulation up
    DIST = [0.25, 0.25, 0.50]  # % of RED, BLUE, and NONE
    THRESHOLD = 0.7  # % of surrounding neighbours that should be like me for satisfaction

    @staticmethod
    def __create_world(size, dist) -> World:
        list_of_actors = []
        blue = round(dist[0] * size ** 2)
        red = round(dist[1] * size ** 2)
        none = round(dist[2] * size ** 2)
        for i in range(blue):
            list_of_actors.append(Actor.BLUE)
        for i in range(red):
            list_of_actors.append(Actor.RED)
        for i in range(none):
            list_of_actors.append(Actor.NONE)
        random.shuffle(list_of_actors)
        brave_new_world = to_matrix(list_of_actors)
        return brave_new_world

    def __update_world(self):
        list_of_unsatisfied = []
        empty_locations = self.free_spots()
        random.shuffle(empty_locations)
        for row_num in range(len(self.world)):
            for col_num in range(len(self.world[row_num])):
                same_neighbours, total_neighbours = self.count_same_neighbours(col_num, row_num)
                if same_neighbours <= (self.THRESHOLD * total_neighbours):
                    list_of_unsatisfied.append([row_num, col_num])
        random.shuffle(list_of_unsatisfied)
        self.swap_actors(empty_locations, list_of_unsatisfied)

    def free_spots(self):
        list_of_none = []
        for row_num in range(len(self.world)):
            for col_num in range(len(self.world[row_num])):
                if self.world[row_num][col_num] == Actor.NONE:
                    list_of_none.append([row_num, col_num])
        return list_of_none

    def count_same_neighbours(self, col_num, row_num):
        list_of_neighbours = self.amount_of_neighbours(row_num, col_num)
        total_neighbours = len(list_of_neighbours)
        actor_index = self.world[row_num][col_num]
        same_neighbours = count(list_of_neighbours, actor_index)
        return same_neighbours, total_neighbours

    def swap_actors(self, empty_locations, list_of_unsatisfied):
        for i in range(len(list_of_unsatisfied)):
            empty_spot = empty_locations.pop()
            unsatisfied_index = list_of_unsatisfied[i]
            unsatisfied_row, unsatisfied_col = unsatisfied_index[0], unsatisfied_index[1]
            temp_empty_spot_actor = self.world[empty_spot[0]][empty_spot[1]]
            self.world[empty_spot[0]][empty_spot[1]] = self.world[unsatisfied_row][unsatisfied_col]
            self.world[unsatisfied_row][unsatisfied_col] = temp_empty_spot_actor
            empty_locations.append(unsatisfied_index)

    def amount_of_neighbours(self, row_num: int, col_num: int, distance: int = 1) -> list:
        start_row_num = max(0, row_num - distance)
        end_row_num = min(len(self.world), row_num + distance + 1)
        start_col_num = max(0, col_num - distance)
        end_col_num = min(len(self.world[0]), col_num + distance + 1)

        rows_to_include = range(start_row_num, end_row_num)
        cols_to_include = range(start_col_num, end_col_num)

        a_list = []
        for row in rows_to_include:
            for col in cols_to_include:
                if not (row == row_num and col == col_num) and self.world[row][col] != Actor.NONE:
                    a_list.append(self.world[row][col])
        return a_list

    def __init__(self, size):
        self.world: World = self.__create_world(size, self.DIST)
        self.observers = []  # for enabling discoupled updating of the view, ignore

    def run(self):
        clock = pg.time.Clock()
        running = True
        while running:
            running = self.__on_clock_tick(clock)
        # stop running
        print("Goodbye!")
        pg.quit()

    def __on_clock_tick(self, clock):
        clock.tick(self.FRAME_RATE)  # update no faster than FRAME_RATE times per second
        self.__update_and_notify()
        return self.__check_for_exit()

    # What to do each frame
    def __update_and_notify(self):
        self.__update_world()
        self.__notify_all()

    @staticmethod
    def __check_for_exit() -> bool:
        keep_going = True
        for event in pg.event.get():
            if event.type == pg.QUIT:
                keep_going = False
        return keep_going

    # Use an Observer pattern for views
    def add_observer(self, observer):
        self.observers.append(observer)

    def __notify_all(self):
        for observer in self.observers:
            observer.on_world_update()


# ---------------- Helper methods ---------------------

def to_matrix(list_of_actors):
    out_matrix = []
    for row_num in range(SIZE):
        new_row = []
        for col_num in range(SIZE):
            new_row.append(list_of_actors[row_num * SIZE + col_num])
        out_matrix.append(new_row)
    return out_matrix


def count(a_list, to_find):
    the_count = 0
    for a in a_list:
        if a == to_find:
            the_count += 1
    return the_count


class NeighboursView:
    # static class variables
    WIDTH = 600  # Size for window
    HEIGHT = 600
    MARGIN = 50

    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)

    # Instance methods

    def __init__(self, model: NeighborsModel):
        pg.init()  # initialize pygame, in case not already done
        self.dot_size = self.__calculate_dot_size(len(model.world))
        self.screen = pg.display.set_mode([self.WIDTH, self.HEIGHT])
        self.model = model
        self.model.add_observer(self)

    def render_world(self):
        # # Render the state of the world to the screen
        self.__draw_background()
        self.__draw_all_actors()
        self.__update_screen()

    # Needed for observer pattern
    # What do we do every time we're told the model had been updated?
    def on_world_update(self):
        self.render_world()

    # private helper methods
    def __calculate_dot_size(self, size):
        return max((self.WIDTH - 2 * self.MARGIN) / size, 2)

    @staticmethod
    def __update_screen():
        pg.display.flip()

    def __draw_background(self):
        self.screen.fill(NeighboursView.WHITE)

    def __draw_all_actors(self):
        for row in range(len(self.model.world)):
            for col in range(len(self.model.world[row])):
                self.__draw_actor_at(col, row)

    def __draw_actor_at(self, col, row):
        color = self.__get_color(self.model.world[row][col])
        xy = self.__calculate_coordinates(col, row)
        pg.draw.circle(self.screen, color, xy, self.dot_size / 2)

    # This method showcases how to nicely emulate 'switch'-statements in python
    @staticmethod
    def __get_color(actor):
        return {
            Actor.RED: NeighboursView.RED,
            Actor.BLUE: NeighboursView.BLUE
        }.get(actor, NeighboursView.WHITE)

    def __calculate_coordinates(self, col, row):
        x = self.__calculate_coordinate(col)
        y = self.__calculate_coordinate(row)
        return x, y

    def __calculate_coordinate(self, offset):
        x: float = self.dot_size * offset + self.MARGIN
        return x


if __name__ == "__main__":
    neighbours()
