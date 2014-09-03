#http://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_python%2Blibtcod

import libtcodpy as libtcod
import math
import textwrap
import shelve

MAIN_TITLE = 'The best game you never knew you wanted'

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 43

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

#PLAYER STUFF
HEAL_AMOUNT = 40
PLAYER_HEALTH_START = 100
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150

#LIGHTNING BOLT
LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5

#SCROLL OF CONFUSION
CONFUSE_NUM_TURNS = 10
CONFUSE_RANGE = 8

#SCROLL OF FIREBALL
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25

CONTROLS_TEXT = ('ALT+ENTER: FULLSCREEN \n'+
'I: INVENTORY \n'+
'G: PICK UP ITEM \n'+
'D: DROP ITEM\n'+
'COMMA: GO DOWN STAIRS \n'+
'ARROW KEYS or NUMPAD: MOVE \n'+
'WAIT: NUM 5')
				
#####################################################
#color_dark_wall = libtcod.Color(0,0,100)
#color_light_wall = libtcod.Color(130,110,50)
#color_dark_ground = libtcod.Color(50,50,150)
#color_light_ground = libtcod.Color(200,180,50)
#####################################################
color_dark_wall = libtcod.darkest_grey
color_light_wall = libtcod.grey
color_dark_ground = libtcod.darkest_sepia
color_light_ground = libtcod.light_sepia

FOV_ALGO = 0 # default FOV algorithm for libtcod
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

#sizes and coordinates for GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
CHARACTER_SCREEN_WIDTH = 30
LEVEL_SCREEN_WIDTH = 40

#message bar size
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

INVENTORY_WIDTH = 50

#MONSTER SPAWN CHANCES
monster_chances = {'orc': 20, 
					'troll': 10, 
					'kobold': 30, 
					'gnome': 40}

#ITEM PLACE CHANCES
item_chances = {'potion': 70,
				'scroll of fireball': 10, 
				'scroll of lightning': 10, 
				'scroll of confusion': 10}

material_chances = {'wood': 30,
					'stone':30,
					'iron': 23,
					'steel': 15}
					
weapon_type_chances = {'sword':20,
						'axe':20,
						'dagger':20,
						'staff':20}
						
wand_type_chances = {'lightning':43,
					'fireball':45,
					'confusion':58,
					'more spells':50}
				
				
#IN PROGRESS
def random_weapon_material():
	global weapon_material
	weapon_material = random_choice(material_chances)
	
	if weapon_material == 'wood':
		return 'wood', 1
	if weapon_material == 'stone':
		return 'stone', 2
	if weapon_material == 'iron':
		return 'iron', 3
	if weapon_material == 'steel':
		return 'steel', 4
	
def random_weapon_type():
	weapon_type = random_choice(weapon_type_chances)
	
	if weapon_type == 'sword':
		return 'sword', 'right hand'
	elif weapon_type == 'axe':
		return 'axe', 'right hand'
	elif weapon_type == 'wand':
		#need more stuff here
		return 'wand', 'right hand'
	elif weapon_type == 'staff':
		return 'staff', 'both hands'
	elif weapon_type == 'bow':
		return 'bow', 'both hands'
	elif weapon_type == 'dagger':
		return 'dagger', 'right hand'

def place_random_weapon(x,y):
	weapon_type, weapon_slot = random_weapon_type()
	weapon_material, weapon_bonus = random_weapon_material()
	
	print (weapon_type +' '+ weapon_slot +' '+ weapon_material +' '+ str(weapon_bonus))
	
	if weapon_type == 'sword':
		equipment_component = Equipment(slot=weapon_slot, power_bonus=weapon_bonus)
		return Object(x,y, '/', (weapon_material+' sword'), libtcod.sky, equipment=equipment_component)
	elif weapon_type == 'axe':
		equipment_component = Equipment(slot=weapon_slot, power_bonus=weapon_bonus)
		return Object(x,y, 'P', (weapon_material+' axe'), libtcod.sky, equipment=equipment_component)
	elif weapon_type == 'staff':
		equipment_component = Equipment(slot=weapon_slot, power_bonus=weapon_bonus)
		return Object(x,y, '|', (weapon_material+' staff'), libtcod.sky, equipment=equipment_component)
	elif weapon_type == 'dagger':
		equipment_component = Equipment(slot=weapon_slot, power_bonus=weapon_bonus)
		return Object(x,y, '-', (weapon_material+' dagger'), libtcod.sky, equipment=equipment_component)
#	elif weapon_type == 'bow':
#		break
#	elif weapon_type == 'wand':
#		break
	
	
	
	
	
#TILES OBJECT walls and floor and such
class Tile:
	#a tile of the map and its properties
	def __init__(self, blocked, block_sight = None):
		self.blocked = blocked
		
		self.explored = False
		
		#by default, if a tile is blocked, it also blocks sight
		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight
	
