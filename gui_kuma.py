# based on https://github.com/TheBigKahuna353/Inventory_system and https://github.com/ppizarror/pygame-menu/blob/master/pygame_menu/examples/other/scrollbar.py
import pygame
import pygame_menu
import pygame_gui
from pathlib import Path
from pygame_gui.windows.ui_file_dialog import UIFileDialog, UIConfirmationDialog
from pygame_gui.elements import UIDropDownMenu, UIButton
from pygame.rect import Rect
from pygame_menu.widgets import ScrollBar
import kbd_reader as kbd
import configparser

# read/create settings
settings_file = 'KUMA_settings.ini'
config = configparser.ConfigParser()
if Path(settings_file).is_file():
    config.read(settings_file)
if not config.has_section("CONFIG"):
    config.add_section("CONFIG")
    config.set("CONFIG", "FPS", str(60))
    config.set("CONFIG", "BUTTONS", 'Dualshock 4')
if not config.has_section("PATHS"):
    config.add_section("PATHS")
    config.set("PATHS", "Input", str(Path().resolve()) + '/input_file.kbd')
    config.set("PATHS", "Output", str(Path().resolve()) + '/output_file.kbd')

# initialize pygame stuff
pygame.init()
font = pygame.font.SysFont("Comic-Sans", 18)
clock = pygame.time.Clock()
pygame.display.set_caption('KUMA')



# class for a item, just holds the surface and can resize it


class Item:
    def __init__(self, id, note_type):
        self.id = id
        self.note_type = note_type
        self.surface = items[id]

    def resize(self, size):
        return pygame.transform.scale(self.surface, (size, size))

# the karaoke system


class Karaoke:
    def __init__(self):
        self.rows = 8
        self.col = 2100 #FIXME, notes above 1985 are broken.
        self.items = [[None for _ in range(self.rows)]
                      for _ in range(self.col)]
        self.box_size = 30
        self.x = 50
        self.y = 50
        self.border = 3

    # draw everything
    def draw(self, world, scroll):
        # draw background
        col_start = scroll // (self.box_size + self.border) - 2
        col_end = col_start + 50
        if col_end > self.col:
            col_end = self.col
        pygame.draw.rect(world, (100, 100, 100), (scroll, self.y, (self.box_size + self.border)*col_end + self.border, (self.box_size + self.border)*self.rows + self.border))
        # drawing only the columns we can see, for performance reasons
        for x in range(col_start, col_end):
            for y in range(self.rows):
                rect = (self.x + (self.box_size + self.border)*x + self.border, self.x +
                        (self.box_size + self.border)*y + self.border, self.box_size, self.box_size)
                pygame.draw.rect(world, (180, 180, 180), rect)
                if self.items[x][y]:
                    world.blit(self.items[x][y][0].resize(self.box_size), rect)

    # get the square that the mouse is over
    def Get_pos(self, scroll):
        mouse = pygame.mouse.get_pos()
        x = scroll + mouse[0] - self.x  # adjust for scrollbar
        y = mouse[1] - self.y
        x = x//(self.box_size + self.border)
        y = y//(self.box_size + self.border)
        return (x, y)

    # add an item
    def Add(self, Item, xy):
        x, y = xy
        self.items[x][y] = Item

    # check whether the mouse in in the grid
    def In_grid(self, x, y):  # TODO - clean
        if x < 0:
            return False
        if y < 0:
            return False
        if x >= self.col:
            return False
        if y >= self.rows:
            return False
        return True

def strip_from_sheet(sheet, start, size, columns, rows): #https://python-forum.io/thread-403.html
    frames = []
    for j in range(rows):
        for i in range(columns):
            location = (start[0]+size[0]*i, start[1]+size[1]*j)
            frames.append(sheet.subsurface(pygame.Rect(location, size)))
    return frames

def load_item_tex(button_type, karaoke):
    global items
    #load note textures
    if button_type == 'XBOX':
        tex_name = 'assets/textures/buttons_xbox.png'
    elif button_type == 'Dualshock 4':
        tex_name = 'assets/textures/buttons_ds.png'
    elif button_type == 'Nintendo Switch':
        tex_name = 'assets/textures/buttons_nx.png'
    else:
        print('Invalid type', button_type)
    image = pygame.image.load(tex_name).convert_alpha()
    buttons = strip_from_sheet(image, (0,0), (122,122), 2, 2)
    items = [pygame.Surface((122, 122), pygame.SRCALPHA) for _ in range(6)]
    items[0].blit(buttons[1], (0, 0)) #circle
    items[1].blit(buttons[3], (0, 0)) #cross
    items[2].blit(buttons[2], (0, 0)) #square
    items[3].blit(buttons[0], (0, 0)) #triangle
    pygame.draw.line(items[4], (0, 109, 198), (0, 61), (144, 61), 61)  # hold
    pygame.draw.line(items[5], (198, 0, 99), (0, 61), (144, 61), 61)  # rapid

    for x in range(0, karaoke.col): #change existing button's texture
            for y in range(karaoke.rows):
                if karaoke.items[x][y]:
                    button_id = karaoke.items[x][y][0].id
                    karaoke.items[x][y][0].surface.blit(items[button_id], (0, 0))

