import sys
import math

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

def print_console(message):
    print(message, file=sys.stderr)

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
    self.my_score = my_score
    self.my_stock = my_stock
    self.recipes = recipes
    self.spells = spells
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

  def play_best_action(self):
    print_console("best recipe {}".format(self.recipes[0]))
    if len(self.brewable_recipes):
      self.brew(self.brewable_recipes[0])
    elif len(self.pure_tomes):
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
    elif len(self.castable_spells):
      best_recipe = self.recipes[0]
      usefull_spells = [spell for spell in self.castable_spells if spell.can_help_brew_from_stock(best_recipe, self.my_stock)]
      usefull_spells.sort(key=lambda spell: spell.value, reverse=True)
      if len(usefull_spells):
        print_console("best spell {}".format(usefull_spells[0]))
        self.cast(usefull_spells[0])
      else:
        print_console("no more usefull spell to cast")
        self.rest()
    else:
      print_console("no more spell to cast at all")
      self.rest()

class Stock:
  def __init__(self, inv_0, inv_1, inv_2, inv_3):
    self.inv_0 = inv_0
    self.inv_1 = inv_1
    self.inv_2 = inv_2
    self.inv_3 = inv_3

  def available_space(self):
    return 10 - self.inv_0 - self.inv_1 - self.inv_2 - self.inv_3

  def can_brew(self, recipe):
    if recipe.can_be_used(self):
        return True

  def can_cast(self, spell):
    if spell.castable and spell.can_be_used(self) and spell.place_needed() <= self.available_space():
        return True

  def can_learn(self, tome):
    if self.inv_0 >= tome.index:
        return True


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

  def place_needed(self):
    return self.delta_0 + self.delta_1 + self.delta_2 + self.delta_3

  def __str__(self):
    return "{}:[{},{},{},{}]".format(self.id,self.delta_0,self.delta_1,self.delta_2,self.delta_3)

class Recipe(Magic):
  def __init__(self, id, price, delta_0, delta_1, delta_2, delta_3):
    super().__init__(id, delta_0, delta_1, delta_2, delta_3)
    self.price = price
    self.value = self.price / abs(self.total_delta)

  def __str__(self):
    return "{} {}-> {}".format(super().__str__(), self.price, self.value)


class Spell(Magic):
  def __init__(self, id, castable, delta_0, delta_1, delta_2, delta_3):
    super().__init__(id, delta_0, delta_1, delta_2, delta_3)
    self.castable = castable
    self.value = self.total_delta

  def can_help_brew_from_stock(self, recipe, stock):
    need_tier_3 = stock.inv_3 + recipe.delta_3 < 0
    need_tier_2 = stock.inv_2 + recipe.delta_2 < 0
    need_tier_1 = stock.inv_1 + recipe.delta_1 < 0
    need_tier_0 = stock.inv_0 + recipe.delta_0 < 0
    if (self.delta_3 > 0 and need_tier_3):
      return True
    elif (self.delta_2 > 0 and (need_tier_3 or need_tier_2)):
      return True
    elif (self.delta_1 > 0 and (need_tier_3 or need_tier_2 or need_tier_1)):
      return True
    elif (self.delta_0 > 0 and (need_tier_3 or need_tier_2 or need_tier_1  or need_tier_0)):
      return True
    return False

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