class Rect:
	#a rectangle on the map, used to characterize a room.
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h
		
	def center(self):
		center_x = (self.x1 + self.x2) / 2
		center_y = (self.y1 + self.y2) / 2
		return (center_x, center_y)
		
	def intersect(self, other):
		#return true if this rectangle intersects with another one
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and
				self.y1 <= other.y2 and self.y2 >= other.y1)
	
#PLAYER OBJECT
class Object:
	#this is a generic object: the player, a monster, an item, the stairs...
	#it's always represented by a character on screen.
	def __init__(self, x, y, char, name, color, blocks=False, always_visible=False, fighter=None, ai=None, item=None, equipment=None):
		self.x = x
		self.y = y
		self.char = char
		self.color = color
		self.name = name
		self.blocks = blocks
		self.always_visible = always_visible
		self.item = item
		if self.item: #let the item component know who owns it
			self.item.owner = self
		
		self.fighter = fighter
		if self.fighter: #let the fighter component know who owns it
			self.fighter.owner = self
			
		self.equipment = equipment
		if self.equipment: #let the equipment component know who owns it
			self.equipment.owner = self
			
			#item component so equipment component works properly
			self.item = Item()
			self.item.owner = self
			
		self.ai = ai
		if self.ai: #let the AI component know who owns it
			self.ai.owner = self
		
	def move(self, dx, dy):
		if not is_blocked(self.x + dx, self.y + dy):
			#move by the given amount
			self.x += dx
			self.y += dy
			
	def move_towards(self, target_x, target_y):
		#vector from this object to the target, and distance
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx ** 2 + dy ** 2)
		
		#normalize it to length 1 (preserving direction), then round it and convert to integer
		#to restrict it to the map grid
		dx = int(round(dx / distance))
		dy = int(round(dy / distance))
		self.move(dx, dy)
		
	def distance_to(self, other):
		#return the distance to another object
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx ** 2 + dy ** 2)
		
	def distance(self, x, y):
		#return the distance to some coordinates
		return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
		
	def send_to_back(self):
		#make this object drawn first
		global objects
		objects.remove(self)
		objects.insert(0,self)
	
	def draw(self):
		#only show if visible to the player
		if (libtcod.map_is_in_fov(fov_map, self.x, self.y) or
				(self.always_visible and map[self.x][self.y].explored) or self.name=='room number'):
			#set the color and then draw the character that represents this object at its position
			libtcod.console_set_default_foreground(con, self.color)
			libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
		
	def clear(self):
		#erase the character that represents this object
		libtcod.console_put_char(con, self.x, self.y, ' ',libtcod.BKGND_NONE)
		
class Fighter:
	#combat-related properties and methods (monster, player, NPC)
	def __init__(self, hp, defense, power, xp, death_function=None):
		self.base_max_hp = hp
		self.hp = hp
		self.base_defense = defense
		self.base_power = power
		self.xp = xp
		self.death_function = death_function
		
	@property
	def power(self): #return actual defense, by summing up the bonuses from all equipped items
		bonus = sum(equipment.power_bonus for equipment in get_all_equipped(self.owner))
		return self.base_power + bonus
		
	@property
	def defense(self):
		bonus = sum(equipment.defense_bonus for equipment in get_all_equipped(self.owner))
		return self.base_defense + bonus
		
	@property
	def max_hp(self):
		bonus = sum(equipment.max_hp_bonus for equipment in get_all_equipped(self.owner))
		return self.base_max_hp + bonus
		
	def take_damage(self, damage):
		#apply damage if possible
		if damage > 0:
			self.hp -= damage
			
			#check for deaths
			if self.hp <= 0:
				if self.owner != player: #yields experience
					player.fighter.xp += self.xp
					
				function = self.death_function
				if function is not None:
					function(self.owner)
					
	def attack(self, target):
		#a simple formula for attack damage
		damage = self.power - target.fighter.defense
		
		if damage > 0:
			#make target take some damage
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
			target.fighter.take_damage(damage)
		else:
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect.')
			
	def heal(self, amount):
		#heal by the given amount, without going over the max
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp		

class Item:
	
	def __init__(self, use_function=None):
		self.use_function = use_function
		
	def use(self):
		#special case: if the object has equipment component, the action equips/dequips
		if self.owner.equipment:
			self.owner.equipment.toggle_equip()
			return
		#just call the "use_function" if it is defined
		if self.use_function is None:
			message('The ' + self.owner.name + ' cannot be used.')
		else:
			if self.use_function() != 'cancelled':
				inventory.remove(self.owner) #destroy after use, unless it was cancelled for some reason
				
	#an item that can be picked up and used.
	def pick_up(self):
		#add to the player's inventory and remove from the map
		if len(inventory) >= 26:
			message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.red)
		else:
			inventory.append(self.owner)
			objects.remove(self.owner)
			message('You picked up a ' + self.owner.name + '!', libtcod.green)
			
		#special case: auto equip if slot is unused
		equipment = self.owner.equipment
		if equipment and (get_equipped_in_slot(equipment.slot) is None):
			equipment.equip()
			
	def drop(self):
		#add to the map and remove from player's inventory. place at players feet
		objects.append(self.owner)
		#special case: if the object has the equipment component remove it before dropping
		if self.owner.equipment:
			self.owner.equipment.dequip()
			
		inventory.remove(self.owner)
		self.owner.x = player.x
		self.owner.y = player.y
		message('You dropped a ' + self.owner.name + '.', libtcod.yellow)

