import sys
import math
from random import *

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
# TODO Add more radars for late game if no more ore to dig
PLACES_FOR_RADARS = [[7, 7], [11, 3], [11, 11], [15, 7], [19, 3], [19, 11], [3, 3], [3, 11], [23, 7], [27, 3], [27, 11]]
MIN_TO_DIG_TO_SET_TRAPS = 5
MAX_FOLLOWING_RADAR = 2
STARTING_GUESS_COLUMN = 7
MAX_ROUND_FOR_TRAPS_IF_NOT_TRAPPED = 150
MAX_ACTIVE_TRAPS = 5
MAX_ORE_TO_SET_RADARS = 10


class Pos:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, pos):
        return abs(self.x - pos.x) + abs(self.y - pos.y)

    def same(self, pos):
        return self.x == pos.x and self.y == pos.y


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
        self.move(Pos(0, self.y), "BACK")

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
        self.amadeusium = int(amadeusium) if amadeusium != '?' else None
        self.hole = hole

    def has_hole(self):
        return self.hole == HOLE

    def update(self, amadeusium, hole):
        self.amadeusium = int(amadeusium) if amadeusium != '?' else None
        self.hole = hole


class Grid:
    def __init__(self):
        self.cells = []
        self.places_for_radar = []
        self.holes = []
        for y in range(height):
            for x in range(width):
                self.cells.append(Cell(x, y, 0, 0))
        self.init_radars()

    def init_radars(self):
        self.places_for_radar = []
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
        self.to_dig_safe = []
        self.suspicious_enemies = {}
        self.previous_turn_enemies = {}
        self.suspicious_pos = []
        self.waiting_robots = []
        self.enemies_trapped = 0
        self.trap_enabled = True
        self.round = 0
        self.total_diggable_amadesium = 0
        self.radar_enabled = True

    def reset(self):
        self.radars = []
        self.traps = []
        self.my_robots = []
        self.enemy_robots = []
        self.to_dig = []
        self.to_dig_safe = []
        self.grid.init_radars()
        self.grid.holes = []
        self.enemies_trapped = 0
        self.total_diggable_amadesium = 0
        self.radar_enabled = True

game = Game()