# changes scale to 100ms per square


def pos_convert(pos):
    return int(((pos / 3000) * 10))

# converts pos back to yakuza time


def pos_to_game(pos):
    return int((pos / 10) * 3000)


def load_kbd(file, karaoke):
    try:
        data = kbd.read_file(file)
    except(ValueError):
        print('Unable to read file.')
    except(PermissionError):
        print('Unable to open file.')
    else:
        karaoke = Karaoke()  # reset data
        for note in data['Notes']:
            start_pos = pos_convert(note['Start position'])
            karaoke.Add([Item(note['Button type'], note['Note type'])],
                        (start_pos, note['Vertical position']))
            if note['Note type'] != 'Regular':
                end_pos = pos_convert(note['End position'])
                if note['Note type'] == 'Hold':
                    note_id = 4
                else:
                    note_id = 5
                for i in range(start_pos + 1, end_pos):
                    karaoke.Add([Item(note_id, note['Note type'])],
                                (i, note['Vertical position']))
                karaoke.Add([Item(note['Button type'], note['Note type'])],
                            (end_pos, note['Vertical position']))
    return karaoke


def write_kbd(file, karaoke):
    data = dict()
    note_list = list()
    x = 0
    while x < len(karaoke.items):
        y = 0
        while y < len(karaoke.items[x]):
            if karaoke.items[x][y] != None:
                if karaoke.items[x][y][0].id <= 3 and karaoke.items[x][y][0].note_type != 'End':
                    note = dict()
                    note['Start position'] = pos_to_game(x)
                    note['End position'] = 0
                    note['Vertical position'] = y
                    note['Button type'] = karaoke.items[x][y][0].id
                    note['Note type'] = karaoke.items[x][y][0].note_type
                    note['Cue ID'] = 0  # TODO - audio support
                    note['Cuesheet ID'] = 0  # TODO - audio support
                    if karaoke.items[x+1][y] != None:
                        if karaoke.items[x+1][y][0].id > 3:
                            o = x + 1
                            note['Note type'] = karaoke.items[o][y][0].note_type
                            while karaoke.items[o][y][0].id > 3:
                                o += 1
                            karaoke.items[o][y][0].note_type = 'End'
                            note['End position'] = pos_to_game(o)
                    note_list.append(note)
            y += 1
        x += 1
    data['Notes'] = note_list
    data['Header'] = dict()
    data['Header']['Version'] = 2
    kbd.write_file(data, file)
    print('File written to', file)


def update_fps():  # fps counter from https://pythonprogramming.altervista.org/pygame-how-to-display-the-frame-rate-fps-on-the-screen/
    fps = str(int(clock.get_fps()))
    fps_text = font.render(fps, 1, pygame.Color("black"))
    return fps_text