class Equipment:
	#an object that can be equipped, yielding bonuses. automatically adds the Item component.
	def __init__(self, slot, power_bonus=0, defense_bonus=0, max_hp_bonus=0):
		self.slot = slot
		self.is_equipped = False
		self.power_bonus = power_bonus
		self.defense_bonus = defense_bonus
		self.max_hp_bonus = max_hp_bonus
		
	def toggle_equip(self): #toggle equip/dequip status
		if self.is_equipped:
			self.dequip()
		else:
			self.equip()
			
	def equip(self):
		#if the slot is already being used, remove whatever is there first
		
		if self.slot == 'both hands':
			old_equipment_right = get_equipped_in_slot('right hand')
			old_equipment_left = get_equipped_in_slot('left hand')
			if old_equipment_right is not None:
				old_equipment_right.dequip()
			if old_equipment_left is not None:
				old_equipment_left.dequip()
		old_equipment = get_equipped_in_slot(self.slot)
		
		if old_equipment is not None:
			old_equipment.dequip()
			
		#equip object and show a message about it
		self.is_equipped = True
		message('Equipped ' + self.owner.name + ' on ' + self.slot + '.', libtcod.light_green)
				
	def dequip(self):
		#dequip object and show message about it
		if not self.is_equipped: return
		self.is_equipped = False
		message('Removed ' + self.owner.name + ' from ' + self.slot + '.', libtcod.light_yellow)
		
	def get_equipment_type(self):
		return self.owner.name

class BasicMonster:
	#AI for a basic monster
	def take_turn(self):
		#a basic monster takes its turn, If you can see it, it can see you
		monster = self.owner
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
			
			#move towards the player if far away
			if monster.distance_to(player) >=2:
				monster.move_towards(player.x, player.y)
				
			#close enough to attack
			elif player.fighter.hp > 0:
				monster.fighter.attack(player)

class ConfusedMonster:
	#AI for a confused monster
	def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
		self.old_ai = old_ai
		self.num_turns = num_turns
		
	def take_turn(self):
		if self.num_turns > 0: #still confused
			#move in a random direction
			self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
			self.num_turns -= 1
			
		else: #restore previous AI. this one is deleted because it's not referenced anymore
			self.owner.ai = self.old_ai
			message('The ' + self.owner.name + ' is no longer confused.', libtcod.red)
				
def menu(header, options, width):
	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')
	
	#calculate total height for the header (after auto wrap) and one line per option
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
	if header == '':
		header_height = 0
		
	height = len(options) + header_height
	
	#create an off-screen console that represents the menu's window
	window = libtcod.console_new(width, height)
	
	#print the header, with auto wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
	
	#print all the options
	y = header_height
	letter_index = ord('a')
	for option_text in options:
		text = '(' + chr(letter_index) + ') ' + option_text
		libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
		y += 1
		letter_index += 1
		
	#blit the contents of "window" to the root console
	x = SCREEN_WIDTH/2 - width/2
	y = SCREEN_HEIGHT/2 - height/2
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
	
	#present the root console to the player and wait for a key press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)
	
	#fullscreen
	if key.vk == libtcod.KEY_ENTER and key.lalt: 
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	
	#convert the ASCII code to an index, if it corresponds to an option, return it
	index = key.c - ord('a')
	if index >=0 and index < len(options): return index
	return None
		
def inventory_menu(header):
	#show a menu with each item of the inventory as an option
	if len(inventory) == 0:
		options = ['Inventory is empty.']
	else:
		options = []
		for item in inventory:
			text = item.name
			#show additional information, in case its equipped
			if item.equipment and item.equipment.is_equipped:
				text = text + ' (on ' + item.equipment.slot + ')'
			options.append(text)
		
	index = menu(header, options, INVENTORY_WIDTH)
	
	#if an item was chosen, return it
	if index is None or len(inventory) == 0: return None
	return inventory[index].item
	
def player_death(player):
	#game ended
	global game_state
	message('You are dead', libtcod.red)
	game_state = 'dead'
	
	#transform player into a corpse
	player.char = '%'
	player.color = libtcod.dark_red
	
def monster_death(monster):
	#transform into corpse
	#doesn't block cant attack cant move blah blah blah
	message((monster.name.capitalize() + ' is dead! You gain ' + str(monster.fighter.xp) + 'experience.'), libtcod.orange)
	monster.char = '%'
	monster.color = libtcod.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = 'remains of ' + monster.name
	#set corpse to render first
	monster.send_to_back()
	if dice_roll():
		item = place_random_weapon(monster.x, monster.y)
		objects.append(item)

