import sys
import math
import copy
from collections import deque, Counter
import time

# Rajouter le calcul des éléments restants
# Evaluer les chances que l'adversaire fasse cette recette ce tour
# tenir à jour le nombre de potions réalisées par l'adversaire (en suivant son score)
# Evaluer l'interet du sort à jouer dans le score final

# 

ACTION_TYPE_LEARN = "LEARN"
ACTION_TYPE_BREW = "BREW"
ACTION_TYPE_CAST = "CAST"
ACTION_TYPE_WAIT = "WAIT"
ACTION_TYPE_REST = "REST"
ACTION_TYPE_OPPONENT_CAST = "OPPONENT_CAST"

LVL_0_VALUE = 1
LVL_1_VALUE = 2
LVL_2_VALUE = 3
LVL_3_VALUE = 4

MAX_NUMBER_OF_STEPS_FOR_VISION = 5
TIME_TO_PASS_SEARCHING_VISIONS = 0.035

def print_console(message):
    print(message, file=sys.stderr, flush=True)

class Game: 
  def __init__(self):
    self.score = 0
    self.recipes = []
    self.spells = []
    self.brewable_recipes = []
    self.castable_spells = []

  def __str__(self):
    return "game:[{},{},{},{}]".format(self.inv_0, self.inv_1, self.inv_2, self.inv_3)

  def reset(self, my_score, my_stock, recipes, spells, tomes):
    self.start = time.time()
    self.my_score = my_score
    self.my_stock = my_stock
    self.recipes = recipes
    self.spells = spells
    self.spells_dict = {}
    for spell in spells:
      self.spells_dict[spell.id] = spell
    self.tomes = tomes
    self.recipes.sort(key=lambda recipe: recipe.value, reverse=True)
    self.brewable_recipes = [recipe for recipe in self.recipes if  self.my_stock.can_brew(recipe)]
    self.castable_spells = [spell for spell in self.spells if  self.my_stock.can_cast(spell)]
    self.pure_tomes = [tome for tome in self.tomes if tome.pure]
    self.learnable_pure_tomes = [tome for tome in self.pure_tomes if  self.my_stock.can_learn(tome)]

  def brew(self, recipe):
    print(f"{ACTION_TYPE_BREW} {recipe.id}")

  def cast(self, spell):
    print(f"{ACTION_TYPE_CAST} {spell.id}")

  def learn(self, tome):
    print(f"{ACTION_TYPE_LEARN} {tome.id}")

  def wait(self):
    print(f"{ACTION_TYPE_WAIT}")

  def rest(self):
    print(f"{ACTION_TYPE_REST}")

  def find_critical_spell_path(self, recipes):
    vision = Vision(self.my_stock)
    visions = deque([vision])
    successful_visions = []
    found_stocks = []
    spells = [(spell.id, spell.get_tuple()) for spell in self.spells]
    found_recipes = []
    # TODO Virer les visions qui ne donnent plus sur rien
    while len(visions) and len(successful_visions) <5 and time.time() - self.start < TIME_TO_PASS_SEARCHING_VISIONS:
      vision = visions.popleft()
      for spell_id, spell in spells:
        ongoing_vision = copy.deepcopy(vision)
        expected_stock = tuple([sum(x) for x in zip(ongoing_vision.stock, spell)])
        if all([a >= 0 for a in list(expected_stock)]) and sum(list(expected_stock)) <= 10:
          ongoing_vision.stock = expected_stock
          ongoing_vision.casted_spells.append(spell_id)
          for recipe in recipes:
            if recipe.id not in found_recipes and all([(a >= abs(b)) for a, b in zip(ongoing_vision.stock,recipe.get_tuple())]):
                recipe.vision = ongoing_vision
                found_recipes.append(recipe.id)
                successful_visions.append(ongoing_vision)
          if not ongoing_vision.stock in found_stocks and len(ongoing_vision.casted_spells) < MAX_NUMBER_OF_STEPS_FOR_VISION:
            visions.append(ongoing_vision)
            found_stocks.append(ongoing_vision.stock)
    
    return successful_visions

  def play_best_action(self):
    # Find critical path for each recipe
    self.find_critical_spell_path(self.recipes)
    for recipe in recipes:  
      if recipe.vision:
        recipe.value += MAX_NUMBER_OF_STEPS_FOR_VISION  * 2 - len(recipe.vision.casted_spells) - max(Counter(recipe.vision.casted_spells).values()) + 1
      else:
        recipe.value = 0

    # TODO peut être a enlever plus tard pour faire entièrement confiance aux visions et tenter la recette presque atteinte mais plus intéressante
    if len(self.brewable_recipes):
      print_console("Je peux faire une potion, je fais la meilleure")
      self.brewable_recipes.sort(key=lambda recipe: recipe.value, reverse=True)
      self.brew(self.brewable_recipes[0])
    elif len(self.pure_tomes):
      print_console("Je peux apprendre un sort pur")
      if len(self.learnable_pure_tomes):
        self.learnable_pure_tomes.sort(key=lambda tome: tome.value, reverse=True)
        self.learn(self.learnable_pure_tomes[0])
      else:
        tier_0_generators = self.castable_spells.copy()
        tier_0_generators.sort(key=lambda spell: spell.delta_0, reverse=True)
        if len(tier_0_generators):
          self.cast(tier_0_generators[0])
        else:
          self.rest()
    elif len([recipe for recipe in self.recipes if recipe.value]):
      self.recipes.sort(key=lambda recipe: recipe.value, reverse=True)
      best_recipe = self.recipes[0]
      print_console("best vision {} for {}".format(best_recipe.vision, best_recipe))
      for spell_id in best_recipe.vision.casted_spells:
        spell = self.spells_dict[spell_id]
        if self.my_stock.can_cast(spell):
          self.cast(spell)
          break
      else:
        self.rest()
    else:
      print_console("no more spell to cast at all, beter to learn")
      # TODO Améliorer pour apprendre le sort le plus intéressant pour mon deck
      self.learn(self.tomes[0])
    print_console("total time elapsed {}".format(time.time() - self.start))

