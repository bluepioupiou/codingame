import sys
import copy

# Reste à faire 
# Calculer exactement combien d'attaques sur un montre pour le faire tomber, idéalement le chiffre exact
# pour ça il faut d'abord préparer les cible et ensuite trouver comment les tomber

# Mettre en place la sauvegarde du deck pour tenir en compte ce qui peut sortir bientot

# Gerer les guards puis les lethal puis les trop grosses cartes ensuite seulement taper l'opposant

class Card:
    TYPE_CREATURE = 0
    TYPE_GREEN_ITEM = 1
    TYPE_RED_ITEM = 2
    TYPE_BLUE_ITEM = 3

    LOCATION_MY_HAND = 0
    LOCATION_MY_BOARD = 1
    LOCATION_OPPONENT_BOARD = -1
     
    def __init__(self, input_value):
        input_value = input_value.split()
        self.number = int(input_value[0])
        self.id = int(input_value[1])
        self.location = int(input_value[2])
        self.type = int(input_value[3])
        self.cost = int(input_value[4])
        self.attack = int(input_value[5])
        self.defense = int(input_value[6])
        self.abilities = str(input_value[7])
        self.my_health_change = int(input_value[8])
        self.opponent_health_change =int(input_value[9])
        self.draw = int(input_value[10])
        self.aces = []
        self.weight_effect = 0

    @property
    def weight(self):
        base_creature = 1
        base_item = 5
        if self.number in self.aces:
            return 100
        if type == self.TYPE_CREATURE:
            return base_creature + (self.attack * 1) + (self.defense * 0.5) + (5 if "G" in self.abilities else 0) \
                   + (5 if "W" in self.abilities else 0) + (5 if "L" in self.abilities else 0) \
                   + (2 if "C" in self.abilities else 0) + (2 if "B" in self.abilities else 0) \
                   + (2 if "D" in self.abilities else 0) - (self.cost * 2)
        else:
            return base_item + (self.attack * 1) + (self.defense * 0.5) + (5 if "G" in self.abilities else 0) \
                   + (5 if "W" in self.abilities else 0) + (5 if "L" in self.abilities else 0) \
                   + (2 if "C" in self.abilities else 0) + (2 if "B" in self.abilities else 0) \
                   + (2 if "D" in self.abilities else 0) - (self.cost * 2)

    def __str__(self):
        return "card(#" + str(self.number) + " " + str(self.id) + ") " + str(self.weight) + " | " + self.abilities + " | c:" + str(self.cost) + "-a:" + str(self.attack)


class DraftCard(Card):

    def __init__(self, input_value, position):
        super().__init__(input_value)
        self.position = position
        self.aces = [122, 142, 143, 151]



class BattleCard(Card):

    has_attacked = False

    def __init__(self, input_value):
        super().__init__(input_value)
        self.aces = [80, 116]

MAX_TROOP_ON_BOARD = 6
COST_HISTOGRAMME = {
    0: 10,
    1: 4,
    2: 6,
    3: 6,
    4: 8,
    5: 6,
    6: 4,
    7: 4,
    8: 2,
    9: 2,
    10: 2,
    11: 2,
    12: 2
}

ITEM_HISTOGRAMME = {
    Card.TYPE_GREEN_ITEM: 4,
    Card.TYPE_RED_ITEM: 4,
    Card.TYPE_BLUE_ITEM: 4
}

my_board = []
opponent_board = []
hand = []
actions = []
my_mana = 0

def summon(troop):
    global actions
    global hand
    global my_board
    global my_mana

    actions.append("SUMMON " + str(troop.id))
    hand = list(filter(lambda x: x.id != troop.id, hand))
    if "C" not in troop.abilities:
        troop.has_attacked = True
    my_board.append(troop)
    my_mana -= troop.cost


def attack_player(troop):
    global my_board
    global actions

    actions.append("ATTACK " + str(troop.id) + " -1")
    troop.has_attacked = True


def attack(troop, enemy):
    global opponent_board
    global actions
    global my_board

    is_dead = False

    actions.append("ATTACK " + str(troop.id) + " " + str(enemy.id))
    troop.has_attacked = True
    print(str(troop.id) + " attack " +str(enemy.id), file=sys.stderr)
    if "W" in enemy.abilities:
        enemy.abilities = enemy.abilities[0:5] + "-"
    elif "L" in troop.abilities:
        enemy.defense = 0
    else:
        enemy.defense = enemy.defense - troop.attack

    if enemy.defense <= 0:
        opponent_board = list(filter(lambda x: x.id != enemy.id, opponent_board))
        is_dead = True

    if "W" in troop.abilities:
        troop.abilities = troop.abilities[0:4] + "-"
    elif "L" in enemy.abilities:
        troop.defense = 0
    else:
        troop.defense = troop.defense - enemy.attack

    if troop.defense <= 0:
        print("my creature will die", file=sys.stderr)
        my_board = list(filter(lambda x: x.id != troop.id, my_board))


    return is_dead


