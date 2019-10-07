import sys
import math

# Deliver more amadeusium to hq (left side of the map) than your opponent. Use radars to find amadeusium but beware of traps!

# height: size of the map
width, height = [int(i) for i in input().split()]

NONE = -1
ROBOT_ALLY = 0
ROBOT_ENEMY = 1
HOLE = 1
RADAR = 2
TRAP = 3
AMADEUSIUM = 4
PLACES_FOR_RADARS = [[3, 3], [3, 11], [7, 7], [11, 3], [11, 11], [15, 7], [19, 3], [19, 11], [23, 7], [27, 3], [27, 11]]


class Pos:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, pos):
        return abs(self.x - pos.x) + abs(self.y - pos.y)


class Entity(Pos):
    def __init__(self, x, y, type, id):
        super().__init__(x, y)
        self.type = type
        self.id = id


class Robot(Entity):
    def __init__(self, x, y, type, id, item):
        super().__init__(x, y, type, id)
        self.item = item
        self.action = None

    def is_dead(self):
        return self.x == -1 and self.y == -1

    def go_back_to_base(self):
        self.move(Pos(0, self.y), "GOING BACK TO BASE WITH ORE")

    def move(self, pos, message=""):
        self.action = f"MOVE {pos.x} {pos.y} {message} ({self.id})"
        print(self.action)

    def wait(self, message=""):
        print(f"WAIT {message} ({self.id})")

    def dig(self, pos, message=""):
        self.action = f"DIG {pos.x} {pos.y} {message} ({self.id})"
        print(self.action)

    def request(self, requested_item, message=""):
        if requested_item == RADAR:
            self.action = f"REQUEST RADAR {message} ({self.id})"
        elif requested_item == TRAP:
            self.action = f"REQUEST TRAP {message} ({self.id})"
        else:
            raise Exception(f"Unknown item {requested_item}")
        print(self.action)

    def __str__(self):
        return f"{self.id}: carry {self.item}"


class Cell(Pos):
    def __init__(self, x, y, amadeusium, hole):
        super().__init__(x, y)
        self.amadeusium = amadeusium
        self.hole = hole

    def has_hole(self):
        return self.hole == HOLE

    def update(self, amadeusium, hole):
        self.amadeusium = amadeusium
        self.hole = hole


class Grid:
    def __init__(self):
        self.cells = []
        self.places_for_radar = []
        for y in range(height):
            for x in range(width):
                self.cells.append(Cell(x, y, 0, 0))

        for pos in PLACES_FOR_RADARS:
            self.places_for_radar.append(Pos(pos[0], pos[1]))

    def get_cell(self, x, y):
        if width > x >= 0 and height > y >= 0:
            return self.cells[x + width * y]
        return None

    def update_radars(self, radar):
        for i, o in enumerate(self.places_for_radar):
            if o.x == radar.x and o.y == radar.y:
                del self.places_for_radar[i]
                break

    def get_best_place_for_radar(self):
        if len(self.places_for_radar):
            return self.places_for_radar[0]
        else:
            return None


class Game:
    def __init__(self):
        self.grid = Grid()
        self.my_score = 0
        self.enemy_score = 0
        self.radar_cooldown = 0
        self.trap_cooldown = 0
        self.radars = []
        self.traps = []
        self.my_robots = []
        self.enemy_robots = []
        self.to_dig = []

    def reset(self):
        self.radars = []
        self.traps = []
        self.my_robots = []
        self.enemy_robots = []
        self.to_dig = []


game = Game()

# game loop
while True:
    # my_score: Players score
    game.my_score, game.enemy_score = [int(i) for i in input().split()]
    game.reset()
    for i in range(height):
        inputs = input().split()
        for j in range(width):
            # amadeusium: amount of amadeusium or "?" if unknown
            # hole: 1 if cell has a hole
            amadeusium = inputs[2 * j]
            hole = int(inputs[2 * j + 1])
            cell = game.grid.get_cell(j, i)
            cell.update(amadeusium, hole)
            if amadeusium != '?' and int(amadeusium) > 0:
                game.to_dig.append(cell)
    # entity_count: number of entities visible to you
    # radar_cooldown: turns left until a new radar can be requested
    # trap_cooldown: turns left until a new trap can be requested
    entity_count, game.radar_cooldown, game.trap_cooldown = [int(i) for i in input().split()]

    for i in range(entity_count):
        # id: unique id of the entity
        # type: 0 for your robot, 1 for other robot, 2 for radar, 3 for trap
        # y: position of the entity
        # item: if this entity is a robot, the item it is carrying (-1 for NONE, 2 for RADAR, 3 for TRAP, 4 for AMADEUSIUM)
        id, type, x, y, item = [int(j) for j in input().split()]

        if type == ROBOT_ALLY:
            game.my_robots.append(Robot(x, y, type, id, item))
        elif type == ROBOT_ENEMY:
            game.enemy_robots.append(Robot(x, y, type, id, item))
        elif type == TRAP:
            game.traps.append(Entity(x, y, type, id))
        elif type == RADAR:
            game.radars.append(Entity(x, y, type, id))
            game.grid.update_radars(Pos(x, y))

    print(f"{len(game.to_dig)} to dig", file=sys.stderr)
    radar_requested = False
    best_candidate_for_radar = None
    min_distance = 50
    next_radar = game.grid.get_best_place_for_radar()
    someone_has_a_radar = False

    for robot in game.my_robots:
        # Do we need a radar
        if len(game.grid.places_for_radar) and not game.radar_cooldown:
            # Find the best candidate to pick the radar (closest to base)
            if robot.item in [-1, 4]:
                distance = robot.x + Pos(0, robot.y).distance(next_radar)
                if not best_candidate_for_radar or distance < min_distance:
                    best_candidate_for_radar = robot
                    min_distance = distance
        # Has someone already a radar
        if robot.item == 2:
            someone_has_a_radar = True

    for robot in game.my_robots:
        # Write an action using print
        # To debug: print("Debug messages...", file=sys.stderr)
        # WAIT|
        # MOVE x y|REQUEST item
        # The robot had a target before and didn't reached it yet

        if best_candidate_for_radar and robot == best_candidate_for_radar:
            robot.request(RADAR)
        elif robot.item == 4:
            robot.go_back_to_base()
        elif robot.item == 2 and next_radar:
            best_place = next_radar
            robot.dig(best_place, "PLACING RADAR")
        else:
            if game.to_dig:
                min_distance = 50
                best_cell = game.to_dig[0]
                to_delete = 0
                for i, cell in enumerate(game.to_dig):
                    distance = robot.distance(cell) + cell.x
                    if distance < min_distance:
                        best_cell = cell
                        min_distance = distance
                        to_delete = i
                del game.to_dig[to_delete]
                robot.dig(best_cell)
            elif someone_has_a_radar:
                robot.move(next_radar)
            else:
                robot.wait(f"Nothing better to do")