# game loop
while True:
    # my_score: Players score
    game.my_score, game.enemy_score = [int(i) for i in input().split()]
    game.reset()
    game.round += 1
    for i in range(height):
        inputs = input().split()
        for j in range(width):
            # amadeusium: amount of amadeusium or "?" if unknown
            # hole: 1 if cell has a hole
            amadeusium = inputs[2 * j]
            hole = int(inputs[2 * j + 1])
            cell = game.grid.get_cell(j, i)
            if hole == HOLE:
                game.grid.holes.append(cell)
            cell.update(amadeusium, hole)
            if amadeusium != '?' and int(amadeusium) > 0:
                game.to_dig.append(cell)
    # entity_count: number of entities visible to you
    # radar_cooldown: turns left until a new radar can be requested
    # trap_cooldown: turns left until a new trap can be requested
    entity_count, game.radar_cooldown, game.trap_cooldown = [int(i) for i in input().split()]

    for i in range(entity_count):
        # id: unique id of the entity
        # x,y: position of the entity
        id, type, x, y, item = [int(j) for j in input().split()]

        if type == ROBOT_ALLY:
            game.my_robots.append(Robot(x, y, type, id, item))
        elif type == ROBOT_ENEMY:
            game.enemy_robots.append(Robot(x, y, type, id, item))
            if x == -1 and y == -1:
                game.enemies_trapped += 1
        elif type == TRAP:
            game.traps.append(Entity(x, y, type, id))
        elif type == RADAR:
            game.radars.append(Entity(x, y, type, id))
            game.grid.update_radars(Pos(x, y))

    # Stop luring enemies or adding trap if not efficient
    if game.round > MAX_ROUND_FOR_TRAPS_IF_NOT_TRAPPED:
        game.trap_enabled = False
    else:
        game.trap_enabled = False if len(game.traps) > MAX_ACTIVE_TRAPS else True

    radar_requested = False
    best_candidate_for_radar = None
    best_candidate_for_trap = None
    min_distance_for_radar = 50
    min_distance_for_trap = 50
    next_radar = game.grid.get_best_place_for_radar()
    cell_to_trap = None
    someone_has_a_radar = False
    someone_has_a_trap = False
    following_radar = 0

    # Find if some enemy robot do something suspicious
    for robot in game.enemy_robots:
        if robot.id in game.previous_turn_enemies:
            previous = game.previous_turn_enemies[robot.id]
            # Robot didn't move
            if robot.same(previous):
                # Robot is on QG : it may have a radar or a trap
                if robot.x == 0:
                    game.suspicious_enemies[robot.id] = robot
                else:
                    # Robot potentially release a trap somewhere
                    if robot.id in game.suspicious_enemies:
                        # Match for all accessible holes and mark them
                        for diff in [[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1]]:
                            new_x = robot.x + diff[0]
                            new_y = robot.y + diff[1]
                            cell_to_check = game.grid.get_cell(new_x, new_y)
                            if cell_to_check and cell_to_check.has_hole():
                                game.suspicious_pos.append(cell_to_check)
                        del game.suspicious_enemies[robot.id]

        game.previous_turn_enemies[robot.id] = robot

    # Remove my_traps from other dig list
    new_dig_list = []
    for pos in game.to_dig:
        for trap in game.traps:
            if pos.same(trap):
                break
        else:
            new_dig_list.append(pos)
    game.to_dig = new_dig_list

    # Remove suspicious positions from the to_dig_safe list
    for to_dig in game.to_dig:
        for suspicious in game.suspicious_pos:
            if to_dig.same(suspicious):
                break
        else:
            game.to_dig_safe.append(to_dig)

    # Stop setting radar if enough ore to dig in non suspicious cells
    for cell in game.to_dig_safe:
        game.total_diggable_amadesium += cell.amadeusium
    if game.total_diggable_amadesium > MAX_ORE_TO_SET_RADARS:
        game.radar_enabled = False

    print(f"traps enabled ? {game.trap_enabled} ({len(game.traps)})", file=sys.stderr)
    print(f"radar enabled ? {game.radar_enabled} ({game.total_diggable_amadesium})", file=sys.stderr)
    print(f"{len(game.to_dig)} to dig", file=sys.stderr)
    print(f"{len(game.to_dig_safe)} to dig safe : {','.join(str(p.x) + ':' + str(p.y) for p in game.to_dig_safe)}", file=sys.stderr)
    print(f"{len(game.suspicious_enemies)} suspicious_enemies : {','.join(str(r.id) for i, r in game.suspicious_enemies.items())}", file=sys.stderr)
    print(f"{len(game.suspicious_pos)} suspicious_pos : {','.join(str(p.x) + ':' + str(p.y) for p in game.suspicious_pos)}", file=sys.stderr)
    print(f"{len(game.waiting_robots)} waiting robots : {','.join(str(robot_id) for robot_id in game.waiting_robots)}", file=sys.stderr)

    # Find if someone can a trap
    # TODO maybe don't select this candidate if he's near cristal to dig
    if game.trap_enabled and len(game.to_dig) > MIN_TO_DIG_TO_SET_TRAPS:
        for robot in game.my_robots:
            if robot.item in [-1, 4]:
                distance = Pos(0, robot.y).distance(robot)
                if not best_candidate_for_trap or distance < min_distance_for_trap:
                    best_candidate_for_trap = robot
                    min_distance_for_trap = distance

    # Loop my robot to find priorities first
    for robot in game.my_robots:
        # Do we need a radar
        # TODO find the best radar (nearest to existing vein)  to place and not only the next one
        if game.radar_enabled and len(game.grid.places_for_radar) and not game.radar_cooldown:
            # Find the best candidate to pick the radar (closest to base)
            if robot.item in [-1, 4]:
                distance = robot.x + Pos(0, robot.y).distance(next_radar)
                if not best_candidate_for_radar or distance < min_distance_for_radar:
                    best_candidate_for_radar = robot
                    min_distance_for_radar = distance
        # Has someone already a radar
        if robot.item == 2:
            someone_has_a_radar = True
        # Has someone already a trap
        if robot.item == 3:
            someone_has_a_trap = True

    already_reserved_cells = []
    for robot in game.my_robots:
        # Write an action using print
        # To debug: print("Debug messages...", file=sys.stderr)
        # WAIT|
        # MOVE x y|REQUEST item
        # The robot had a target before and didn't reached it yet
        if robot == best_candidate_for_radar and not someone_has_a_radar:
            robot.request(RADAR)
        elif robot == best_candidate_for_trap and not someone_has_a_trap:
            robot.request(TRAP)
        elif robot.item == 4:
            robot.go_back_to_base()
        elif robot.item == 2 and next_radar:
            # TODO be carefull of suspicious cells, maybe try just on the side
            robot.dig(next_radar, "PLACING RADAR")
        else:
            to_dig = game.to_dig_safe
            if not to_dig:
                to_dig = game.to_dig
                print(f"Passed to non safe digs", file=sys.stderr)
            if len(to_dig):
                min_distance_for_radar = 50
                best_cell = to_dig[0]
                to_delete = 0
                for i, cell in enumerate(to_dig):
                    if robot.item != 3 or robot.item == 3 and cell.amadeusium > 1:
                        distance = robot.distance(cell) + cell.x
                        if distance < min_distance_for_radar:
                            best_cell = cell
                            min_distance_for_radar = distance
                            to_delete = i
                # Maybe wait one turn to lure enemy into believing it will put a trap
                waiting_to_lure_enemy = False
                if best_cell.amadeusium == 3:
                    if robot.x == 0:
                        if robot.id not in game.waiting_robots:
                            waiting_to_lure_enemy = True
                            game.waiting_robots.append(robot.id)
                        else:
                            game.waiting_robots.remove(robot.id)

                # Remove cell from available if this robot depleted it (maybe with others)
                already_reserved_cells.append(best_cell)
                number_of_reservation = 0
                for already_reserved_cell in already_reserved_cells:
                    if already_reserved_cell.x == best_cell.x and already_reserved_cell.y == best_cell.y:
                        number_of_reservation += 1
                if number_of_reservation >= best_cell.amadeusium:
                    del to_dig[to_delete]
                if waiting_to_lure_enemy:
                    robot.wait("LURE ENEMY")
                else:
                    robot.dig(best_cell, "DIGGING")
            elif someone_has_a_radar and following_radar < MAX_FOLLOWING_RADAR:
                robot.move(next_radar)
                following_radar += 1
            else:
                # If nothing particular to do, try to advance on the same row at random
                if not game.grid.holes:
                    robot.dig(Pos(STARTING_GUESS_COLUMN, robot.y), "RANDOM")
                else:
                    for column in range(STARTING_GUESS_COLUMN, width - 1):
                        cell_to_check = game.grid.get_cell(column, min(max(robot.y, 1), 13))
                        for hole in game.grid.holes:
                            if cell_to_check.same(hole):
                                break
                        else:
                            robot.dig(cell_to_check, "RANDOM")
                            break
                    else:
                        robot.wait(f"Nothing better to do")