def use_blue_item(item):
    global hand
    global my_mana

    actions.append("USE " + str(item.id) + " -1")
    hand = list(filter(lambda x: x.id != item.id, hand))
    my_mana -= item.cost


def use_item(item, creature, simulate=False):
    global hand
    global opponent_board
    global my_board
    global my_mana

    abilities = ["B", "C", "D", "G", "L", "W"]

    if not simulate:
        actions.append("USE " + str(item.id) + " " + str(creature.id))
        hand = list(filter(lambda x: x.id != item.id, hand))
        my_mana -= item.cost
    else:
        creature = copy.deepcopy(creature)

    if item.type == item.TYPE_RED_ITEM:
        for index, ability in enumerate(abilities):
            if ability in item.abilities:
                creature.abilities = "".join(["-" if i == index else c for i, c in enumerate(creature.abilities)])
        creature.attack -= item.attack
        creature.defense -= item.defense

    elif item.type == item.TYPE_GREEN_ITEM:
        for index, ability in enumerate(abilities):
            if ability in item.abilities:
                creature.abilities = "".join([ability if i == index else c for i, c in enumerate(creature.abilities)])
        creature.attack += item.attack
        creature.defense += item.defense

    return creature


def attack_group(group, ability, priority=False):
    global hand, my_board, my_mana
    # Check the guard enemies
    group.sort(key=lambda x: x.defense, reverse=True)
    for enemy in group:
        managed = False
        if ability:
            # Can I 'remove' them with items
            my_items = list(filter(lambda x: ability in x.abilities and x.type == Card.TYPE_RED_ITEM, hand))
            for item in my_items:
                if item.cost <= my_mana:
                    use_item(item, enemy)
                    managed = True
                    break
            if managed:
                continue

        # If there is a ward ability, trying to remove it first
        if "W" in enemy.abilities:
            unwarded = False
            my_items = list(filter(lambda x: "L" in x.abilities and x.type == Card.TYPE_RED_ITEM, hand))
            for item in my_items:
                if item.cost <= my_mana:
                    use_item(item, enemy)
                    unwarded = True
                    break
            if not unwarded:
                anti_ward = list(filter(lambda x: "G" not in x.abilities and "L" not in x.abilities and x.attack and not x.has_attacked,my_board))
                anti_ward.sort(key=lambda x: x.attack)
                if anti_ward:
                    attack(anti_ward[0], enemy)

        # Find a way to defeat it with letals
        letals = list(filter(lambda x: "G" not in x.abilities and "L" in x.abilities and x.attack and not x.has_attacked, my_board))
        letals.sort(key=lambda x: x.attack)
        for attacker in letals:
            is_dead = attack(attacker, enemy)
            if is_dead:
                managed = True
                break
        if managed:
            continue

        # Find a way to defeat it without guards first with exact kill, secondly with more, and finally with sum of several
        sub_group = list(filter(lambda x: "G" not in x.abilities and not x.has_attacked, my_board))
        kill_with_best_combination(sub_group, enemy)

        # If there is still guard I use MY guards
        if priority:
            sub_group = list(filter(lambda x: not x.has_attacked, my_board))
            kill_with_best_combination(sub_group, enemy)


def kill_with_best_combination(group, enemy):
    global my_board

    exact_kill = list(filter(lambda x: x.attack == enemy.defense, group))
    if exact_kill:
        is_dead = attack(exact_kill[0], enemy)
        if is_dead:
            return True
    else:
        more_kill = list(filter(lambda x: x.attack > enemy.defense, group))
        if more_kill:
            is_dead = attack(more_kill[0], enemy)
            if is_dead:
                return True
        else:
            to_sum_attackers = list(filter(lambda x: x.attack, group))
            to_sum_attackers.sort(key=lambda x: x.attack, reverse=True)
            for attacker in to_sum_attackers:
                is_dead = attack(attacker, enemy)
                if is_dead:
                    return True

    return False

