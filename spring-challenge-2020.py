import sys
import math
import copy

NEIGHBOURS_DIRECTIONS = [[-1, 0], [1, 0], [0, -1], [0, 1]]
MAX_PATH_LENGTH = 10


class Path:
    def __init__(self, tile):
        self.tiles = [tile]
        self.value = 0

    def __str__(self):
        formatedList = ["({0},{1})".format(str(tile.x), str(tile.y))
                        for tile in self.tiles]
        return "{0} {1}".format(",".join(formatedList), self.value)

    def addTile(self, tile):
        self.tiles.append(tile)
        self.value += int(tile.value)

    def getLastTile(self):
        return self.tiles[-1]


class PacMan:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y

    def __str__(self):
        return "{0}:{1}".format(self.x, self.y)

    def getBestMove(self, board):
        bestPath = self.findBestPath(board)
        nextTile = bestPath.tiles[1]
        if not bestPath.value:
            nextTile = board.findClosestPellet(self)
        board.setTile(nextTile.x, nextTile.y, 0)
        return self.getMove(nextTile.x, nextTile.y)

    def getMove(self, x, y):
        return "MOVE {0} {1} {2}".format(self.id, x, y)

    def findBestPath(self, board):
        path = Path(board.getTile(self.x, self.y))
        paths = [path]
        self.calculatePossiblePaths(paths, path, board)
        for path in paths:
            print(path, file=sys.stderr)
        paths.sort(key=lambda x: x.value, reverse=True)
        sameValuePaths = list(
            filter(lambda path: path.value == paths[0].value, paths))
        print("{0} chemins avec la valeur {1}".format(
            len(sameValuePaths), paths[0].value), file=sys.stderr)
        sameValuePaths.sort(key=lambda x: len(x.tiles))
        chosenPath = sameValuePaths[0]
        return chosenPath

    def calculatePossiblePaths(self, paths, path, board):
        neighbours = board.getNeighbours(path.getLastTile())
        # print("tile {0} {1} with {2} neighbours : {3}".format(
        #    path.getLastTile().x, path.getLastTile().y, len(neighbours), ",".join(["({0},{1}-{2})".format(str(tile.x), str(tile.y), str(tile.value)) for tile in neighbours])), file=sys.stderr)
        path_to_copy = copy.deepcopy(path)
        i = 0
        for neighbour in neighbours:
            if not neighbour in path.tiles:
                i += 1
                if i > 1:
                    path = copy.deepcopy(path_to_copy)
                    paths.append(path)
                path.addTile(neighbour)
                if not len(path.tiles) >= MAX_PATH_LENGTH:
                    self.calculatePossiblePaths(paths, path, board)


class Tile:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rows = [[0] * width for i in range(height)]

    def reset(self):
        for y, row in enumerate(self.rows):
            for x, tileValue in enumerate(row):
                if not tileValue == "#":
                    self.setTile(x, y, 0)

    def __str__(self):
        for row in self.rows:
            print("".join([str(car) for car in row]), file=sys.stderr)

    def setTile(self, x, y, value):
        # print("width {0} height {1}".format(
        #    self.width, self.height), file=sys.stderr)
        # print("set tile {0} {1}".format(x, y), file=sys.stderr)
        self.rows[y][x] = value

    def getTile(self, x, y):
        return Tile(x, y, self.rows[y][x])

    def getNeighbours(self, tile):
        neighbours = []
        for neighbour in NEIGHBOURS_DIRECTIONS:
            new_x = tile.x + neighbour[0]
            new_y = tile.y + neighbour[1]
            if new_x == self.width:
                new_x = 0
            elif new_x < 0:
                new_x = self.width - 1
            if new_y == self.height:
                new_y = 0
            elif new_y < 0:
                new_y = self.height - 1
            new_tile = self.getTile(new_x, new_y)
            if not new_tile.value == "#":
                neighbours.append(new_tile)
        return neighbours

    def findClosestPellet(self, pacman):
        nearest = 50
        best_tile = self.getTile(0, 0)
        for y, row in enumerate(self.rows):
            for x, tileValue in enumerate(row):
                distance = abs(pacman.x-x) + abs(pacman.y-y)
                if distance < nearest and not tileValue == "#" and not tileValue == 0:
                    nearest = distance
                    best_tile = self.getTile(x, y)
        return best_tile


class Game:
    def __init__(self):
        self.myPacMen = []
        self.enemyPacMen = []
        self.commands = []

    def reset(self):
        self.myPacMen = []
        self.enemyPacMen = []
        self.commands = []

    def add_command(self, command):
        print(command, file=sys.stderr)
        self.commands.append(command)

    def play(self):
        print("|".join(self.commands))


game = Game()

# width: size of the grid
# height: top left corner is (x=0, y=0)
width, height = [int(i) for i in input().split()]
board = Board(width, height)
for i in range(height):
    row = input()  # one line of the grid: space " " is floor, pound "#" is wall
    for j, value in enumerate(row):
        board.setTile(j, i, value if value == "#" else 0)

# game loop
while True:
    game.reset()
    my_score, opponent_score = [int(i) for i in input().split()]
    visible_pac_count = int(input())  # all your pacs and enemy pacs in sight
    for i in range(visible_pac_count):
        # pac_id: pac number (unique within a team)
        # mine: true if this pac is yours
        # x: position in the grid
        # y: position in the grid
        # type_id: unused in wood leagues
        # speed_turns_left: unused in wood leagues
        # ability_cooldown: unused in wood leagues
        pac_id, mine, x, y, type_id, speed_turns_left, ability_cooldown = input().split()
        pac_id = int(pac_id)
        mine = mine != "0"
        x = int(x)
        y = int(y)
        speed_turns_left = int(speed_turns_left)
        ability_cooldown = int(ability_cooldown)

        pacman = PacMan(pac_id, x, y)

        if mine:
            game.myPacMen.append(pacman)
        else:
            game.enemyPacMen.append(pacman)

    board.reset()

    visible_pellet_count = int(input())  # all pellets in sight
    for i in range(visible_pellet_count):
        # value: amount of points this pellet is worth
        x, y, value = [int(j) for j in input().split()]
        board.setTile(x, y, value)
    # print(board)
    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)
    # MOVE <pacId> <x> <y>
    for pacman in game.myPacMen:
        game.add_command(pacman.getBestMove(board))
    game.play()