def dice_roll():
	dice = libtcod.random_get_int(0, 1, 100)
	if dice <= 50:
		message('It seems to have dropped some fat loots.', libtcod.green)
		return True
	else:
		return
		
def closest_monster(max_range):
	#find closest enemy within a max range that is in FOV
	closest_enemy = None
	closest_dist = max_range + 1	#start with (slightly more than) max range
	
	for object in objects:
		if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
			#calculate distance between this object and the player
			dist = player.distance_to(object)
			if dist < closest_dist:	#its closer, so remember it
				closest_enemy = object
				closest_dist = dist
	return closest_enemy

def check_level_up():
	#see if the player's experience is enough to level up
	level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
	if player.fighter.xp >= level_up_xp:
		#level up time
		player.level += 1
		player.fighter.xp -= level_up_xp
		message('Your battle skills have grown! You reached level ' + str(player.level) + '!', libtcod.yellow)
		
		choice = None
		while choice == None: #keep asking untill a choice is made
			choice = menu('Level up! Choose a stat to raise: \n',
				['Constitution (+20 HP, from ' + str(player.fighter.base_max_hp) + ')',
				'Strength (+1 attack, from ' + str(player.fighter.base_power) + ')',
				'Defense (+1 defense, from ' + str(player.fighter.base_defense) + ')'], LEVEL_SCREEN_WIDTH)
				
		if choice == 0:
			player.fighter.base_max_hp += 20
			player.fighter.hp += 20
		elif choice == 1:
			player.fighter.base_power += 1
		elif choice == 2:
			player.fighter.base_defense += 1

def get_equipped_in_slot(slot): #returns the equipment in a slot, or None if it's empty
	for obj in inventory:
		if obj.equipment and (obj.equipment.slot == slot or obj.equipment.slot == 'both hands') and obj.equipment.is_equipped:
			
			return obj.equipment
	return None

def get_all_equipped(obj): #returns a list of equipped items
	if obj == player:
		equipped_list = []
		for item in inventory:
			if item.equipment and item.equipment.is_equipped:
				equipped_list.append(item.equipment)
				
		return equipped_list
	else:
		return [] #other objects have no equipments

	
def cast_heal():
	#heal the player
	if player.fighter.hp == player.fighter.max_hp:
		message('You are already at full health.', libtcod.red)
		return 'cancelled'
		
	message('Youre wounds start to feel better!', libtcod.light_violet)
	player.fighter.heal(HEAL_AMOUNT)
	
