import sys
import math
from random import *

# height: size of the map
width, height = [int(i) for i in input().split()]

NONE = -1
ROBOT_ALLY = 0
ROBOT_ENEMY = 1
HOLE = 1
RADAR = 2
TRAP = 3
AMADEUSIUM = 4

TRY_TO_BREAK_RADARS = False
TRY_TO_SIMULATE_TRAPS = False
MANUAL_STEPS = True
MAX_REACHABLE_DISTANCE = 4
FIRST_PLACES_FOR_RADARS = [[7, 7], [11, 3], [11, 11], [15, 7], [19, 3], [19, 11], [3, 3], [3, 11], [23, 7], [27, 3], [27, 11]]
SECOND_PLACES_FOR_RADARS = [[7, 0], [15, 0], [23, 0], [7, 14], [15, 14], [23, 14]]
MIN_TO_DIG_TO_SET_TRAPS = 50
MAX_FOLLOWING_RADAR = 2
STARTING_GUESS_COLUMN = 7
MAX_ROUND_FOR_TRAPS_IF_NOT_TRAPPED = 150
MIN_ROUND_TO_TRY_NOT_SAFE_CELLS = 200
MAX_ACTIVE_TRAPS = 5
MAX_ORE_TO_SET_RADARS = 10
NEIGHBORS = [[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1]]
NUMBER_OF_STATIC_FIRST_RADARS = 4
ROW_SUSPECT_WITH_RADARS = [3, 7, 11]


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

    def go_back_to_base(self, grid, enemies, my_traps, message=""):
        self.move(Pos(0, self.y), grid, enemies, my_traps, message if message else "BACK")

    # TODO cas ou ou il pose une mine en meme temps qu'on s'approche juste a côté et il la fait peter le coup d'apres

    def move(self, target, grid, enemies, my_traps, message="", force=False):
        # First find, if not accessible in one move, the next step
        original_target = target
        distance = self.distance(target)
        if MANUAL_STEPS and distance > MAX_REACHABLE_DISTANCE:
            min_distance = 50
            for potential_new_target in grid.get_cells_between_distances(self, 4, 4):
                if potential_new_target.distance(original_target) < min_distance:
                    min_distance = potential_new_target.distance(original_target)
                    target = potential_new_target

        # Find if the destination is dangerous
        if force or not grid.is_destination_dangerous(target, enemies, my_traps) or target.distance(self) > MAX_REACHABLE_DISTANCE:
            print(f"MOVE {target.x} {target.y} {message} ({self.id})")
        else:
            # Find best of all possibilities to land
            best_new_target = None
            min_distance = 50
            for potential_new_target in grid.get_cells_between_distances(self, 0, 4):
                if not grid.is_destination_dangerous(potential_new_target, enemies, my_traps):
                    if not best_new_target or potential_new_target.distance(original_target) < min_distance:
                        best_new_target = potential_new_target
                        min_distance = potential_new_target.distance(original_target)
            if best_new_target:
                print(f"({robot.id}) step too dangerous changing target to {best_new_target.x}/{best_new_target.y}", file=sys.stderr)
                print(f"MOVE {best_new_target.x} {best_new_target.y} {message} ({self.id})")
            else:
                self.wait("DANGER")

    def wait(self, message=""):
        print(f"WAIT {message} ({self.id})")

    def dig(self, target, grid, enemies, my_traps, message="", force=False):
        if self.distance(target) <= 1:
            print(f"DIG {target.x} {target.y} {message} ({self.id})")
        else:
            self.move(Pos(target.x - 1, target.y), grid, enemies, my_traps, message, force)

    def request(self, requested_item, grid, enemies, my_traps, message=""):
        if self.x > 0:
            self.go_back_to_base(grid, enemies, my_traps, message)
        else:
            if requested_item == RADAR:
                print(f"REQUEST RADAR {message} ({self.id})")
            elif requested_item == TRAP:
                print(f"REQUEST TRAP {message} ({self.id})")
            else:
                raise Exception(f"Unknown item {requested_item}")


