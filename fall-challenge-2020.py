import sys
import math
from collections import deque, Counter
import time
import numpy

# Rajouter le calcul des éléments restants dans le compte du score
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

EARLY_GAME_LEARN_TURNS = 10

MAX_NUMBER_OF_STEPS_FOR_VISION = 6
VISION_PONDERATION_TARGET_BREW = MAX_NUMBER_OF_STEPS_FOR_VISION

TIME_TO_PASS_SEARCHING_VISIONS = 0.035

LOGGING_READ_INPUT_VISION = False
LOGGING_PART_VISION_DETAIL = False
LOGGING_PART_VISION_SPELLS = False
LOGGING_PART_VISION_TOMES = False
LOGGING_PART_VISION_SUMMARY = True

LOGGING_CYCLE_TO_PRINT = None

def print_console(message, loggin_part = True):
  if loggin_part and not LOGGING_CYCLE_TO_PRINT:
    print(message, file=sys.stderr, flush=True)

class Game: 
  def __init__(self):
    self.cycles = 0
    self.score = 0
    self.recipes = []
    self.spells = []
    self.brewable_recipes = []
    self.castable_spells = []

  def __str__(self):
    return "game:[{},{},{},{}]".format(self.inv_0, self.inv_1, self.inv_2, self.inv_3)

  def reset(self, my_score, my_stock, recipes, spells, tomes):
    self.cycles += 1
    self.start = time.time()
    self.my_score = my_score
    self.my_stock = my_stock
    self.recipes = recipes
    self.spells = spells
    self.spells_dict = {}
    for spell in spells:
      self.spells_dict[spell.id] = spell
    self.tomes = tomes
    self.tomes_dict = {}
    for tome in self.tomes:
      self.tomes_dict[tome.id] = tome
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

  # TODO utilisation des repeatable
  def find_critical_spell_path(self):
    successful_visions = []
    found_stocks = []
    found_recipes = []
    stock = self.my_stock.get_tuple()
    spells = [(spell.id, spell.get_tuple()) for spell in self.spells]
    tomes = [(tome.id, tome.get_tuple(), tome.index, tome.tax) for tome in self.tomes]
    vision = Vision(stock, spells, tomes)
    visions = deque([vision])
    count = 0
    max_count_actions = 0
    while len(visions) and len(successful_visions) <5 and time.time() - self.start < TIME_TO_PASS_SEARCHING_VISIONS:
      vision = visions.popleft()
      count += 1
      # Parcours les spells et leur effet
      print_console("starting vision {}".format(vision), LOGGING_PART_VISION_DETAIL)
      for spell_id, spell in vision.spells:
        expected_stock = tuple([sum(x) for x in zip(vision.stock, spell)])
        if all([a >= 0 for a in list(expected_stock)]) and sum(list(expected_stock)) <= 10:
          ongoing_vision = Vision(vision.stock, vision.spells[:], vision.tomes[:], vision.actions[:])
          ongoing_vision.stock = expected_stock
          ongoing_vision.add_action({"type": ACTION_TYPE_CAST, "id":spell_id})
          
          if not ongoing_vision.stock in found_stocks and len(ongoing_vision.actions) < MAX_NUMBER_OF_STEPS_FOR_VISION:
            for recipe in self.recipes:
              if recipe.id not in found_recipes and all([(a >= abs(b)) for a, b in zip(ongoing_vision.stock,recipe.get_tuple())]):
                recipe.vision = ongoing_vision
                ongoing_vision.recipe = recipe
                found_recipes.append(recipe.id)
                successful_visions.append(ongoing_vision)
            
            visions.append(ongoing_vision)
            max_count_actions = max(max_count_actions, len(vision.actions) + vision.rest_count)
            found_stocks.append(ongoing_vision.stock)
      for i, (tome_id, tome, index, tax) in enumerate(vision.tomes[:]):
        print_console(" - checking tome {}".format(tome_id), LOGGING_PART_VISION_TOMES)
        if vision.stock[0] >= index:
          ongoing_vision = Vision(vision.stock, vision.spells[:], vision.tomes[:], vision.actions[:])
          print_console("   - can learn {} in vision {} ({} >= {}) {} spells and {} tomes".format(tome_id, ongoing_vision, ongoing_vision.stock[0], index, len(ongoing_vision.spells), len(ongoing_vision.tomes)), LOGGING_PART_VISION_TOMES)
          ongoing_vision.stock = (ongoing_vision.stock[0] + min(tax, 10 - sum(list(ongoing_vision.stock))) - index, ongoing_vision.stock[1], ongoing_vision.stock[2], ongoing_vision.stock[3])
          ongoing_vision.add_action({"type": ACTION_TYPE_LEARN, "id":tome_id})
          ongoing_vision.spells.append((tome_id, tome))
          print_console("Will pop position {} of {}".format(i, len( ongoing_vision.tomes)), LOGGING_PART_VISION_TOMES)
          ongoing_vision.tomes.pop(i)
          for j, tome in enumerate(ongoing_vision.tomes):
            if j < i:
              ongoing_vision.tomes[j] = (tome[0], tome[1], tome[2], tome[3] + 1)
            else:
              ongoing_vision.tomes[j] = (tome[0], tome[1], tome[2] - 1, tome[3])
          visions.append(ongoing_vision)
          max_count_actions = max(max_count_actions, len(vision.actions) + vision.rest_count)

          print_console("   - learned {} in vision {}. {} spells and {} tomes".format(tome_id, ongoing_vision, len(ongoing_vision.spells), len(ongoing_vision.tomes)), LOGGING_PART_VISION_TOMES)


    print_console("{} visions total, {} actions max".format(count, max_count_actions), LOGGING_PART_VISION_SUMMARY)
    for vision in successful_visions:
      print_console("{} for {}".format(vision, vision.recipe), LOGGING_PART_VISION_SUMMARY)

    return successful_visions

  def get_best_castable_generator(self, lvl):
    tier_generators = list(filter(lambda spell: spell.get_tuple()[lvl] > 0, self.castable_spells))
    if len(tier_generators):
      tier_generators.sort(key=lambda spell: spell.get_tuple()[lvl], reverse=True)
      return tier_generators[0]
    return None
        
  def play_best_action(self):
    # Find critical path for each recipe
    self.find_critical_spell_path()
    for recipe in recipes:  
      if recipe.vision:
        recipe.value += (MAX_NUMBER_OF_STEPS_FOR_VISION  * 2 - len(recipe.vision.actions) - recipe.vision.rest_count) / MAX_NUMBER_OF_STEPS_FOR_VISION

    # TODO peut être a enlever plus tard pour faire entièrement confiance aux visions et tenter la recette presque atteinte mais plus intéressante
    #if len(self.brewable_recipes):
      #print_console("Je peux faire une potion, je fais la meilleure")
      #self.brewable_recipes.sort(key=lambda recipe: recipe.value, reverse=True)
      #self.brew(self.brewable_recipes[0])
    if len(self.pure_tomes):
      if len(self.learnable_pure_tomes):
        print_console("Je peux apprendre un sort pur directement")
        self.learnable_pure_tomes.sort(key=lambda tome: tome.value, reverse=True)
        self.learn(self.learnable_pure_tomes[0])
      else:
        tier_generator = self.get_best_castable_generator(0)
        if tier_generator:
          print_console("Je peux apprendre un sort pur en lancant {}".format(tier_generator))
          self.cast(tier_generator)
        else:
          print_console("Je me repose pour apprendre un sort pur")
          self.rest()
    elif self.cycles < EARLY_GAME_LEARN_TURNS:
      print_console("Pas de sort pur, j'apprends ce que je peux")
      # TODO meilleur choix de sort que juste le premier
      self.learn(self.tomes[0])
    else:
      self.recipes.sort(key=lambda recipe: recipe.value, reverse=True)
      best_recipe = self.recipes[0]
      if self.my_stock.can_brew(best_recipe):
        # TODO Attention si c'est la derniere et que je ne mene pas au score
        print_console("Je peux faire la potion, je fais la meilleure")
        self.brew(best_recipe)
      elif best_recipe.vision:
        print_console("best vision {} for {}".format(best_recipe.vision, best_recipe))
        for action in best_recipe.vision.actions:
          if action["type"] == ACTION_TYPE_CAST and action["id"] in self.spells_dict:
            spell = self.spells_dict[action["id"]]
            if self.my_stock.can_cast(spell):
              self.cast(spell)
              break
          elif action["type"] == ACTION_TYPE_LEARN and action["id"] in self.tomes_dict:
            tome = self.tomes_dict[action["id"]]
            if self.my_stock.can_learn(tome):
              self.learn(tome)
              break
        else: 
          self.rest()
      else:
        result = self.my_stock.if_magic_applied(best_recipe)
        for lvl in [3, 2, 1, 0]:
          tier_generator = self.get_best_castable_generator(lvl)
          if tier_generator:
            print_console("trouvé générateur {} pour me rapprocher".format(tier_generator))
            self.cast(tier_generator)
            break
        else:
          print_console("pas de vision, on avance comme on peut, pour le moment on apprend")
          self.learn(self.tomes[0])

    print_console("total time elapsed {}".format(time.time() - self.start))

class Vision:
  def __init__(self, stock, spells, tomes, actions = []):
    self.stock = stock
    self.spells = spells
    self.tomes = tomes
    self.actions = actions
    self.rest_count = 0

  def __str__(self):
    return "{}(en {} + {} rest) stock {}".format("->".join([str(action["id"]) for action in self.actions]), len(self.actions), self.rest_count, self.stock)

  def add_action(self, action):
    self.actions.append(action)
    self.rest_count =  max(Counter([action["id"] for action in self.actions]).values()) - 1


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

  def if_magic_applied(self, magic):
    return numpy.add(magic.get_tuple(), self.get_tuple())

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
    self.value = self.price
    self.vision = None

  def __str__(self):
    return "{} {}-> {}".format(super().__str__(), self.price, self.value)

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
  def __init__(self, id, index, tax, delta_0, delta_1, delta_2, delta_3):
    super().__init__(id, False, delta_0, delta_1, delta_2, delta_3)
    self.index = index
    self.tax = tax
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
      print_console("found tome {}".format(action_id), LOGGING_READ_INPUT_VISION)
      tome = Tome(action_id, tome_index, tax_count, delta_0, delta_1, delta_2, delta_3)
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
