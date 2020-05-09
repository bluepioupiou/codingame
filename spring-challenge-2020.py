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
    TYPE_ROCK = "ROCK"
    TYPE_PAPER = "TYPE_PAPER"
    TYPE_SCISSORS = "SCISSORS"

    def __init__(self, id, x, y, mine, type_id, speed_turns_left, ability_cooldown):
        self.id = id
        self.x = x
        self.y = y
        self.mine = mine
        self.type_id = type_id
        self.speed_turns_left = speed_turns_left
        self.ability_cooldown = ability_cooldown

    def __str__(self):
        return "{0}:{1}".format(self.x, self.y)

    def __eq__(self, other):
        return self.id == other.id

    def isOnTile(self, tile):
        return self.x == tile.x and self.y == tile.y

    def canEat(self, other):
        return (self.type_id == self.TYPE_ROCK and other.type_id == self.TYPE_SCISSORS) or (self.type_id == self.TYPE_PAPER and other.type_id == self.TYPE_ROCK) or (self.type_id == self.TYPE_SCISSORS and other.type_id == self.TYPE_PAPER)


class Tile:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value

    def __str__(self):
        return "({0}:{1})".format(self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rows = [[0] * width for i in range(height)]

    def print(self):
        for row in self.rows:
            print("".join(["X" if car == 10 else "-" if car == 0 else "+" if car == 1 else " "
                           for car in row]), file=sys.stderr)

    def setTile(self, x, y, value):
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

    def findBestPaths(self, pacman):
        path = Path(self.getTile(pacman.x, pacman.y))
        paths = [path]
        self.calculatePossiblePaths(paths, path)
        return paths

    def calculatePossiblePaths(self, paths, path):
        neighbours = self.getNeighbours(path.getLastTile())
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
                    self.calculatePossiblePaths(paths, path)


class Game:
    def __init__(self, width, height):
        self.myPacMen = []
        self.powerPacMen = []
        self.enemyPacMen = []
        self.commands = []
        self.board = Board(width, height)

    def reset(self):
        self.myPacMen = []
        self.powerPacMen = []
        self.enemyPacMen = []
        self.commands = []

    def movePacMen(self):
        for pacMan in self.myPacMen:
            if pacMan not in self.powerPacMen:
                self.addBestMove(pacMan)

    def resolvePowers(self):
        for pacMan in self.myPacMen:
            if not pacMan.ability_cooldown:
                self.speedCommand(pacMan)
                self.powerPacMen.append(pacMan)

    def haveToAvoidTile(self, tile, myPacMan):
        # TODO : ne faire attention que si PacMan dangereux et virer les miens si on traite les changements de board
        for pacMan in self.enemyPacMen + self.myPacMen:
            if myPacMan == pacMan:
                return False
            if pacMan.isOnTile(tile):
                if pacMan.mine:
                    return True

                if myPacMan.canEat(pacMan):
                    print("{0} can eat {1}".format(
                        myPacMan.id, pacMan.id), file=sys.stderr)
                    return False
                return True

            if pacMan.mine:
                return False

            neightbours = self.board.getNeighbours(tile)
            for neightbour in neightbours:
                if pacMan.isOnTile(neightbour):
                    if myPacMan.canEat(pacMan):
                        print("{0} could eat {1}".format(
                            myPacMan.id, pacMan.id), file=sys.stderr)
                        return False

                    if pacMan.canEat(myPacMan):
                        print("{0} could be eaten by {1}".format(
                            myPacMan.id, pacMan.id), file=sys.stderr)
                        return True

                    return False
        return False

    def addBestMove(self, pacman):
        paths = self.board.findBestPaths(pacman)
        # Vire les chemins ou on rencontre un autre pacman
        paths = list(
            filter(lambda path: len(path.tiles) == len(list(filter(lambda tile: not self.haveToAvoidTile(tile, pacman), path.tiles))), paths))

        paths.sort(key=lambda x: x.value, reverse=True)
        sameValuePaths = list(
            filter(lambda path: path.value == paths[0].value, paths))
        # print("{0} chemins avec la valeur {1}".format(
        #    len(sameValuePaths), paths[0].value), file=sys.stderr)
        sameValuePaths.sort(key=lambda x: len(x.tiles))
        beginWithPelletPaths = list(
            filter(lambda path: not path.tiles[1].value == 0, paths))
        chosenPath = None
        if len(beginWithPelletPaths):
            chosenPath = beginWithPelletPaths[0]
            message = "Meilleur chemin, valeur {0}, destination {1}".format(
                chosenPath.value, chosenPath.tiles[-1])
        elif len(sameValuePaths):
            chosenPath = sameValuePaths[0]
            message = "Alternative, valeur {0}, destination {1}".format(
                chosenPath.value, chosenPath.tiles[-1])

        # Si le chemin ne rencontre aucune pellet, trouve la plus proche
        if not chosenPath or not chosenPath.value:
            nextTile = self.board.findClosestPellet(pacman)
            message = "Je trouve rien, je vais au plus proche"
        else:
            if pacman.speed_turns_left and len(chosenPath.tiles) > 2:
                nextTile = chosenPath.tiles[2]
            else:
                nextTile = chosenPath.tiles[1]

        self.board.setTile(nextTile.x, nextTile.y, 0)
        self.moveCommand(pacman, nextTile, message)

    def moveCommand(self, pacman, tile, message):
        self.addCommand(("MOVE {0} {1} {2} {3}".format(
            pacman.id, tile.x, tile.y, message)))

    def speedCommand(self, pacman):
        self.addCommand(("SPEED {0}".format(pacman.id)))

    def addCommand(self, command):
        self.commands.append(command)

    def printCommands(self):
        print("|".join(self.commands))


# width: size of the grid
# height: top left corner is (x=0, y=0)
width, height = [int(i) for i in input().split()]

game = Game(width, height)

for i in range(height):
    row = input()  # one line of the grid: space " " is floor, pound "#" is wall
    for j, value in enumerate(row):
        game.board.setTile(j, i, value if value == "#" else 1)

# game loop
while True:
    game.reset()
    my_score, opponent_score = [int(i) for i in input().split()]
    visible_pac_count = int(input())  # all your pacs and enemy pacs in sight
    for i in range(visible_pac_count):
        pac_id, mine, x, y, type_id, speed_turns_left, ability_cooldown = input().split()
        pac_id = int(pac_id)
        mine = mine != "0"
        x = int(x)
        y = int(y)
        speed_turns_left = int(speed_turns_left)
        ability_cooldown = int(ability_cooldown)

        pacman = PacMan(pac_id, x, y, mine, type_id,
                        speed_turns_left, ability_cooldown)
        # TODO améliorer la MAJ de la board, ça marche pas
        game.board.setTile(x, y, 0)
        if mine:
            game.myPacMen.append(pacman)
        else:
            game.enemyPacMen.append(pacman)

    visible_pellet_count = int(input())  # all pellets in sight
    for i in range(visible_pellet_count):

        x, y, value = [int(j) for j in input().split()]
        game.board.setTile(x, y, value)
    # game.board.print()

    game.resolvePowers()
    game.movePacMen()

    game.printCommands()
