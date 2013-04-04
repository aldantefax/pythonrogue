import libtcodpy as libtcod
 
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
 
 
########################################################################################## 
# OBJECTS
# General object class for entities. This is a generic class for any
# object that has a presence on the screen and requires a symbol.
##########################################################################################  
 
class Object:
    def __init__(self, x, y, char, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    # utilize the move method to delineate movement of an Object        
    def move(self, dx, dy): 
        # checks to permit movement if no blocked tiles ahead.
        if not map[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy
    
    # utilize the draw method to actually display the Object to the buffer console
    def draw(self): 
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
        
    # utilize the clear method to remove the Object from the buffer console
    def clear(self):
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

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
# DUNGEON GENERATOR
# generates rooms and hallways to connect to those rooms.
#############################################

def center(self):
    center_x = (self.x1 + self.x2) / 2
    center_y = (self.y1 + self.y2) / 2
    return (center_x, center_y)

def intersect(self, other):
    return(self.x1 <= other.x2 and self.x2 >= other.x1 and
           self.y1 <= other.y2 and self.y2 >= other.y1)

       
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
    
    #create two rooms
    room1 = Rect(20, 15, 10, 15)
    room2 = Rect(50,15,10,15)
    create_room(room1)
    create_room(room2)
    
    #create a hallway to join the two rooms
    create_h_tunnel(25, 55, 23)
    
    # put the player into the room on the left.
    player.x = 25
    player.y = 23
    
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

player = Object(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, '@', libtcod.white)

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