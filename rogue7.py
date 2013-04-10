import libtcodpy as libtcod
import math

#############################################
# Constants
#############################################
 
# Variables to denote window size in abstract points
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# size of the map viewport

MAP_WIDTH = 80
MAP_HEIGHT = 43 #leaves 7 lines at the bottom (5+2 padding) for status bars and text displays, etc
 
LIMIT_FPS = 20  #20 frames-per-second maximum

# dungeon generation room parameters
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

# monster generation parameters
MAX_ROOM_MONSTERS = 3

# Field of View constants
FOV_ALGO = 0 #use the default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# Status Bar constants
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

#############################################
# Map class and color definitions
#############################################

# dark or unlit tiles
color_dark_wall = libtcod.Color(0, 0, 100)
color_dark_ground = libtcod.Color(50, 50, 150)

# light or lit tiles (ha, ha)
color_light_wall = libtcod.Color(130,110, 50)
color_light_ground = libtcod.Color (200, 180, 50)

class Tile:
    #defines behavior for 'blocked' tiles, including FOV properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked
        
        #initialize all tiles as unexplored!
        self.explored = False
        
        # if a tile is blocked it also blocks sight using the following code        
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight
        
#############################################
# Room creation - Rectangular Rooms
#############################################        

class Rect:
        #a rectangle on the map. Used to define a room.
        def __init__(self, x, y, w, h):
            # room position 1 - where is this located on the map starting from the top left corner
            self.x1 = x
            self.y1 = y
            # room size - where is the bottom right corner of the room
            self.x2 = x + w #defines room horizontal length (w - width)
            self.y2 = y + h #defines room vertical length (h - height)
            
        def center(self):
            center_x = (self.x1 + self.x2) / 2
            center_y = (self.y1 + self.y2) / 2
            return (center_x, center_y)

        def intersect(self, other):
            return(self.x1 <= other.x2 and self.x2 >= other.x1 and
                   self.y1 <= other.y2 and self.y2 >= other.y1)

 
 
########################################################################################## 
# OBJECTS
# General object class for entities. This is a generic class for any
# object that has a presence on the screen and requires a symbol.
##########################################################################################  
 
class Object:
    def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks
        
        self.fighter = fighter
        if self.fighter: # let the fighter component know who owns it
            self.fighter.owner = self
            
        self.ai = ai
        if self.ai: # let the AI component know who knows it
            self.ai.owner = self

    # utilize the move method to delineate movement of an Object        
    def move(self, dx, dy): 
        # checks to permit movement if no blocked tiles ahead.
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    # movement AI - basically, "if you see a player, chase him"
    def move_towards(self, target_x, target_y):
        #calculate vector from this object to the target and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        
        #normalize the calculations above to length 1
        #also round then convert to whole integer to prevent OOB movement
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)
    
    #return the distance to another object, handy for a variety of things
    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
    
    # utilize the draw method to actually display the Object to the buffer console
    def draw(self): 
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
            
    # utilize the clear method to remove the Object from the buffer console
    def clear(self):
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)
        
    def send_to_back(self):
        #draw this object first so all others appear above it if they occupy the same tile
        global objects
        objects.remove(self)
        objects.insert(0, self)

class Fighter:
    # combat statistics for monsters, players, and NPCs
    def __init__(self, hp, defense, power, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function
    
    #damage routine
    def take_damage(self, damage):
        #if there's any damage to apply do it
        if damage > 0:
            self.hp -= damage
            
            if self.hp <= 0:
                function = self.death_function
                if function is not None:
                    function(self.owner)
            
    #attack routine
    def attack(self, target):
        damage = self.power - target.fighter.defense
        
        if damage > 0:
            choice = libtcod.random_get_int(0, 0, 100)
            if choice < 20:
                print self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.'
                target.fighter.take_damage(damage)
            elif choice < 20+20:
                print self.owner.name.capitalize() + ' swings ' + target.name + ' for ' + str(damage) + ' hit points.'
                target.fighter.take_damage(damage)
            elif choice < 20+20+20:
                print self.owner.name.capitalize() + ' bashes ' + target.name + ' for ' + str(damage) + ' hit points.'
                target.fighter.take_damage(damage)
            elif choice < 20+20+20+20:
                print self.owner.name.capitalize() + ' clobbers ' + target.name + ' for ' + str(damage) + ' hit points.'
                target.fighter.take_damage(damage)
            else:
                print self.owner.name.capitalize() + ' smashes ' + target.name + ' for ' + str(damage) + ' hit points.'
                target.fighter.take_damage(damage)
        else: 
            print self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!'

class BasicMonster:
    # AI for a basic monster.
    def take_turn(self):
        #a basic monster takes its turn when in FOV only
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            #move towards player if far away
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)
        

