import sys
import math

# Mettre en place un comparatif qui pour le meme prix me donne la recette la moins chere
# Rajouter le calcul des éléments restants
# Evaluer les chances que l'adversaire fasse cette recette ce tour
# tenir à jour le nombre de potions réalisées par l'adversaire (en suivant son score)
# Evaluer l'interet du sort à jouer dans le score final

ACTION_TYPE_BREW = "BREW"
ACTION_TYPE_CAST = "CAST"
ACTION_TYPE_WAIT = "WAIT"


class Game: 
  def __init__(self):
    self.score = 0
    self.inv_0 = 3
    self.inv_1 = 0
    self.inv_2 = 0
    self.inv_3 = 0
    self.brewable_recipes = []

  def reset(self, score, inv_0, inv_1, inv_2, inv_3, recipes, spells):
    self.score = score
    self.inv_0 = inv_0
    self.inv_1 = inv_1
    self.inv_2 = inv_2
    self.inv_3 = inv_3
    self.recipes = recipes
    self.spells = spells
    self.brewable_recipes = []
    self.find_brewable_recipes()

  def find_brewable_recipes(self):
    for recipe in self.recipes:
      if recipe.delta_0 + self.inv_0 >= 0 and recipe.delta_1 + self.inv_1 >= 0 and recipe.delta_2 + self.inv_2 >= 0 and recipe.delta_3 + self.inv_3 >= 0:
        self.brewable_recipes.append(recipe)

  def brew(self, id):
    print(f"{ACTION_TYPE_BREW} {id}")

  def cast(self, id):
    print(f"{ACTION_TYPE_CAST} {id}")

  def wait(self):
    print(f"{ACTION_TYPE_WAIT}")

  def play_best_action(self):
    if len(self.brewable_recipes):
      self.brew(self.brewable_recipes[0].id)
    else:
      self.wait()


class Recipe:
  def __init__(self, id, price, delta_0, delta_1, delta_2, delta_3):
    self.id = id
    self.price = price
    self.delta_0 = delta_0
    self.delta_1 = delta_1
    self.delta_2 = delta_2
    self.delta_3 = delta_3


class Spell:
  def __init__(self, id, delta_0, delta_1, delta_2, delta_3):
    self.id = id
    self.delta_0 = delta_0
    self.delta_1 = delta_1
    self.delta_2 = delta_2
    self.delta_3 = delta_3

# game loop
game = Game()
while True:
  action_count = int(input())  # the number of spells and recipes in play
  recipes = []
  spells = []
  for i in range(action_count):
    # action_id: the unique ID of this spell or recipe
    # action_type: in the first league: BREW; later: CAST, OPPONENT_CAST, LEARN, BREW
    # delta_0: tier-0 ingredient change
    # delta_1: tier-1 ingredient change
    # delta_2: tier-2 ingredient change
    # delta_3: tier-3 ingredient change
    # price: the price in rupees if this is a potion
    # tome_index: in the first two leagues: always 0; later: the index in the tome if this is a tome spell, equal to the read-ahead tax
    # tax_count: in the first two leagues: always 0; later: the amount of taxed tier-0 ingredients you gain from learning this spell
    # castable: in the first league: always 0; later: 1 if this is a castable player spell
    # repeatable: for the first two leagues: always 0; later: 1 if this is a repeatable player spell
    action_id, action_type, delta_0, delta_1, delta_2, delta_3, price, tome_index, tax_count, castable, repeatable = input().split()
    action_id = int(action_id)
    delta_0 = int(delta_0)
    delta_1 = int(delta_1)
    delta_2 = int(delta_2)
    delta_3 = int(delta_3)
    price = int(price)
    tome_index = int(tome_index)
    tax_count = int(tax_count)
    castable = castable != "0"
    repeatable = repeatable != "0"

    if action_type == ACTION_TYPE_BREW:
      recipe = Recipe(action_id, price, delta_0, delta_1, delta_2, delta_3)
      recipes.append(recipe)
    elif action_type == ACTION_TYPE_CAST:
      spell = Spell(action_id, delta_0, delta_1, delta_2, delta_3)
      spells.append(spell)
  for i in range(2):
    # inv_0: tier-0 ingredients in inventory
    # score: amount of rupees
    inv_0, inv_1, inv_2, inv_3, score = [int(j) for j in input().split()]

  game.reset(score, inv_0, inv_1, inv_2, inv_3, recipes, spells)
  game.play_best_action()
