import sys
import math
import copy
from typing import List

NEIGHBOURS_DIRECTIONS = [[-1, 0], [1, 0], [0, -1], [0, 1]]
STARTING_MAX_PATH_LENGTH = 12
MAX_PATH_LENGTH = 12

DISTANCE_WEIGHT = 0.91
FRIEND_PACMAN_VALUE = 10
BLOCKED_PATH_VALUE = 50
SAFE_ENEMY_VALUE = 20
DANGEROUS_ENEMY_VALUE = 20
ENEMY_VALUE = 10
UNKNOWN_PELLET_VALUE = 0.5


def print_console(message):
    print(message, file=sys.stderr)


class Tile:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value

    def __str__(self):
        return "({0}:{1})".format(self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Pacman:
    TYPE_ROCK = "ROCK"
    TYPE_PAPER = "PAPER"
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

    def getDistanceFrom(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    def getCanEat(self):
        if self.type_id == self.TYPE_PAPER:
            return self.TYPE_SCISSORS
        elif self.type_id == self.TYPE_ROCK:
            return self.TYPE_PAPER
        else:
            return self.TYPE_ROCK

    def canEat(self, other):
        return (self.type_id == self.TYPE_ROCK and other.type_id == self.TYPE_SCISSORS) or (self.type_id == self.TYPE_PAPER and other.type_id == self.TYPE_ROCK) or (self.type_id == self.TYPE_SCISSORS and other.type_id == self.TYPE_PAPER)


class Path:
    def __init__(self, tile):
        self.tiles = [tile]
        self.value = float(0)
        self.encounters = []
        self.haveToTurnInto = None

    def addTile(self, tile: Tile):
        self.value += float(tile.value * DISTANCE_WEIGHT ** len(self.tiles))

        if(tile.value == 10):
            self.encounters.append("X")
        self.tiles.append(tile)

    def calculateWeight(self, board, myPacman: Pacman, pacmen: List[Pacman]):
        for number, tile in enumerate(self.tiles[1:]):
            if tile.value < 0:  # Une tuile interdite car un autre ami y passe et atteignable
                if myPacman.speed_turns_left > 0 and number == 1 or number == 0:
                    self.value -= float(BLOCKED_PATH_VALUE * (DISTANCE_WEIGHT ** len(
                        self.tiles)))
                    self.encounters.append("B")
                    break
            else:
                for pacman in pacmen:
                    # Un des miens est sur le chemin direct
                    if pacman.mine:
                        if pacman.isOnTile(tile):
                            self.value -= float(FRIEND_PACMAN_VALUE * (DISTANCE_WEIGHT ** len(
                                self.tiles)))
                            self.encounters.append("F")
                    else:  # un ennemi
                        neightbours = board.getNeighbours(tile)
                        for i, inspectTile in enumerate([tile] + neightbours):
                            # Ca ne sert a rien de regarder les cases voisines qui sont une case du path
                            if pacman.isOnTile(tile) and (i == 0 or not inspectTile in self.tiles):
                                distance = myPacman.getDistanceFrom(pacman)
                                enemy_speed = 1
                                if pacman.speed_turns_left:
                                    enemy_speed = 2
                                if myPacman.canEat(pacman):  # je peux le manger
                                    if pacman.ability_cooldown:  # Il n'a pas encore son pouvoir
                                        self.value += float(SAFE_ENEMY_VALUE * (DISTANCE_WEIGHT ** len(
                                            self.tiles))) / 1 if i == 0 else 2
                                    else:  # Il a son pouvoir # TODO : à ponderer
                                        self.value -= float(DANGEROUS_ENEMY_VALUE * (DISTANCE_WEIGHT ** len(
                                            self.tiles))) / 1 if i == 0 else 2
                                    self.encounters.append("S")
                                elif pacman.canEat(myPacman):  # il peut me manger
                                    if myPacman.ability_cooldown > 0:  # Je n'ai pas encore mon pouvoir # TODO à ponderer
                                        self.value -= float(DANGEROUS_ENEMY_VALUE * (DISTANCE_WEIGHT ** len(
                                            self.tiles))) / 1 if i == 0 else 2
                                    else:  # J'ai mon pouvoir je considere que je vais pouvoir le manger ou fuir apres
                                        if distance - enemy_speed > 1:  # On ne peut pas se manger
                                            self.value += float(SAFE_ENEMY_VALUE * (DISTANCE_WEIGHT ** len(
                                                self.tiles))) / 1 if i == 0 else 2
                                        elif distance - enemy_speed <= 1:  # Il peut arriver juste à côté ou me manger à ce tour si je ne bouge pas -- hop je change de type
                                            self.value += float(SAFE_ENEMY_VALUE * (DISTANCE_WEIGHT ** len(
                                                self.tiles)))
                                            self.haveToTurnInto = pacman.getCanEat()
                                    self.encounters.append("D")
                                else:  # Il est comme moi
                                    if myPacman.ability_cooldown > 0:  # Je n'ai pas encore mon pouvoir # TODO à ponderer
                                        self.value -= float(ENEMY_VALUE * (DISTANCE_WEIGHT **
                                                                           len(self.tiles))) / 1 if i == 0 else 2
                                    else:  # J'ai mon pouvoir je considere que je vais pouvoir le manger ou fuir apres
                                        if distance - enemy_speed > 1:  # On ne peut pas se manger
                                            self.value += float(SAFE_ENEMY_VALUE * (DISTANCE_WEIGHT ** len(
                                                self.tiles))) / 1 if i == 0 else 2
                                        elif distance - enemy_speed <= 1:  # Il peut arriver juste à côté ou me manger à ce tour si je ne bouge pas -- hop je change de type
                                            self.value += float(SAFE_ENEMY_VALUE * (DISTANCE_WEIGHT ** len(
                                                self.tiles)))
                                            self.haveToTurnInto = pacman.getCanEat()
                                    self.encounters.append("E")

    def getLastTile(self):
        return self.tiles[-1]

    def getDirections(self):
        directions = []
        for i, tile in enumerate(self.tiles[1:]):
            difference = [tile.x - self.tiles[i].x, tile.y - self.tiles[i].y]
            if difference == [-1, 0]:
                directions.append("◄")
            elif difference == [1, 0]:
                directions.append("►")
            elif difference == [0, -1]:
                directions.append("▲")
            elif difference == [0, 1]:
                directions.append("▼")
        return "".join(directions)

    def print(self):
        print(" - {0:.2f}:{1} ({2}) {3}".format(self.value, self.getDirections(),
                                                "".join(self.encounters), self.haveToTurnInto), file=sys.stderr)


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rows = [[UNKNOWN_PELLET_VALUE] * width for i in range(height)]

    def print(self):
        for row in self.rows:
            print("".join(["X" if car == 10 else "-" if car == 0 else "+" if car == 1 else " "
                           for car in row]), file=sys.stderr)

    def printNumberOfPellets(self):
        total = 0
        for row in self.rows:
            for car in row:
                if not car == "#":
                    total += 1 if float(car) > 0 else 0
        print_console(total)

    def applyPath(self, path):
        for i, tile in enumerate(path.tiles):
            self.setTile(tile.x, tile.y, 0 if i > 1 else -1)

    def resetXPellets(self):
        for y, row in enumerate(self.rows):
            for x, tileValue in enumerate(row):
                if tileValue == 10:
                    self.setTile(x, y, 0)

    def setTile(self, x, y, value):
        self.rows[y][x] = value

    def getTile(self, x, y):
        return Tile(x, y, self.rows[y][x])

    def getNeighboursTile(self, tile, neighbour):
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
        return new_tile

    def getNeighbours(self, tile):
        neighbours = []
        for neighbour in NEIGHBOURS_DIRECTIONS:
            new_tile = self.getNeighboursTile(tile, neighbour)
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

    def findPossiblePaths(self, pacman):
        path = Path(self.getTile(pacman.x, pacman.y))
        paths = [path]
        self.followPossiblePaths(paths, path)
        return paths

    def followPossiblePaths(self, paths, path):
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
                    self.followPossiblePaths(paths, path)


class Game:
    def __init__(self, width, height):
        self.myPacMen = []
        self.enemyPacMen = []
        self.commands = []
        self.board = Board(width, height)
        self.simulatedBoard = None

    def reset(self):
        self.myPacMen = []
        self.enemyPacMen = []
        self.commands = []
        self.board.resetXPellets()

    def updateBoard(self, visible_pellets):
        positions = []
        removed = []

        for (x, y, value) in visible_pellets:  # Mets à jour la map
            game.board.setTile(x, y, value)
            positions.append((x, y))
        for pacman in self.myPacMen:  # Vire les pastilles que le pacman devrait voir mais qui ne sont pas dans les visibles
            for neighbour in NEIGHBOURS_DIRECTIONS:
                new_tile = self.board.getNeighboursTile(pacman, neighbour)
                while new_tile.value != "#":
                    # Tile que l'on voit pas dans les pastilles visible, donc = 0
                    if not (new_tile.x, new_tile.y) in positions:
                        self.board.setTile(new_tile.x, new_tile.y, 0)
                        removed.append((new_tile.x, new_tile.y))
                    new_tile = self.board.getNeighboursTile(
                        new_tile, neighbour)

    def movePacMen(self):
        self.simulatedBoard = copy.deepcopy(self.board)
        for pacman in self.myPacMen:
            self.addBestMove(pacman)

    def addBestMove(self, pacman):
        print_console(pacman.id)
        paths = self.simulatedBoard.findPossiblePaths(pacman)

        # Ajoute les poids pour chaque chemin
        for path in paths:
            path.calculateWeight(self.board, pacman,
                                 self.myPacMen + self.enemyPacMen)
        # Trie les chemins par valeur décroissante
        paths.sort(key=lambda x: x.value, reverse=True)
        # Ne garde que les chemins avec valeur > 0
        paths = list(filter(lambda path: path.value > float(0), paths))
        for path in paths:
            path.print()

        encounter_enemy = False
        if len(paths) > 0:
            chosenPath = paths[0]
            self.simulatedBoard.applyPath(chosenPath)
            if pacman.speed_turns_left and len(chosenPath.tiles) > 2:
                self.board.setTile(
                    chosenPath.tiles[1].x, chosenPath.tiles[1].y, 0)
                nextTile = chosenPath.tiles[2]
            else:
                nextTile = chosenPath.tiles[1]
            if "X" in chosenPath.encounters:
                message = "MAAAM"
            elif "S" in chosenPath.encounters:
                encounter_enemy = True
                message = "Gotcha!"
            elif "D" in chosenPath.encounters:
                encounter_enemy = True
                message = "Aaahhhh"
            elif "F" in chosenPath.encounters:
                message = "Hello Friend"
            elif "B" in chosenPath.encounters:
                message = "Blocked!"
            elif "E" in chosenPath.encounters:
                encounter_enemy = True
                message = "Ho, Hi"
            else:
                message = "Nom!"
        else:
            nextTile = self.board.findClosestPellet(pacman)
            message = "Lost :'("

        if encounter_enemy:
            if chosenPath.haveToTurnInto:
                self.switchCommand(pacman, chosenPath.haveToTurnInto)
            else:
                self.moveCommand(pacman, nextTile, message)
        else:
            if not pacman.ability_cooldown:
                self.speedCommand(pacman)
            else:
                self.moveCommand(pacman, nextTile, message)

    def moveCommand(self, pacman, tile, message):
        self.board.setTile(tile.x, tile.y, 0)
        self.addCommand("MOVE {0} {1} {2} {3}".format(
            pacman.id, tile.x, tile.y, message))

    def speedCommand(self, pacman):
        self.addCommand(("SPEED {0} Zooooom".format(pacman.id)))

    def switchCommand(self, pacman, into):
        self.addCommand(("SWITCH {0} {1} Suprise!".format(pacman.id, into)))

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
        game.board.setTile(j, i, value if value ==
                           "#" else UNKNOWN_PELLET_VALUE)

# game loop
while True:
    my_score, opponent_score = [int(i) for i in input().split()]
    visible_pac_count = int(input())  # all your pacs and enemy pacs in sight
    game.reset()
    for i in range(visible_pac_count):
        pac_id, mine, x, y, type_id, speed_turns_left, ability_cooldown = input().split()
        pac_id = int(pac_id)
        mine = mine != "0"
        x = int(x)
        y = int(y)
        speed_turns_left = int(speed_turns_left)
        ability_cooldown = int(ability_cooldown)

        pacman = Pacman(pac_id, x, y, mine, type_id,
                        speed_turns_left, ability_cooldown)
        # TODO améliorer la MAJ de la board, ça marche pas
        # TODO initialiser la board autrement
        game.board.setTile(x, y, 0)
        if mine:
            game.myPacMen.append(pacman)
        else:
            game.enemyPacMen.append(pacman)

    # Mets à jour le nombre de tuiles max a inspecter pour des raisons de timing
    MAX_PATH_LENGTH = STARTING_MAX_PATH_LENGTH - len(game.myPacMen)

    visible_pellet_count = int(input())  # all pellets in sight
    visible_pellets = []
    for i in range(visible_pellet_count):
        x, y, value = [int(j) for j in input().split()]
        visible_pellets.append((x, y, value))
    game.updateBoard(visible_pellets)
    # game.board.print()
    game.movePacMen()
    game.printCommands()

# TODO : calculer ou j'en suis du temps et l'utiliser au mieux
# TODO : prendre en compte les pac morts
