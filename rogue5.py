import libtcodpy as libtcod

#############################################
# Constants
#############################################
 
# Variables to denote window size in abstract points
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# size of the map viewport

MAP_WIDTH = 80
MAP_HEIGHT = 45 #note this leaves 5 rows at the bottom or top for anything else
 
LIMIT_FPS = 20  #20 frames-per-second maximum

# dungeon generation room parameters
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

# monster generation parameters
MAX_ROOM_MONSTERS = 3

#############################################
# Map class and color definitions
#############################################

color_dark_wall = libtcod.Color(0, 0, 100)
color_dark_ground = libtcod.Color(50, 50, 150)

class Tile:
    #defines behavior for 'blocked' tiles, including FOV properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked
        
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
    def __init__(self, x, y, char, name, color, blocks=False):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks

    # utilize the move method to delineate movement of an Object        
    def move(self, dx, dy): 
        # checks to permit movement if no blocked tiles ahead.
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
    
    # utilize the draw method to actually display the Object to the buffer console
    def draw(self): 
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
        
    # utilize the clear method to remove the Object from the buffer console
    def clear(self):
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

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
    global map
    
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
                monster = Object(x, y, 'h', 'human', libtcod.green, blocks=True)
            elif choice < 20+40:
                monster = Object(x, y, 'o', 'orc', libtcod.green, blocks=True)
            elif choice < 20+40+10:
                monster = Object(x, y, 'd', 'dragon', libtcod.green, blocks=True)
            else:
                monster = Object(x, y, 'T', 'troll', libtcod.green, blocks=True)
                            
            objects.append(monster)
        
#############################################
# draw all objects in the list and map tiles
#############################################

#utilize the earlier draw method to draw all objects in the list
def render_all():
    for object in objects:
        object.draw()
        
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            wall = map[x][y].block_sight
            if wall:
                libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
            else:
                libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)    

    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0) # display buffer 'con' information to the main terminal window
     
#############################################
# In-game key commands 
#############################################
 
def handle_keys():
    global playerx, playery
 
    #key = libtcod.console_check_for_keypress()  #real-time
    key = libtcod.console_wait_for_keypress(True)  #turn-based
 
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
    elif key.vk == libtcod.KEY_ESCAPE:
        return True  #exit game
 
    # Movement keys by arrows.
    if libtcod.console_is_key_pressed(libtcod.KEY_UP): #north
        player.move(0, -1)
  
    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN): #south
        player.move (0, 1)
  
    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT): #west
        player.move (-1, 0)
 
    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT): #east
        player.move (1, 0) 
 
#############################################
# Initialization
#############################################
 
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD) # game font
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False) # create the game window (not fullscreen)
libtcod.sys_set_fps(LIMIT_FPS)

# Initialize objects
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT) #creates an offscreen buffer called 'con'

player = Object(0, 0, '@', 'player', libtcod.white, blocks=True)

objects = [player] #does it actually matter which order the entities are loaded in?

# Make the map
make_map()
 
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
    exit = handle_keys()
    if exit:
        break