def cast_lightning():
	#find closest enemy (inside a max range) and damage it
	monster = closest_monster(LIGHTNING_RANGE)
	if monster is None:	#no enemy found within range
		message('No enemy is close enough to strike', libtcod.red)
		return 'cancelled'
		
	#zap it
	message('A lightning bolt strikes the ' + monster.name + ' with a loud thunder, and damages it for '
			+ str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
	monster.fighter.take_damage(LIGHTNING_DAMAGE)

def cast_confusion():
	#ask player for target
	message('Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan)
	monster = target_monster(CONFUSE_RANGE)
	if monster is None: return 'cancelled'
	#replace monsters AI with a "confused" one and restore after set amount of turns
	old_ai = monster.ai
	monster.ai = ConfusedMonster(old_ai)
	monster.ai.owner = monster #tell the new component who owns it
	message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around', libtcod.light_green)
	
def cast_fireball():
	#ask the player for a target tile
	message('Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = target_tile()
	if x is None: return 'cancelled'
	message('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles', libtcod.orange)
	
	for obj in objects: #damage every fighter in range, including the player
		if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
			message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points.', libtcod.orange)
			obj.fighter.take_damage(FIREBALL_DAMAGE)
			
def create_room(room):
	global map
	#go through the tiles in the rectangle and make them passable
	#python excludes the last element in the loop
	#leave extra space for walls around room
	for x in range(room.x1 + 1, room.x2):
		for y in range (room.y1 + 1, room.y2):
			map[x][y].blocked = False
			map[x][y].block_sight = False
		
def create_h_tunnel(x1,x2,y):
	global map
	for x in range(min(x1,x2), max(x1,x2) + 1):
		map[x][y].blocked = False
		map[x][y].block_sight = False
		
def create_v_tunnel(y1,y2,x):
	global map
	for y in range(min(y1,y2),max(y1,y2) + 1):
		map[x][y].blocked = False
		map[x][y].block_sight = False
	
def is_blocked(x, y):
		#first test the map tile
		if map[x][y].blocked:
			return True
			
		#now check for any blocking objects
		for object in objects:
			if object.blocks and object.x == x and object.y == y:
				return True
		
		return False

#MAP TIME!
def make_map():
	global map, player, objects, stairs
	
	#list of objects with just the player
	objects = [player]
	
	#fill map with "blocked" tiles
	map = [[ Tile(True)
		for y in range(MAP_HEIGHT) ]
			for x in range(MAP_WIDTH)]
			
			
	#MAKE MAP
	rooms = []
	num_rooms = 0
	
	for r in range(MAX_ROOMS):
		#random width and height
		w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		#random position without going out of the boundaries of the map
		x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
		y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
		
		#"rect" class makes rectangles easier to work with
		new_room = Rect(x, y, w, h)
		
		#run through the other rooms and see if they intersect with this one
		failed = False
		for other_room in rooms:
			if new_room.intersect(other_room):
				failed = True
				break
				
		
		if not failed:
			#this means there are no intersections, so this room is valid
			#"paint" it to the map's tiles
			create_room(new_room)
			
			#add some contents to this room
			place_objects(new_room)
			
			#center coordinates of new room, will be useful later
			(new_x, new_y) = new_room.center()
			
			######################################################################
			#OPTIONAL: print "room number" to see how the map drawing worked
			#we may have more than ten rooms, so print with letters
			#room_no = Object(new_x, new_y, chr(65 + num_rooms), 'room number', libtcod.white, always_visible=True)
			#objects.insert(0, room_no) #draw early, so monsters are drawn on top
			#######################################################################
			
			if num_rooms == 0:
				#this is the first room, where the player starts
				player.x = new_x
				player.y = new_y
				
			else:
				#all rooms after the first
				#connect it to the previous room with a tunnel
				
				#center coordinates of previous room
				(prev_x, prev_y) = rooms[num_rooms-1].center()
				#draw a coin (random number that is either 0 or 1
				if libtcod.random_get_int(0,0,1) == 1:
					#first move horizontally, then vertically
					create_h_tunnel(prev_x, new_x, prev_y)
					create_v_tunnel(prev_y, new_y, new_x)
					
				else:
					#first move vertically, then horizontally
					create_v_tunnel(prev_y, new_y, prev_x)
					create_h_tunnel(prev_x, new_x, new_y)
			
			#finally, append the new room to the list
			rooms.append(new_room)
			num_rooms += 1
			
	#create stairs at the center of the last room
	stairs = Object(new_x, new_y, '<', 'stairs', libtcod.white,always_visible=True)
	objects.append(stairs)
	stairs.send_to_back() #so its drawn below the monsters

def from_dungeon_level(table):
	#returns a value that depends on level. the table specifies what value occurs after each level, default is 0
	for(value, level) in reversed(table):
		if dungeon_level >= level:
			return value
	return 0
	
def random_choice_index(chances): #choose one option from the list of chances, returning its index
		#the dice will land on some number between 1 and the sum of the chances
		dice = libtcod.random_get_int(0, 1, sum(chances))
		
		#go through all chances, keeping the sum so far
		running_sum = 0
		choice = 0
		for w in chances:
			running_sum += w
			
			#see if the dice landed in the part that corresponds to this option
			if dice <= running_sum:
				return choice
			choice += 1

def random_choice(chances_dict):
	#choose one option from dictionary of chances, returning its key
	chances = chances_dict.values()
	strings = chances_dict.keys()
	
	return strings[random_choice_index(chances)]
	
def place_objects(room):

	#maximum number of monsters per room
	max_monsters = from_dungeon_level([[2,1], [3,4], [5,6]])
	
	#chance of each monster
	monster_chances = {}
	monster_chances['gnome'] = 80 #orc always shows up, even if all other monsters have 0 chance
	monster_chances['kobold'] = 30
	monster_chances['troll'] = from_dungeon_level([[15,3], [20,5], [35,7]])
	monster_chances['orc'] = from_dungeon_level([[25,2], [40,4], [50,6]])
		
	#choose random number of monsters
	num_monsters = libtcod.random_get_int(0,0, max_monsters)
	
	for i in range(num_monsters):
		#choose random spot for this monster
		x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
		y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)
		
		if not is_blocked(x,y):
			choice = random_choice(monster_chances)
			if choice == 'orc':
				#create an orc
				fighter_component = Fighter(hp=20, defense=0, power=4, xp=35, death_function = monster_death)
				ai_component = BasicMonster()
				
				monster = Object(x,y,'o', 'orc', libtcod.desaturated_green, blocks=True,
								fighter=fighter_component, ai=ai_component)
				
			elif choice == 'troll':
				#create a troll
				fighter_component = Fighter(hp=30, defense=2, power=8, xp=100, death_function = monster_death)
				ai_component = BasicMonster()
				
				monster = Object(x,y,'T', 'troll', libtcod.darker_green, blocks=True,
								fighter=fighter_component, ai=ai_component)
				
			elif choice == 'kobold':
				#create kobold
				fighter_component = Fighter(hp=20, defense=2, power=4, xp=30, death_function = monster_death)
				ai_component = BasicMonster()
				
				monster = Object(x,y,'k', 'kobold', libtcod.darker_blue, blocks=True,
								fighter=fighter_component, ai=ai_component)
				
			elif choice == 'gnome': #40% chance to get gnome
				#create gnome
				fighter_component = Fighter(hp=10, defense =0, power=3, xp=25, death_function = monster_death)
				ai_component = BasicMonster()
				
				monster = Object(x,y,'G', 'gnome', libtcod.dark_magenta, blocks=True,
								fighter=fighter_component, ai=ai_component)
				
			objects.append(monster)
			
	#maximum number of items per room
	max_items = from_dungeon_level([[1,1], [2,4]])
	
	#chances of each item by default chance of 0 at level 1
	item_chances = {}
	item_chances['potion'] = 35 #healing potion always shows up
	item_chances['scroll of lightning'] = from_dungeon_level([[25,4]])
	item_chances['scroll of fireball'] = from_dungeon_level([[25,5]])
	item_chances['scroll of confusion'] = from_dungeon_level([[10,2]])
	#equipment!!
	item_chances['sword'] = from_dungeon_level([[5,1],[10,3],[15,5]])
	item_chances['shield'] =10
	
	num_items = libtcod.random_get_int(0, 0, max_items)
	
	for i in range(num_items):
		#choose random spot for this item
		x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
		y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
		
		#only place if the tile is not blocked
		if not is_blocked(x, y):
			item_choice = random_choice(item_chances)
			
			if item_choice == 'potion':
				item_component = Item(use_function=cast_heal)
				item = Object(x, y, '!', 'healing potion', libtcod.violet, always_visible=True, item=item_component)
				
			elif item_choice == 'scroll of fireball': #10% chance
				item_component = Item(use_function=cast_fireball)
				item = Object(x, y, '#', 'scroll of fireball', libtcod.light_yellow, always_visible=True, item=item_component)
				
			elif item_choice == 'scroll of confusion': #10% chance
				item_component = Item(use_function=cast_confusion)
				item = Object(x, y, '#', 'scroll of confusion', libtcod.light_yellow, always_visible=True, item=item_component)
				
			elif item_choice == 'scroll of lightning':
				#create a lightning bolt scroll
				item_component = Item(use_function=cast_lightning)
				item = Object(x, y, '#', 'scroll of lightning bolt', libtcod.light_yellow, always_visible=True, item=item_component)
			
			elif item_choice == 'sword':
			
				item = place_random_weapon(x,y)
				print 'placed a weapon'
				#create a sword
#				equipment_component = Equipment(slot='right hand', power_bonus=3)
#				item = Object(x, y, '/', 'sword', libtcod.sky, equipment=equipment_component)
				
			elif item_choice == 'shield':
				equipment_component = Equipment(slot='left hand', defense_bonus=2)
				item = Object(x, y, '*', 'shield', libtcod.sky, equipment=equipment_component)
			
			objects.append(item)
			item.send_to_back() #items appear below other objects
			item.always_visible = True

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
	#render a bar. first calculate the width of the bar
	bar_width = int(float(value) / maximum * total_width)
	
	#render the background first
	libtcod.console_set_default_background(panel, back_color)
	libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
	
	#now render the bar on top
	libtcod.console_set_default_background(panel, bar_color)
	if bar_width > 0:
		libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
		
	#centered text with the values
	libtcod.console_set_default_foreground(panel, libtcod.white)
	libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
			name + ': ' + str(value) + '/' + str(maximum))
			
def render_all():
	global color_dark_wall, color_light_wall
	global color_dark_ground, color_light_ground
	global fov_recompute
	
	if fov_recompute:
		#recompute FOV if needed (the player moved or tile changed)
		fov_recompute = False
		libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
	
		#go through all tiles, and set their background color
		for y in range(MAP_HEIGHT):
			for x in range(MAP_WIDTH):
				visible = libtcod.map_is_in_fov(fov_map, x, y)
				wall = map[x][y].block_sight
				if not visible:
					#if it's not visible right now, the player can only see it if it's explored
					if map[x][y].explored:
						#its out of the player's FOV
						if wall:
							libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
						else:
							libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
							
				else:
					# its visible
					if wall:
						libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET)
					else:
						libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
					
					#since its visible, explore it
					map[x][y].explored = True
			
	###draw all objects in the list
	for object in objects:
		if object != player:
			object.draw()
	player.draw()
		
	#blit documentation: http://doryen.eptalys.net/data/libtcod/doc/1.5.1/html2/console_offscreen.html?c=false&cpp=false&cs=false&py=true&lua=false#6
	libtcod.console_blit(con,0,0,MAP_WIDTH, MAP_HEIGHT,0,0,0)
	
	#display GUI
	#prepare to render GUI panel
	libtcod.console_set_default_background(panel, libtcod.black)
	libtcod.console_clear(panel)
	
	#print the game messages, one line at a time
	y = 1
	for(line, color) in game_msgs:
		libtcod.console_set_default_foreground(panel, color)
		libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
		#print line
		y += 1
	
	
	#show the players stats HP
	render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
			libtcod.light_red, libtcod.darker_red)
			
	#show dungeon level counter
	libtcod.console_print_ex(panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon level: ' + str(dungeon_level))
			
	#display names of objects under the mouse
	libtcod.console_set_default_foreground(panel, libtcod.light_gray)
	libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
	
	#blit the contents of "panel" to the root console
	libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)
	
