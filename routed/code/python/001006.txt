"""Creates a brownian tree"""
import random
import os
import numpy as np
from PIL import Image

random.seed()

class MyTuple():
    """Custom tuple with operator overloads"""
    def __init__(self, x, y):
        self.x_val = x
        self.y_val = y

    def __add__(self, rhs):
        return MyTuple(self.x_val + rhs.x_val, self.y_val + rhs.y_val)

    def __sub__(self, rhs):
        return MyTuple(self.x_val - rhs.x_val, self.y_val - rhs.y_val)

    def __lt__(self, rhs):
        return self.x_val < rhs.x_val and self.y_val < rhs.y_val

    def __gt__(self, rhs):
        return self.x_val > rhs.x_val and self.y_val > rhs.y_val

    def set_vals(self, x, y):
        """sets both values"""
        self.x_val = x
        self.y_val = y

    def get_vals(self):
        """casts to a normal tuple"""
        return (self.x_val, self.y_val)


class Grid():
    """Stores the data about the grid and tree"""
    def __init__(self, size):
        """grid constructor"""
        self.size = size
        self.data = np.zeros(self.size.get_vals(), dtype=np.uint8)
        self.max_steps = 0

    def get_val(self, location):
        """returns the cell value at that location"""
        return self.data[location.x_val, location.y_val]

    def is_occupied(self, location):
        """returns True if the location is occupied"""
        return self.data[location.x_val, location.y_val]

    def set_val(self, location, steps):
        """sets the value at that location"""
        if self.max_steps < steps:
            self.max_steps = steps
        self.data[location.x_val, location.y_val] = 255

    def is_outside_bounds(self, location):
        """Checks if the location supplied is inside the grid"""
        lower = location > MyTuple(-1, -1)
        upper = location < self.size
        return upper and lower

    def normalise(self):
        max = self.max_steps
        def normalise(data):
            return 255 - (data / (self.max_steps / 255))
        np.vectorize(normalise)(self.data)

BOUNDS = MyTuple(100, 75)
# BOUNDS = MyTuple(160, 120)

LEFT = MyTuple(-1, 0)
UP = MyTuple(0, 1)
RIGHT = MyTuple(1, 0)
DOWN = MyTuple(0, -1)
NONE = MyTuple(0, 0)
DIRECTIONS = [UP, DOWN, LEFT, RIGHT]


class Particle():
    """Stores data about individual particles"""
    def __init__(self, direction, location):
        """particle constructor"""
        self.direction = direction
        self.location = location
        self.is_free = True

    def move(self, new_direction):
        """moves particle in a direction"""
        self.direction = new_direction
        self.location += new_direction

    def fix_location(self):
        """sets the location of said particle"""
        self.direction = NONE
        self.is_free = False


def random_xy_loc(bounds):
    """Creates a random xy tuple within bounds"""
    return MyTuple(random.randint(0, bounds.x_val - 1), random.randint(0, bounds.y_val - 1))


def get_next_direction():
    return random.choice(DIRECTIONS)


def main():
    """main init"""
    data_grid = Grid(BOUNDS)

    max_particles = int(BOUNDS.x_val * BOUNDS.y_val / 3)

    for y in range(BOUNDS.y_val):
        for x in range(BOUNDS.x_val):
            if x == 0 or x == (BOUNDS.x_val - 1) or y == 0 or y == (BOUNDS.y_val - 1):
                data_grid.set_val(MyTuple(x, y), 1)

    data_grid.set_val(MyTuple(int(BOUNDS.x_val / 2), int(BOUNDS.y_val / 2)), 1)

    is_occupied = data_grid.is_occupied
    is_outside_bounds = data_grid.is_outside_bounds

    for i in range(max_particles):
        count = -1
        location = random_xy_loc(BOUNDS)
        while is_occupied(location):
            location = random_xy_loc(BOUNDS)
        new_particle = Particle(direction=NONE, location=location)
        while new_particle.is_free:
            count += 1
            direction = get_next_direction()
            new_location = new_particle.location + direction
            if not is_outside_bounds(new_location):
                continue
            if not is_occupied(new_location):
                new_particle.move(direction)
            else:
                new_particle.fix_location()
        data_grid.set_val(new_particle.location, count)
        print(f"Finished {i + 1}, loops: {count}")
    output_name = f"time_data_{max_particles}_{BOUNDS.get_vals()}.bmp"
    full_path = os.path.join(os.path.dirname(__file__), output_name)
    Image.fromarray(data_grid.data).save(full_path)


if __name__ == "__main__":
    main()
