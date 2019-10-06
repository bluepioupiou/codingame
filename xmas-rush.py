import sys
import math
import copy
import time
from random import randint

# Help the Christmas elves fetch presents in a magical labyrinth!
TURN_TYPE_PUSH = 0
TURN_TYPE_MOVE = 1

MY_PLAYER_ID = 0
OPPONENT_PLAYER_ID = 1

BOARD_WIDTH = 7

DIRECTIONS = ['UP', 'RIGHT', 'DOWN', 'LEFT']

DIRECTION_MODIFIERS = [
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 0)
]

FROM_DIR_TO_MODIFIER = list(zip(DIRECTIONS, DIRECTION_MODIFIERS))
FROM_MODIFIER_TO_DIR = dict(zip(DIRECTION_MODIFIERS, DIRECTIONS))


def getDirectionDistance(source, target):
    return (source.x - target.x, source.y - target.y)


def getAbsoluteDistance(source, target):
    direction = getDirectionDistance(source, target)
    return abs(direction[0]) + abs(direction[1])


class Item:
    def __init__(self, item_name, item_x, item_y, item_player_id):
        self.name = item_name
        self.x = item_x
        self.y = item_y
        self.player = item_player_id

    def __str__(self):
        return "{0}:{1}".format(self.x, self.y)


class Player:

    def __init__(self, num_player_cards, player_x, player_y, player_tile):
        self.cards = num_player_cards
        self.x = player_x
        self.y = player_y
        self.tile = Tile(-1, -1, player_tile)
        self.items = []
        self.quests = []
        self.prior_items = []

    def __str__(self):
        return ('{0}:{1}').format(self.x, self.y)

    def add_item(self, item):
        self.items.append(item)

    def add_quest(self, quest):
        self.quests.append(quest)

    def getBestPath(self, board):
        startingTile = board.getTile(self.x, self.y)
        # print("Starting:" + str(startingTile), file=sys.stderr)
        path = Path(0, startingTile, self.prior_items)
        paths = [path]
        self.calculatePaths(board, path, paths)
        # Find best path between all this paths
        # for path in paths:
        # print("- path {0} len {1} closest {2} at distance {3}".format(path, path.length, path.closest, path.min_distance), file=sys.stderr)
        paths.sort(key=lambda x: x.min_distance, reverse=False)
        return paths[0]

    def calculatePaths(self, board, path, paths):
        exits = path.tiles[-1].getExits(path, board)
        path_to_copy = copy.deepcopy(path)
        for i, exit in enumerate(exits):
            if i > 0:
                # print("- fork path {0} for exit {1}".format(str(path.position), exit), file=sys.stderr)
                path = copy.deepcopy(path_to_copy)
                path.position = len(paths)
                paths.append(path)
            #print("Add exit {0} to path {1}".format(exit,path), file=sys.stderr)
            path.addTile(exit)
            self.calculatePaths(board, path, paths)


class Path:

    def __init__(self, position, startingTile, target_items):
        self.tiles = []
        self.directions = []
        self.length = 0
        self.closest = 0
        self.min_distance = 14
        for item in target_items:
            distance = getAbsoluteDistance(startingTile, item)
            if distance < self.min_distance:
                self.min_distance = distance
        #print("calculating fist tile distance {0}".format(self.min_distance), file=sys.stderr)

        self.target_items = target_items
        self.tiles.append(startingTile)
        self.length = 1
        self.position = position

    def __str__(self):
        return "{0} : {1}".format(str(self.position), '-'.join(self.directions))

    def addTile(self, tile):
        self.directions.append(tile.direction)

        for item in self.target_items:
            distance = getAbsoluteDistance(tile, item)
            if 1 < distance < self.min_distance:
                self.min_distance = distance
                self.closest = len(self.tiles)
                #print("found closest tile number {0}".format(self.closest), file=sys.stderr)

        self.tiles.append(tile)
        self.length += 1