##########################################################################################
# Blocked Tile Logic
# This checks to see if a map tile is blocked by a wall, then by any object.
# This is probably going to be pretty useful later on for collision detection!
##########################################################################################

def is_blocked(x, y):
    if map[x][y].blocked:
        return True
    
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True
        
    return False

############################################# 
# dungeon creation routines
# using x/y + 1 it will ensure there is a separating wall!
#############################################

# creates rectangular rooms

def create_room(room):
    global map
    for x in range(room.x1 + 1, room.x2): #note that the +1 will help the range offset for this loop
            for y in range(room.y1 + 1, room.y2):
                map[x][y].blocked = False
                map[x][y].block_sight = False

# create horizontal hallways
                
def create_h_tunnel(x1, x2, y): 
    global map
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False

# create vertical hallways

def create_v_tunnel(y1, y2, x):
    global map
    for y in range(min(y1, y2), max(y1, y2) +1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
        
############################################# 
# MAP DISPLAY:
# actually creates the visible map.
#############################################

def make_map():
    global map, player
    
    #fill map with unblocked tiles
    map = [[ Tile(True)
           for y in range(MAP_HEIGHT) ]
                for x in range(MAP_WIDTH) ]
    
    # populate the viewport with rooms.
    
    rooms = [] #container for all these rooms that get generated
    num_rooms = 0 # initialize the number of rooms to 0
    
    for r in range(MAX_ROOMS): #as long as there are less than 30 rooms, do this.
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE) #room width
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE) #room height
        #generate a random position without going out of the boundaries of the map.
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
        
        #load Rect class to make the above variable easier to handle
        new_room = Rect(x, y, w, h)
        
        #room sanity check - does any other room intersect this one?
        failed = False
        for other_room in rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break
                
        if not failed:
            # if there's no other rooms colliding with this one to intersect, keep going...
            
            # actually generate the room.
            create_room(new_room)
            
            # plop new objects in. for module 5, these are monsters!
            place_objects(new_room)
            
            #determine center coords of this room.
            (new_x, new_y) = new_room.center()
            
            #generate room number to show how the generation system works.
            room_no = Object(new_x, new_y, chr(65+num_rooms), 'room number', libtcod.white)
            objects.insert(0, room_no) #draw the room numbers before drawing other elements
            
            #this slaps the player into the center of the first room generated.
            if num_rooms == 0:
                player.x = new_x
                player.y = new_y
                
            #otherwise keep going to create the remaining rooms with the following instructions...
            else:
                # connect to the previous room that was generated with a tunnel
                (prev_x, prev_y) = rooms[num_rooms-1].center()
                
                #flip a coin to determine if the hallway generated is vertical or horizontal.
                # 1 is heads, 0 is tails. i THINK the choices presented are either
                # 50/50 or 66/33 favoring vertical tunnels
                if libtcod.random_get_int(0, 0, 1) == 1:
                    #horizontal then vertical
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                
                else:
                    #vertical then horizontal
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
                    
            # add the room to the room bucket and increase the room count for generation purposes.
            rooms.append(new_room)
            num_rooms += 1
            
#############################################
# Monster Generation
# Remember that monsters are a subset of objects.
#############################################

def place_objects(room):
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)
    
    for i in range(num_monsters):
        #pick a random location for object generation
        x = libtcod.random_get_int(0, room.x1, room.x2)
        y = libtcod.random_get_int(0, room.y1, room.y2)
        
        #uses option b to create 4 monster entities based on 20/40/10/30% distribution
        #checks to see if a tile is blocked. if not, step into these choices:
        if not is_blocked(x, y):
            choice = libtcod.random_get_int(0, 0, 100)
            if choice < 20:
                fighter_component = Fighter(hp=10, defense=0, power=3, death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'h', 'human', libtcod.desaturated_green, blocks=True, fighter=fighter_component, ai=ai_component)
            elif choice < 20+40:
                fighter_component = Fighter(hp=15, defense=0, power=4, death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'o', 'orc', libtcod.orange, blocks=True, fighter=fighter_component, ai=ai_component)
            elif choice < 20+40+10:
                fighter_component = Fighter(hp=20, defense=0, power=5, death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'd', 'dragon', libtcod.red, blocks=True, fighter=fighter_component, ai=ai_component)
            else:
                fighter_component = Fighter(hp=25, defense=0, power=6, death_function=monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, 'T', 'troll', libtcod.green, blocks=True, fighter=fighter_component, ai=ai_component)
                            
            objects.append(monster)

    