def main():
    controllers = ['Dualshock 4', 'XBOX', 'Nintendo Switch']
    current_controller = config['CONFIG']['BUTTONS']
    scr_size = (1600, 480)
    width_multiplier = 41
    screen = pygame.display.set_mode((scr_size))
    world = pygame.Surface(
        (int(scr_size[0] * width_multiplier), int(scr_size[1])), pygame.SRCALPHA, 32)
    karaoke = Karaoke()
    load_item_tex(current_controller, karaoke) #load button textures
    manager = pygame_gui.UIManager(scr_size)
    file_selection_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 325), (100, 50)),
                                                         text='Open file',
                                                         manager=manager)
    output_selection_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((110, 325), (100, 50)),
                                                           text='Save file',
                                                           manager=manager)
    reset_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((210, 325), (100, 50)),
                                                text='Reset',
                                                manager=manager)
    button_picker = UIDropDownMenu(options_list=controllers,
                              starting_option=current_controller,
                              relative_rect=pygame.Rect(10, 375, 200, 30),
                              manager=manager)

    # Horizontal ScrollBar
    thick_h = 20
    sb_h = ScrollBar(
        length=scr_size[0],
        values_range=(50, world.get_width() - scr_size[0]),
        slider_pad=2,
        page_ctrl_thick=thick_h
    )

    sb_h.set_shadow(
        color=(0, 0, 0),
        position=pygame_menu.locals.POSITION_SOUTHEAST
    )
    sb_h.set_position(0, scr_size[1] - thick_h)
    sb_h.set_page_step(scr_size[0])


    # what the player is holding
    selected = None
    gui_button_mode = None
    note_id = 0  # note that you get when you want to add one, first is circle
    FPS = int(config['CONFIG']['FPS'])
    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------
    while True:
        # Clock tick
        time_delta = clock.tick(FPS) / 1000
        scrollbar_value = sb_h.get_value()
        # draw the screen
        world.fill((169, 149, 154), rect=pygame.Rect(scrollbar_value, 0, 1600, 480))
        karaoke.draw(world, scrollbar_value)

        mousex, mousey = pygame.mouse.get_pos()
        mousex += scrollbar_value  # adjust for scrollbar

        # if holding something, draw it next to mouse
        if selected:
            world.blit(selected[0].resize(20), (mousex, mousey))

        # Application events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                with open(settings_file, 'w') as configfile:  # save config
                    config.write(configfile)
                exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                sb_h.set_value(100)

            sb_h.update([event])
            sb_h.draw(screen)

            if event.type == pygame.MOUSEBUTTONDOWN:
                # if right clicked, get a note
                if event.button == 3:  # right click
                    if selected == None:
                        pass
                    else:
                        if note_id < 3:
                            note_id += 1
                        else:
                            note_id = 0
                    selected = [Item(note_id, 'Regular')]  # add item
                elif event.button == 1:  # left click
                    pos = karaoke.Get_pos(scrollbar_value)
                    if karaoke.In_grid(pos[0], pos[1]):
                        if selected:
                            selected = karaoke.Add(selected, pos)
                        elif karaoke.items[pos[0]][pos[1]]:
                            selected = karaoke.items[pos[0]][pos[1]]
                            karaoke.items[pos[0]][pos[1]] = None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DELETE:
                    selected = None  # deletes selected note
                if event.key == pygame.K_LCTRL:
                    note_id = 4
                    selected = [Item(note_id, 'Hold')]  # add item
                if event.key == pygame.K_LSHIFT:
                    note_id = 5
                    selected = [Item(note_id, 'Rapid')]  # add item

            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    config.set("CONFIG", "BUTTONS", str(
                                button_picker.selected_option))
                    load_item_tex(button_picker.selected_option, karaoke)
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == file_selection_button:
                        gui_button_mode = 'Input'
                        input_selection = UIFileDialog(
                            rect=Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, allow_existing_files_only=True, window_title='Select an input file (kbd)', initial_file_path=Path(config['PATHS']['Input']))
                    if gui_button_mode == 'Input':
                        if event.ui_element == input_selection.ok_button:
                            gui_button_mode = None
                            config.set("PATHS", "Input", str(
                                input_selection.current_file_path))
                            karaoke = load_kbd(
                                input_selection.current_file_path, karaoke)

                    if event.ui_element == output_selection_button:
                        gui_button_mode = 'Output'
                        output_selection = UIFileDialog(
                            rect=Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, window_title='Select an output file (kbd)', initial_file_path=Path(config['PATHS']['Output']))
                    if gui_button_mode == 'Output':
                        if event.ui_element == output_selection.ok_button:
                            gui_button_mode = None
                            config.set("PATHS", "Output", str(
                                output_selection.current_file_path))
                            write_kbd(
                                output_selection.current_file_path, karaoke)

                    if event.ui_element == reset_button:
                        gui_button_mode = 'Reset'
                        reset_all = UIConfirmationDialog(
                            rect=Rect(0, 0, 300, 300), manager=manager, action_long_desc='Are you sure you want to reset? Any unsaved changes will be lost.', window_title='Reset all')
                if event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:  # reset event
                    if gui_button_mode == 'Reset':
                        gui_button_mode = None
                        karaoke = Karaoke()

            manager.process_events(event)

        trunc_world_orig = (scrollbar_value, 0)
        trunc_world = (scr_size[0], scr_size[1] - thick_h)
        screen.blit(world, (0, 0), (trunc_world_orig, trunc_world))
        screen.blit(update_fps(), (10, 0))
        manager.draw_ui(screen)
        manager.update(time_delta)
        pygame.display.update()


if __name__ == '__main__':
    main()