# game loop
while True:
    my_mana = 0
    for i in range(2):
        player_health, player_mana, player_deck, player_rune = [int(j) for j in input().split()]   
        if i == 0:
            my_mana = player_mana
            my_health= player_health
    opponent_hand = int(input())
    card_count = int(input())
    min_cost = 99
    max_attack = 0
    max_defense = 0
    can_attack = []
    can_summon = []
    can_item = []
    cards = []
    stop_looking = False
    summoned = 0
    # By default target is the opponent player
    targets = []
    # Dispatch cards in 'good' lists
    my_board = []
    opponent_board = []
    hand = []
    for i in range(card_count):
        if my_mana == 0:
            card = DraftCard(input(), i)
            print(card, file=sys.stderr)
            cards.append(card)
        else:
            card = BattleCard(input())
            if card.location == BattleCard.LOCATION_MY_HAND:
                hand.append(card)
            elif card.location == BattleCard.LOCATION_MY_BOARD:
                my_board.append(card)
            elif card.location == BattleCard.LOCATION_OPPONENT_BOARD:
                opponent_board.append(card)

    # Drawing of cards
    if my_mana == 0:
        cards.sort(key=lambda x: x.weight, reverse=True)
        choosen = cards[0].position
        for card in cards:
            if COST_HISTOGRAMME[card.cost] > 0:
                if card.type == Card.TYPE_CREATURE or ITEM_HISTOGRAMME[card.type > 0]:
                    choosen = card.position
                    COST_HISTOGRAMME[card.cost] -= 1
                    if card.type != Card.TYPE_CREATURE:
                        ITEM_HISTOGRAMME[card.type] -= 1
                    break
        print(COST_HISTOGRAMME, file=sys.stderr)
        print(ITEM_HISTOGRAMME, file=sys.stderr)
        print("PICK " + str(choosen))
    # Really playing
    else:
        actions = []
        # See if I can invoque cards with charge
        my_chargers = list(filter(lambda x: "C" in x.abilities and x.attack and x.type == Card.TYPE_CREATURE, hand))
        my_chargers.sort(key=lambda x: x.weight, reverse=True)
        for charger in my_chargers:
            if charger.cost <= my_mana and len(my_board) < MAX_TROOP_ON_BOARD:
                summon(charger)

        # Attack groups
        guard_enemies = list(filter(lambda x: "G" in x.abilities, opponent_board))
        attack_group(guard_enemies, "G", True)

        lethal_enemies = list(filter(lambda x: "L" in x.abilities, opponent_board))
        attack_group(lethal_enemies, "L", True)

        too_much_attack_ennemies = list(filter(lambda x: x.attack > 6, opponent_board))
        attack_group(too_much_attack_ennemies, None, False)

        remaining_ennemies = list(filter(lambda x: x.attack, opponent_board))
        remaining_ennemies.sort(key=lambda x: x.weight)
        attack_group(remaining_ennemies[2:], None, False)

        # See if we can still invoque some creatures or use item
        # TODO : Find best combination to play from hand
        for card in hand:
            if card.cost <= my_mana:
                if card.type == Card.TYPE_CREATURE  and len(my_board) < MAX_TROOP_ON_BOARD:
                    summon(card)
                if card.type == Card.TYPE_GREEN_ITEM and my_board:
                    # Try to use item on card with best effect
                    for my_creature in my_board:
                        changed_creature = use_item(card, my_creature, simulate=True)
                        my_creature.weight_effect = changed_creature.weight - my_creature.weight
                        my_board = list(map(lambda x: x if x.id != my_creature.id else my_creature, my_board))
                    my_board.sort(key=lambda x: x.weight_effect, reverse=True)
                    use_item(card, my_board[0])
                if card.type == Card.TYPE_RED_ITEM and opponent_board:
                    # Try to use item on card with worse effect
                    for creature in opponent_board:
                        changed_creature = use_item(card, creature, simulate=True)
                        creature.weight_effect = creature.weight - changed_creature.weight
                        opponent_board = list(map(lambda x: x if x.id != creature.id else creature, opponent_board))
                        opponent_board.sort(key=lambda x: x.weight_effect, reverse=True)
                    use_item(card, opponent_board[0])
                if card.type == Card.TYPE_BLUE_ITEM:
                    use_blue_item(card)

        # Lastly attack the opponent player
        opponent_guards = list(filter(lambda x: "G" in x.abilities, opponent_board))
        if not opponent_guards:
            my_attackers = list(filter(lambda x: x.attack and not x.has_attacked, my_board))
            print("my_attackers " + str(len(my_attackers)), file=sys.stderr)
            for attacker in my_attackers:
                attack_player(attacker)
        else:
            print("still opponents with guard, can't do", file=sys.stderr)

        if actions:
            print(";".join(actions))
        else:
            print("PASS")
        