#############################################
# draw all objects in the list and map tiles
#############################################

#utilize the earlier draw method to draw all objects in the list
def render_all():
    
    #declare global variables in this function
    global fov_map, color_dark_wall, color_dark_ground
    global color_light_wall, color_light_ground
    global fov_recompute
    
    # recompute the FOV if fov_recompute is flagged as True
    if fov_recompute:
    
        fov_recompute = False # reset fov_recompute as False to prevent infinite recompute loop
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
        
        #this determines if something is or is not visible.
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = map[x][y].block_sight
                
                if not visible:
                    if map[x][y].explored:
                        #that means it's INVISIBLE, ha ha
                        if wall:
                            libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
                else:
                    #you can see it.
                    if wall:
                        libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
                    map[x][y].explored = True
    
    #draw all objects in list except player, then draw player
    for object in objects:
        if object != player:
            object.draw()
    player.draw()

    # display buffer 'con' information to the main terminal window    
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0) 
    
    #show player's stats - changed in module 7
    
    #prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
    
    #show player HP - make it pretty
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)
    
    # display the 'panel' offscreen console to the visible root console
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y) 
    
############################################# 
# Combat Routines
#############################################

def player_move_or_attack(dx, dy):
    global fov_recompute
    x = player.x + dx
    y = player.y + dy
    
    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break
    
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True
     
#############################################
# In-game key commands 
#############################################
 
def handle_keys():
    global fov_recompute
 
    #key = libtcod.console_check_for_keypress()  #real-time
    key = libtcod.console_wait_for_keypress(True)  #turn-based
 
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit' #exit game
 
    if game_state =='playing':
        # Movement keys by arrows.
        # New for module 4: fov_recompute will force a recalculation every movement.
        if libtcod.console_is_key_pressed(libtcod.KEY_UP): #north
            player_move_or_attack (0, -1)
            fov_recompute = True
      
        elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN): #south
            player_move_or_attack (0, 1)
            fov_recompute = True
      
        elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT): #west
            player_move_or_attack (-1, 0)
            fov_recompute = True
     
        elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT): #east
            player_move_or_attack (1, 0)
            fov_recompute = True
        else:
            return 'didnt-take-turn'
        
def player_death(player):
    #game over
    global game_state
    print 'You died!'
    game_state = 'dead'
    # turn player into a corpse
    player.char = '%'
    player.color = libtcod.dark_red
    
def monster_death(monster):
    # monster turns into a corpse that doesn't block/attack/move
    print monster.name.capitalize() + ' is dead.'
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = 'remains of ' + monster.name
    monster.send_to_back()
 
#############################################
# Initialization
#############################################
 
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD) # game font
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Module 7 - The GUI', False) # create the game window (not fullscreen)
libtcod.sys_set_fps(LIMIT_FPS)

# Initialize objects
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT) #creates an offscreen buffer called 'con'

#create object representing the player
fighter_component = Fighter(hp=30, defense=2, power=5, death_function=player_death)
player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)

objects = [player] #does it actually matter which order the entities are loaded in?

# Make the map
make_map()
 
# Generate a FOV map (also covers pathfinding visibility for a later module)
fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
        libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked) 

#force the initial rendering of field of view.
fov_recompute = True 

game_state = 'playing'
player_action = None

#############################################
# Status Bars
#############################################

panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

#render a bar (generic - could be HP, EXP, etc)
def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    #calculate width
    bar_width = int(float(value) / maximum * total_width)
    
    #render bar background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
    
    #render the bar on top of the background
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
        
    #add centered text labels to the bar
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER, 
                             name + ': ' + str(value) + '/' + str(maximum))
    

#############################################
# MAIN LOOP
#############################################

while not libtcod.console_is_window_closed():
    
    # render the screen via this function
    render_all()
    
    libtcod.console_flush()

    #utilize the clear method to remove objects from their old locations
    for object in objects:
        object.clear()

    #handle keys and exit game if needed
    player_action = handle_keys()
    if player_action == 'exit':
        break
    
    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for object in objects:
            #if object != player:
                #print 'The ' + object.name + ' barfs!'
            if object.ai:
                object.ai.take_turn() 