class Vision:
  def __init__(self, stock):
    self.stock = stock.get_tuple()
    self.iterations = 0
    self.casted_spells = []

  def __str__(self):
    return "{}(en {}) stock {}".format("->".join([str(spell_id) for spell_id in self.casted_spells]), len(self.casted_spells), self.stock)

  def cast(self, spell):
    self.stock.inv_0 += spell.delta_0
    self.stock.inv_1 += spell.delta_1
    self.stock.inv_2 += spell.delta_2
    self.stock.inv_3 += spell.delta_3
    self.iterations += 1
    self.casted_spells.append(spell)

class Stock:
  def __init__(self, inv_0, inv_1, inv_2, inv_3):
    self.inv_0 = inv_0
    self.inv_1 = inv_1
    self.inv_2 = inv_2
    self.inv_3 = inv_3

  def __str__(self):
    return "[{},{},{},{}]".format(self.inv_0, self.inv_1, self.inv_2, self.inv_3)

  def __eq__(self, other):
    return self.inv_0 == other.inv_0 and self.inv_1 == other.inv_1 and self.inv_2 == other.inv_2 and self.inv_3 == other.inv_3

  def get_tuple(self):
    return (self.inv_0, self.inv_1, self.inv_2, self.inv_3)

  def available_space(self):
    return 10 - self.inv_0 - self.inv_1 - self.inv_2 - self.inv_3

  def can_brew(self, recipe):
    if recipe.can_be_used(self):
        return True
    return False

  def could_cast(self, spell):
    if spell.can_be_used(self) and spell.place_needed() <= self.available_space():
        return True
    return False

  def can_cast(self, spell):
    if spell.castable and spell.can_be_used(self) and spell.place_needed() <= self.available_space():
        return True
    return False

  def can_learn(self, tome):
    if self.inv_0 >= tome.index:
        return True
    return False


class Magic: 
  def __init__(self, id, delta_0, delta_1, delta_2, delta_3):
    self.id = id
    self.delta_0 = delta_0
    self.delta_1 = delta_1
    self.delta_2 = delta_2
    self.delta_3 = delta_3
    self.total_delta = self.delta_0 * LVL_0_VALUE + self.delta_1 * LVL_1_VALUE + self.delta_2 * LVL_2_VALUE + self.delta_3 * LVL_3_VALUE

  def can_be_used(self, stock):
      if self.delta_0 + stock.inv_0 >= 0 and self.delta_1 + stock.inv_1 >= 0 and self.delta_2 + stock.inv_2 >= 0 and self.delta_3 + stock.inv_3 >= 0:
        return True
      return False

  def get_tuple(self):
    return (self.delta_0, self.delta_1, self.delta_2, self.delta_3)

  def place_needed(self):
    return self.delta_0 + self.delta_1 + self.delta_2 + self.delta_3

  def __str__(self):
    return "{}:[{},{},{},{}]".format(self.id,self.delta_0,self.delta_1,self.delta_2,self.delta_3)

class Recipe(Magic):
  def __init__(self, id, price, delta_0, delta_1, delta_2, delta_3):
    super().__init__(id, delta_0, delta_1, delta_2, delta_3)
    self.price = price
    self.value = self.price * 10 / abs(self.total_delta)
    self.vision = None

  def __str__(self):
    return "{} {}-> {}".format(super().__str__(), self.price, self.value)

  def set_successful_vision(self, vision):
    self.vision = vision
    self.value -= vision.iterations

class Spell(Magic):
  def __init__(self, id, castable, delta_0, delta_1, delta_2, delta_3):
    super().__init__(id, delta_0, delta_1, delta_2, delta_3)
    self.castable = castable
    self.value = self.total_delta

  def __str__(self):
    return "{} -> {}".format(super().__str__(), self.value)

  def __str__(self):
    return "{}:[{},{},{},{}]".format(self.id,self.delta_0,self.delta_1,self.delta_2,self.delta_3)

class Tome(Spell):
  def __init__(self, id, index, delta_0, delta_1, delta_2, delta_3):
    super().__init__(id, False, delta_0, delta_1, delta_2, delta_3)
    self.index = index
    self.value = self.total_delta
    self.pure = delta_0 >= 0 and delta_1 >= 0 and delta_2 >= 0 and delta_3 >= 0
    self.value = self.total_delta - index / 2

# game loop
game = Game()
while True:
  action_count = int(input())  # the number of spells and recipes in play
  recipes = []
  spells = []
  tomes = []
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
      spell = Spell(action_id, castable, delta_0, delta_1, delta_2, delta_3)
      spells.append(spell)
    elif action_type == ACTION_TYPE_LEARN:
      tome = Tome(action_id, tome_index, delta_0, delta_1, delta_2, delta_3)
      tomes.append(tome)
  for i in range(2):
    # inv_0: tier-0 ingredients in inventory
    # score: amount of rupees
    inv_0, inv_1, inv_2, inv_3, score = [int(j) for j in input().split()]
    if i == 0:
        my_stock = Stock(inv_0, inv_1, inv_2, inv_3)
        my_score = score
  game.reset(my_score, my_stock, recipes, spells, tomes)
  game.play_best_action()