class Cell(Pos):
    def __init__(self, x, y, amadeusium, hole):
        super().__init__(x, y)
        self.amadeusium = int(amadeusium) if amadeusium != '?' else 0
        self.hole = hole
        self.suspicious = False
        self.enemy = False
        self.trap = False

    def has_hole(self):
        return self.hole == HOLE

    def is_suspicious(self):
        return self.suspicious

    def update(self, amadeusium, hole):
        self.amadeusium = int(amadeusium) if amadeusium != '?' else 0
        self.hole = hole
        self.enemy = False
        self.trap = False


class Grid:
    def __init__(self):
        self.cells = []
        self.first_places_for_availale_radar = []
        self.second_places_for_availale_radar = []
        self.holes = []
        self.radar = False
        for y in range(height):
            for x in range(width):
                self.cells.append(Cell(x, y, 0, 0))
        self.init_radars()

    def init_radars(self):
        self.first_places_for_availale_radar = []
        self.second_places_for_availale_radar = []
        for pos in FIRST_PLACES_FOR_RADARS:
            self.first_places_for_availale_radar.append(self.get_cell(pos[0], pos[1]))
        for pos in SECOND_PLACES_FOR_RADARS:
            self.second_places_for_availale_radar.append(self.get_cell(pos[0], pos[1]))

    def get_cell(self, x, y):
        if width > x >= 0 and height > y >= 0:
            return self.cells[x + width * y]
        return None

    def update_radars(self, radar):
        for i, o in enumerate(self.first_places_for_availale_radar):
            for check_cell in self.get_cells_between_distances(o, 0, 1):
                if check_cell.same(radar):
                    del self.first_places_for_availale_radar[i]
                    break
        for i, o in enumerate(self.second_places_for_availale_radar):
            for check_cell in self.get_cells_between_distances(o, 0, 1):
                if check_cell.same(radar):
                    del self.second_places_for_availale_radar[i]
                    break

    def get_best_place_for_radar(self):
        is_first_place = self.best_place_for_radar_in_list(self.first_places_for_availale_radar, FIRST_PLACES_FOR_RADARS)
        if is_first_place:
            return is_first_place
        else:
            return self.best_place_for_radar_in_list(self.second_places_for_availale_radar, SECOND_PLACES_FOR_RADARS)

    def best_place_for_radar_in_list(self, list_available_positions, list_total_positions):
        if len(list_available_positions):
            # Let the 4 first radar
            best_place = list_available_positions[0]
            if len(list_available_positions) > len(list_total_positions) - NUMBER_OF_STATIC_FIRST_RADARS:
                return best_place

            maximum_chance = 0
            for place_for_radar in list_available_positions:
                chance = 0
                for inspected_cell in self.cells:
                    if inspected_cell.distance(place_for_radar) == 4:
                        chance += inspected_cell.hole + inspected_cell.amadeusium
                if chance > maximum_chance:
                    maximum_chance = chance
                    best_place = place_for_radar
            return best_place
        else:
            return None

    def get_cells_between_distances(self, cell, min_distance, max_distance):
        corresponding_cells = []
        min_range = -max_distance
        max_range = max_distance + 1
        for x in range(min_range, max_range):
            for y in range(min_range, max_range):
                if min_distance <= abs(x) + abs(y) <= max_distance and 0 <= cell.x + x < width and 0 <= cell.y + y < height:
                    corresponding_cell = self.get_cell(cell.x + x, cell.y + y)
                    if corresponding_cell:
                        corresponding_cells.append(corresponding_cell)
        return corresponding_cells

    def get_suspicious_cells(self):
        return list(filter(lambda cell: cell.is_suspicious(), self.cells))

    def is_destination_dangerous(self, cell, enemies, my_traps):
        for diff in NEIGHBORS:
            check_x = cell.x + diff[0]
            check_y = cell.y + diff[1]
            check_cell = self.get_cell(check_x, check_y)
            # TODO pas exactement, il peut faire péter une bombe qui lui est reliée aussi
            if check_cell and check_cell.is_suspicious() and len(list(filter(lambda x: x.distance(check_cell) <= 5, enemies))):
                return True
            for trap in my_traps:
                if check_cell and check_cell.same(trap):
                    return True
        return False

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
        self.waiting_robots = []
        self.enemies_trapped = 0
        self.trap_enabled = True
        self.round = 0
        self.total_diggable_amadesium = 0
        self.radar_enabled = True
        self.trying_suspicious_cells = []
        self.enemy_is_trapping = False

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
            robot = Robot(x, y, type, id, item)
            game.my_robots.append(robot)
            if robot.is_dead() and robot.id in game.trying_suspicious_cells:
                game.enemy_is_trapping = True
        elif type == ROBOT_ENEMY:
            robot = Robot(x, y, type, id, item)
            game.enemy_robots.append(robot)
            if not robot.is_dead():
                game.grid.get_cell(x, y).enemy = True
            else:
                game.enemies_trapped += 1
        elif type == TRAP:
            game.traps.append(Entity(x, y, type, id))
            game.grid.get_cell(x, y).trap = True
        elif type == RADAR:
            game.radars.append(Entity(x, y, type, id))
            game.grid.update_radars(Pos(x, y))



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
    breaking_radar = False
    taking_risk_on_suspicious = False

    # Find if some enemy robot do something suspicious
    for robot in game.enemy_robots:
        if robot.id in game.previous_turn_enemies:
            previous = game.previous_turn_enemies[robot.id]
            # Robot didn't move
            if robot.same(previous):
                # Robot is on QG : it may have a radar or a trap
                if robot.x == 0:
                    game.suspicious_enemies[robot.id] = robot
                # Robot potentially release a trap somewhere
                if robot.id in game.suspicious_enemies:
                    # Match for all accessible holes and mark them
                    for cell_to_check in game.grid.get_cells_between_distances(robot, 0, 1):
                        if cell_to_check and cell_to_check.has_hole():
                            game.grid.get_cell(cell_to_check.x, cell_to_check.y).suspicious = True
            elif robot.x == 0 and robot.id in game.suspicious_enemies:
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
        for suspicious in game.grid.get_suspicious_cells():
            if to_dig.same(suspicious):
                break
        else:
            game.to_dig_safe.append(to_dig)

    # Stop luring enemies or adding trap if not efficient
    if game.round > MAX_ROUND_FOR_TRAPS_IF_NOT_TRAPPED:
        game.trap_enabled = False
    else:
        game.trap_enabled = False if len(game.traps) > MAX_ACTIVE_TRAPS or len(game.to_dig_safe) < MIN_TO_DIG_TO_SET_TRAPS else True

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
    print(f"{len(game.grid.get_suspicious_cells())} suspicious_pos : {','.join(str(p.x) + ':' + str(p.y) for p in game.grid.get_suspicious_cells())}", file=sys.stderr)
    print(f"{len(game.waiting_robots)} waiting robots : {','.join(str(robot_id) for robot_id in game.waiting_robots)}", file=sys.stderr)

    # Loop my robot to find priorities first
    for robot in list(filter(lambda r: not r.is_dead(), game.my_robots)):
        # Do we need a radar
        if game.radar_enabled and next_radar and not game.radar_cooldown:
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
        # Find if we are in a situation where we can destroy more than one enemy
        destroyable_enemies = 0
        cell_to_check = None
        for diff in NEIGHBORS:
            new_x = robot.x + diff[0]
            new_y = robot.y + diff[1]
            cell_to_check = game.grid.get_cell(new_x, new_y)
            destroyable_enemies = 0
            if cell_to_check and cell_to_check.is_suspicious():
                for enemy in game.enemy_robots:
                    if enemy.distance(cell_to_check) == 1:
                        destroyable_enemies += 1
                if destroyable_enemies > 1:
                    break

        # Find if we can destroy a potential radar
        suspected_reachable_radar = None
        for cell in game.grid.get_suspicious_cells():
            if cell.distance(robot) <= MAX_REACHABLE_DISTANCE and cell.y in ROW_SUSPECT_WITH_RADARS:
                suspected_reachable_radar = cell

        # Find if we can destroy a radar
        if robot.is_dead():
            robot.wait("DEAD XXX")
        elif cell_to_check and destroyable_enemies > 1:
            robot.dig(cell_to_check, game.grid, game.enemy_robots, game.traps, "BOOM")
        elif robot == best_candidate_for_radar and not someone_has_a_radar:
            robot.request(RADAR, game.grid, game.enemy_robots, game.traps, "RADAR")
        elif robot.item == 2 and next_radar:
            if not next_radar.suspicious:
                robot.dig(next_radar, game.grid, game.enemy_robots, game.traps, "DIRECT RADAR")
            else:
                print("calling for next radar", file=sys.stderr)
                for cell_to_check in game.grid.get_cells_between_distances(next_radar, 1, 1):
                    for suspicious_cell in game.grid.get_suspicious_cells():
                        if suspicious_cell.same(cell_to_check):
                            break
                    else:
                        robot.dig(cell_to_check, game.grid, game.enemy_robots, game.traps, "DIFF RADAR")
                        break
                else:
                    robot.wait("GAME OVER")
        elif TRY_TO_BREAK_RADARS and suspected_reachable_radar and not breaking_radar:
            robot.dig(suspected_reachable_radar, game.grid, game.enemy_robots, game.traps, "BREAK", True)
            breaking_radar = True
            if suspected_reachable_radar.distance(robot) <= 1:
                game.grid.get_cell(suspected_reachable_radar.x, suspected_reachable_radar.y).suspicious = False
        elif game.trap_enabled and not game.trap_cooldown and not someone_has_a_trap and robot.x == 0:
            robot.request(TRAP, game.grid, game.enemy_robots, game.traps, "TRAP")
            someone_has_a_trap = True
        elif robot.item == 4:
            robot.go_back_to_base(game.grid, game.enemy_robots, game.traps)

        else:
            # TODO try to avoid digging too close from each other and from suspicious cells
            to_dig = game.to_dig_safe
            # See if we try to test suspicious cells or not
            if not to_dig and game.round > MIN_ROUND_TO_TRY_NOT_SAFE_CELLS and not taking_risk_on_suspicious and not game.enemy_is_trapping:
                to_dig = game.to_dig
                print(f"Passed to non safe digs", file=sys.stderr)
                taking_risk_on_suspicious = True
                game.trying_suspicious_cells.append(robot.id)
            elif robot.id in game.trying_suspicious_cells:
                game.trying_suspicious_cells.remove(robot.id)

            if len(to_dig):
                min_distance_for_radar = 50
                best_cell = to_dig[0]
                to_delete = 0
                for i, cell in enumerate(to_dig):
                    if robot.item != 3 or (robot.item == 3 and cell.amadeusium > 1) and not game.grid.is_destination_dangerous(cell, game.enemy_robots, game.traps):
                        distance = robot.distance(cell) + cell.x
                        if distance < min_distance_for_radar:
                            best_cell = cell
                            min_distance_for_radar = distance
                            to_delete = i
                # Maybe wait one turn to lure enemy into believing it will put a trap
                waiting_to_lure_enemy = False
                if TRY_TO_SIMULATE_TRAPS:
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
                    robot.wait("LURE")
                else:
                    robot.dig(best_cell, game.grid, game.enemy_robots, game.traps, "DIGGING")
            elif someone_has_a_radar and following_radar < MAX_FOLLOWING_RADAR:
                robot.move(next_radar, game.grid, game.enemy_robots, game.traps)
                following_radar += 1
            else:
                # If nothing particular to do, try to advance on the same row at random
                if not game.grid.holes:
                    robot.dig(Pos(STARTING_GUESS_COLUMN, robot.y), game.grid, game.enemy_robots, game.traps, "RANDOM")
                else:
                    for column in range(STARTING_GUESS_COLUMN, width - 1):
                        cell_to_check = game.grid.get_cell(column, min(max(robot.y, 1), 13))
                        for hole in game.grid.holes:
                            if cell_to_check.same(hole):
                                break
                        else:
                            for radar in game.radars:
                                if cell_to_check.distance(radar) <= 4:
                                    break
                            else:
                                robot.dig(cell_to_check, game.grid, game.enemy_robots, game.traps, "RANDOM")
                                break
                    else:
                        robot.wait(f"LOST")