def player_move_or_attack(dx, dy):
	global fov_recompute
	
	#the coordinates the player is moving to/attacking
	x = player.x + dx
	y = player.y + dy
	
	#try to find an attackable object there
	target = None
	for object in objects:
		if object.fighter and object.x == x and object.y == y:
			target = object
			break
	
	# attack if target found, move otherwise
	if target is not None:
		player.fighter.attack(target)
	else:
		player.move(dx, dy)
		fov_recompute = True

def target_tile(max_range=None):
	#return the position of a tile left-clicked in player's FOV (optionally in a range), or (None, None) if right-clicked
	global key, mouse
	while True:
		#render the screen. this erases the inventory and shows the names of objects under the mouse
		libtcod.console_flush()
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
		render_all()
		
		(x, y) = (mouse.cx, mouse.cy)
		
		if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and 
				(max_range is None or player.distance(x, y) <= max_range)):
			return (x, y)
			
		if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
			return (None, None) #cancel if the player right-clicks or presses escape
			
def target_monster(max_range=None):
	#returns a clicked monster inside FOV up to a range or None if right-clicked
	while True:
		(x, y) = target_tile(max_range)
		if x is None: #player cancelled
			return None
		
		#return the first clicked monster, otherwise continue looping
		for obj in objects:
			if obj.x == x and obj.y == y and obj.fighter and obj!= player:
				return obj
				