class Board:

    def __init__(self):
        self.rows = [[0] * BOARD_WIDTH for i in range(BOARD_WIDTH)]

    def getVisualRows(self):
        result = []
        for row in self.rows:
            result.append(' '.join([tile.path for tile in row]))
        return result

    def setTile(self, x, y, tile):
        tile = Tile(x, y, tile)
        self.rows[y][x] = tile

    def getTile(self, x, y):
        if 0 <= x <= 6 and 0 <= y <= 6:
            return self.rows[y][x]
        else:
            return None

    def simulateWithPush(self, number, direction, player):
        new_board = copy.deepcopy(self)
        new_player = copy.deepcopy(player)
        if direction == "LEFT" or direction == "RIGHT":
            row = new_board.rows[number]
            if direction == "RIGHT":
                row.insert(0, new_player.tile)
                row.pop()
                if new_player.y == number:
                    new_player.x += 1
                    if new_player.x == BOARD_WIDTH:
                        new_player.x = 0
                for item in new_player.items:
                    if item.y == number:
                        item.x += 1
                        if item.x == BOARD_WIDTH:
                            item.x = -1
                            item.y = -1
                    # Means the item was on the pushed tile
                    if item.y == -1:
                        item.x = 0
                        item.y = number
            elif direction == "LEFT":
                row.append(new_player.tile)
                row.pop(0)
                if new_player.y == number:
                    new_player.x -= 1
                    if new_player.x == -1:
                        new_player.x = BOARD_WIDTH - 1
                for item in new_player.items:
                    if item.y == number:
                        item.x -= 1
                        if item.x == -1:
                            item.y = -1
                    # Means the item was on the pushed tile
                    if item.y == -1:
                        item.x = BOARD_WIDTH - 1
                        item.y = number
        else:
            if direction == "DOWN":
                for i, row in enumerate(new_board.rows):
                    if i == 0:
                        previous_tile = row[number]
                        row[number] = new_player.tile
                    else:
                        actual_tile = row[number]
                        row[number] = previous_tile
                        previous_tile = actual_tile
                if new_player.x == number:
                    new_player.y += 1
                    if new_player.y == BOARD_WIDTH:
                        new_player.y = 0
                for item in new_player.items:
                    if item.x == number:
                        item.y += 1
                        # Item out of board
                        if item.y == BOARD_WIDTH:
                            item.y = -1
                            item.x = -1
                    # Means the item was on the pushed tile
                    if item.x == -1:
                        item.x = number
                        item.y = 0
            else:
                for i, row in enumerate(reversed(new_board.rows)):
                    if i == 0:
                        previous_tile = row[number]
                        row[number] = new_player.tile
                    else:
                        actual_tile = row[number]
                        row[number] = previous_tile
                        previous_tile = actual_tile
                if new_player.x == number:
                    new_player.y -= 1
                    if new_player.y == -1:
                        new_player.y = BOARD_WIDTH - 1
                for item in new_player.items:
                    if item.x == number:
                        item.y -= 1
                        # Item out of board
                        if item.y == -1:
                            item.x = -1
                    # Means the item was on the pushed tile
                    if item.x == -1:
                        item.x = number
                        item.y = BOARD_WIDTH - 1
        # recalculate coordinates of tiles after move
        for y, row in enumerate(new_board.rows):
            for x, tile in enumerate(row):
                tile.x = x
                tile.y = y
        return new_board, new_player


