import libtcodpy as libtcod
 
# test commit comment
# Variables to denote window size in abstract points
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# size of the map viewport

MAP_WIDTH = 80
MAP_HEIGHT = 45 #note this leaves 5 rows at the bottom or top for anything else
 
LIMIT_FPS = 20  #20 frames-per-second maximum

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
# actually creates the visible map.
#############################################

def make_map():
    global map
    
    #fill map with unblocked tiles
    map = [[ Tile(False)
           for y in range(MAP_HEIGHT) ]
                for x in range(MAP_WIDTH) ]
    
    #create two pillars
    map[30][22].blocked = True
    map[30][22].block_sight = True
    map[50][22].blocked = True
    map[50][22].block_sight = True
    
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

npc = Object(SCREEN_WIDTH/2 - 5, SCREEN_HEIGHT/2, '@', libtcod.red)

objects = [npc, player] #does it actually matter which order the entities are loaded in?

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