#key handler
def handle_keys():
	global keys
	global fov_recompute
	
	#key = libtcod.console_check_for_keypress()  for real-time
	#key = libtcod.console_wait_for_keypress(True) #turn based
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#alt+enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	
	elif key.vk == libtcod.KEY_ESCAPE:
		return 'exit' #exit game

	#movement keys only if game_state is playing
	if game_state == 'playing':
		if key.vk == libtcod.KEY_F6:
			player.fighter.xp += 100
		if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
			player_move_or_attack(0, -1)			
		elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
			player_move_or_attack(0, 1)		
		elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
			player_move_or_attack(-1, 0)			
		elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
			player_move_or_attack(1, 0)
		elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
			player_move_or_attack(-1,-1)
		elif key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9:
			player_move_or_attack(1,-1)
		elif key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3:
			player_move_or_attack(1,1)
		elif key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1:
			player_move_or_attack(-1,1)
		elif key.vk == libtcod.KEY_KP5:
			#pass #do nothing/ wait for monster to come to you
			#pick up item if underneath
			for object in objects: #look for item in player's tile
				if object.x == player.x and object.y == player.y and object.item:
					object.item.pick_up()
					break
		
		else: #no key press
			#test for other keys
			key_char = chr(key.c)
			
			if key_char == 'i':
				#print 'pressed i'
				#show the inventory if an item is selected, use it
				chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel. \n')
				if chosen_item is not None:
					chosen_item.use()
					
			if key_char == 'd':
				#print 'pressed d'
				#show the inventory if an item is selected, drop it
				chosen_item = inventory_menu('Press the key next to an item to drop it, or any other key to cancel.\n')
				if chosen_item is not None:
					chosen_item.drop()
			
			if key_char == 'g':
				print 'pressed g'
				#pick up an item
				for object in objects: #look for an item in the player's tile
					if object.x == player.x and object.y == player.y and object.item:
						object.item.pick_up()
						break
			
			if key_char == 'c':
				#print 'pressed c'
				#show character information
				level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
				msgbox('Character Information\n\nLevel: ' + str(player.level) + '\nExperience: ' + str(player.fighter.xp) +
					'\nExperience to level up: ' + str(level_up_xp) + '\n\nMaximum HP: ' + str(player.fighter.max_hp) +
					'\nAttack: ' + str(player.fighter.power) + '\nDefense: ' + str(player.fighter.defense), CHARACTER_SCREEN_WIDTH)
					
			if key_char == ',':
				#debug key
				#go down stairs, if the player is on them
				if stairs.x == player.x and stairs.y == player.y:
					next_level()
			
			return 'turnNotTaken'

def get_names_under_mouse():
	global mouse
	#return a string with the names of all objects under the mouse
	(x,y) = (mouse.cx, mouse.cy)
	
	#create a list of names at the mouse coordinates in FOV
	names = [obj.name.capitalize() for obj in objects
		if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
		
	names = ', '.join(names) #join the names, seperated by commas
	return names

def message(new_msg, color = libtcod.white):
	#split the message if necessary, among multiple lines
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
	
	for line in new_msg_lines:
		#if the buffer is full, remove the first line to make room for the new one
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]
			
		#add the new line as a tuple, with the text and the color
		game_msgs.append( (line, color) )