class Tile:
    def __init__(self, x, y, path):
        self.path = path
        self.x = x
        self.y = y
        self.direction = None

    def __str__(self):
        return ('{0}:{1}').format(self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def getExits(self, path, board):
        exits = []
        for num, is_open in enumerate(self.path):
            nextTile = board.getTile(self.x + DIRECTION_MODIFIERS[num][0], self.y + DIRECTION_MODIFIERS[num][1])
            if is_open == "1" and nextTile and nextTile.path[(num + 2) % 4] == "1":
                if nextTile not in path.tiles:
                    nextTile.direction = DIRECTIONS[num]
                    exits.append(nextTile)
        return exits


# game loop
while True:
    original_board = Board()
    turn_type = int(input())
    for y in range(7):
        tiles = input().split()
        for x, tile in enumerate(tiles):
            original_board.setTile(x, y, tile)

    for i in range(2):
        # num_player_cards: the total number of quests for a player (hidden and revealed)
        num_player_cards, player_x, player_y, player_tile = input().split()
        num_player_cards = int(num_player_cards)
        player_x = int(player_x)
        player_y = int(player_y)
        if i == MY_PLAYER_ID:
            my_player = Player(num_player_cards, player_x, player_y, player_tile)
        else:
            opponent_player = Player(num_player_cards, player_x, player_y, player_tile)

    num_items = int(input())  # the total number of items available on board and on player tiles
    for i in range(num_items):
        item_name, item_x, item_y, item_player_id = input().split()
        item_x = int(item_x)
        item_y = int(item_y)
        item_player_id = int(item_player_id)
        item = Item(
            item_name,
            item_x,
            item_y,
            item_player_id
        )
        if item_player_id == MY_PLAYER_ID:
            my_player.add_item(item)
        else:
            opponent_player.add_item(item)

    num_quests = int(input())  # the total number of revealed quests for both players
    for i in range(num_quests):
        quest_item_name, quest_player_id = input().split()
        quest_player_id = int(quest_player_id)
        if quest_player_id == MY_PLAYER_ID:
            my_player.add_quest(quest_item_name)
        else:
            opponent_player.add_quest(quest_item_name)

    my_player.prior_items = list(filter(lambda item: item.name in my_player.quests, my_player.items))
     # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)

    # PUSH <id> <direction> | MOVE <direction> | PASS
    if turn_type == TURN_TYPE_PUSH:

        start = time.time()
        possibilities = []
        prior_possibilities = []
        for direction in DIRECTIONS:
            for number in range(7):
                # Priorise the row and col with my player or my item
                if direction in ['LEFT', 'RIGHT'] and number in [item.y for item in my_player.prior_items] + [my_player.y]:
                    prior_possibilities.append((number, direction))
                elif direction in ['DOWN', 'UP'] and number in [item.x for item in my_player.prior_items] + [my_player.x]:
                    prior_possibilities.append((number, direction))
                else:
                    possibilities.append((number, direction))

        best_possibility = None
        best_possibility_distance = 14

        while possibilities and (time.time() - start < 0.04):
            if prior_possibilities:
                new_possibility = prior_possibilities.pop()
            else:
                random = randint(0, len(possibilities) - 1)
                new_possibility = possibilities.pop(random)
            new_board, new_player = original_board.simulateWithPush(
                new_possibility[0],
                new_possibility[1],
                my_player
            )
            path = new_player.getBestPath(new_board)
            if path.min_distance < best_possibility_distance:
                best_possibility_distance = path.min_distance
                best_possibility = new_possibility
            #print('if {0}, player {1} item {2} path {3} min distance {4}'.format(new_possibility, new_player, new_player.items[0], path.directions, path.min_distance), file=sys.stderr)
            #for visualRow in new_board.getVisualRows():
            #    print(visualRow, file=sys.stderr)

        print("best bet {0} for distance {1} ({2} simulated)".format(
            best_possibility, best_possibility_distance, 28 - len(possibilities)),
            file=sys.stderr
        )
        if best_possibility_distance == 0:
            print("PUSH {0} {1}".format(best_possibility[0], best_possibility[1]))
        else:
            found = False
            number = None
            direction = None
            for item in my_player.prior_items:
                if item.x == 0:
                    found = True
                    number = item.y
                    direction = "LEFT"
                    break
                elif item.x == 6:
                    found = True
                    number = item.y
                    direction = "RIGHT"
                    break
                elif item.y == 0:
                    found = True
                    number = item.x
                    direction = "UP"
                    break
                elif item.y == 6:
                    found = True
                    number = item.x
                    direction = "DOWN"
                    break

            if found:
                print("found at border and no direct hit", file=sys.stderr)
                print("PUSH {0} {1}".format(str(number), direction))
            else:
                print("PUSH {0} {1}".format(best_possibility[0], best_possibility[1]))
    else:
        path = my_player.getBestPath(original_board)
        print("now best {0} for distance {1}".format(
            path, path.closest),
            file=sys.stderr
        )

        if path.directions and path.closest > 0:
            print("MOVE {0}".format(' '.join(path.directions[0:path.closest])))
        else:
            print("PASS")