def next_level():
	global dungeon_level
	#advance to the next level
	message('You take a moment to rest, and recover your strength.', libtcod.light_violet)
	player.fighter.heal(player.fighter.max_hp / 2) #heal for half health
	
	message('After a rare moment of peace, you descend deeper into the heart of the dungeon.', libtcod.red)
	#increment dungeon counter
	dungeon_level += 1
	
	make_map()
	initialize_fov()
	
def new_game():
	global player, inventory, game_msgs, game_state, dungeon_level
	
	#create object representing the player
	fighter_component = Fighter(hp=PLAYER_HEALTH_START, defense=1, power =4, xp=0, death_function = player_death)
	player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)
	
	player.level = 1
	
	#dungeon level counter
	dungeon_level = 1
	
	#generate map (at this point it's not drawn to the screen)
	make_map()
	
	initialize_fov()
	
	game_state = 'playing'
	inventory = []
	#list of game messages and their colors, starts empty
	game_msgs = []
	#welcoming message
	message('Welcome stranger! Prepare to perish in the Tombes of the Ancient Kings.', libtcod.red)
	
	#initial equipment: a dagger
	equipment_component = Equipment(slot='right hand', power_bonus=2)
	obj = Object(0, 0, '-', 'dagger', libtcod.sky, equipment=equipment_component)
	inventory.append(obj)
	equipment_component.equip()
	obj.always_visible = True

def save_game():
	#opens a new empty shelve (possibly overwriting an old one) to write the game data
	file = shelve.open('savegame', 'n')
	file['map'] = map
	file['objects'] = objects
	file['player_index'] = objects.index(player) #index of player in objects list
	file['inventory'] = inventory
	file['game_msgs'] = game_msgs
	file['game_state'] = game_state
	file['stairs_index'] = objects.index(stairs)
	file['dungeon_level'] = dungeon_level
	file.close()
	
def load_game():
	#opens the previously saved shelve and load the game data
	global map, objects, player, inventory, game_msgs, game_state, dungeon_level, stairs
	
	file = shelve.open('savegame','r')
	map = file['map']
	objects = file['objects']
	player = objects[file['player_index']] #get index of player in objects list and access it
	inventory = file['inventory']
	game_msgs = file['game_msgs']
	game_state = file['game_state']
	dungeon_level = file['dungeon_level']
	stairs = objects[file['stairs_index']] #index of stairs
	file.close()
	
	initialize_fov()
	
def msgbox(text, width=50):
	menu(text, [], width) #use menu() as a sort of "message box"
	
def initialize_fov():
	global fov_recompute, fov_map
	fov_recompute = True
	libtcod.console_clear(con)
	
	#set up FOV map list
	fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)
			
def play_game():
	global key, mouse
	player_action = None
	mouse = libtcod.Mouse()
	key = libtcod.Key()
	#main loop
	while not libtcod.console_is_window_closed():
		#print to screen zero is the console to be printed to
		#libtcod.console_set_default_foreground(0, libtcod.crimson)
		#print character
		#libtcod.console_put_char(con,playerx,playery, '@', libtcod.BKGND_NONE)
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key, mouse)
		
		render_all()
		#flush console(present changes to console)
		libtcod.console_flush()
		
		#check for player level up
		check_level_up()
		
		for object in objects:
			object.clear()
			
		#handle keys and exit game if needed
		player_action  = handle_keys()
		if player_action == 'exit':
			save_game()
			break
			
		#let monsters take their turn
		if game_state == 'playing' and player_action != 'turnNotTaken':
			for object in objects:
				if object.ai:
					object.ai.take_turn()
	
def main_menu():
	img = libtcod.image_load('rltutBackdrop.png')
	
	while not libtcod.console_is_window_closed():
		#libtcod.image_blit(img, 0, 0, 0)
		#show the background image at twice the regular console resolution
		libtcod.image_blit_2x(img, 0, 0, 0)
		
		#show game's title and some credits
		libtcod.console_set_default_foreground(0, libtcod.light_yellow)
		libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER,
				MAIN_TITLE)
		libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-2, libtcod.BKGND_NONE, libtcod.CENTER,
			'by Austin McGee')
		#print controls
		libtcod.console_print_ex(0, 1, 1, libtcod.BKGND_NONE, libtcod.LEFT, CONTROLS_TEXT)
		
		#show options and wait for the player's choice
		choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)

		if choice == 0: #new game
			new_game()
			play_game()
			
		if choice == 1: #load last game
			try:
				load_game()
			
			except:
				msgbox('\n No saved game to load.\n', 24)
				continue
			play_game()
		
		elif choice == 2: #quit
			break
	
#initialization and main loop
#load font
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)

#initialize window (width, height, title, fullscreen)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'BEST GAME EVAH', False)
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)

#limit fps for real time --if turn based doesn't matter
libtcod.sys_set_fps(LIMIT_FPS)

#GUI PANEL
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

main_menu()