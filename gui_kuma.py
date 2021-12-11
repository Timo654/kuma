# based on https://github.com/TheBigKahuna353/Inventory_system and https://github.com/ppizarror/pygame-menu/blob/master/pygame_menu/examples/other/scrollbar.py
import pygame
from pygame_gui import UIManager, UI_BUTTON_START_PRESS, UI_BUTTON_PRESSED, UI_DROP_DOWN_MENU_CHANGED, UI_CONFIRMATION_DIALOG_CONFIRMED
from pygame_gui.windows import UIFileDialog, UIConfirmationDialog, UIMessageWindow
from pygame_gui.elements import UIDropDownMenu, UILabel, UIButton, UITextEntryLine, UIHorizontalSlider
import modules.kbd_reader as kbd
from modules.ui_menu_bar import UIMenuBar
from pathlib import Path
from math import ceil, floor
import json
import configparser

asset_file = 'assets.json'
if Path(asset_file).is_file():
    with open(asset_file, 'r') as json_file:
        assets = json.load(json_file)
else:
    raise Exception('Asset data missing')

texture_path = assets['Texture folder']
controllers = [key for key in assets['Button prompts']]

# read/create settings
settings_file = 'KUMA_settings.ini'
config = configparser.ConfigParser()
if Path(settings_file).is_file():
    config.read(settings_file)
if not config.has_section("CONFIG"):
    config.add_section("CONFIG")
    config.set("CONFIG", "FPS", str(60))
    config.set("CONFIG", "BUTTONS", controllers[0])
if not config.has_section("PATHS"):
    config.add_section("PATHS")
    config.set("PATHS", "Input", str(Path().resolve()) + '\\input_file.kbd')
    config.set("PATHS", "Output", str(Path().resolve()) + '\\output_file.kbd')

# initialize pygame stuff
pygame.init()
font = pygame.font.SysFont("FiraCode", 22)
clock = pygame.time.Clock()
pygame.display.set_caption('KUMA')


# class for a item, just holds the surface and can resize it


class Item:
    # default end pos, cue id and cuesheet id is 0
    def __init__(self, x, y, id, note_type, start_pos, end_pos=0, cue_id=0, cuesheet_id=0):
        self.id = id
        self.note_type = note_type
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.cue_id = cue_id
        self.cuesheet_id = cuesheet_id
        self.surface = items[id]
        self.x = x
        self.y = y

    def resize(self, size):
        return pygame.transform.scale(self.surface, (size, size))

    def note_type_to_int(self):
        note_list = ['Regular', 'Hold', 'Rapid', 'End']
        return note_list.index(self.note_type)

# the karaoke system


class Karaoke:
    def __init__(self):
        self.rows = 8
        self.col = 3966
        self.items = [[None for _ in range(self.rows)]
                      for _ in range(self.col)]
        self.box_size = 30
        self.x = 50
        self.y = 50
        self.scale = 10  # 1/10 second, so 100 ms per square
        self.border = 3

    # draw everything
    def draw(self, world, surface_nr, scroll, screen_width, sheet_bg, line_bg):
        # draw background
        surface2_offset = 0
        one_box = self.box_size + self.border
        if surface_nr == 2:
            x_coord = 0
            scroll -= world.get_width() - 50
            surface2_offset = int(self.col / 2)
        else:
            x_coord = self.x

        col_start = (scroll // one_box - 2)
        col_end = col_start + (screen_width // one_box) + 2
        if surface_nr == 2:
            col_end += 2
        if col_end > (self.col // 2):
            col_end = (self.col // 2)

        for i in range(col_start, col_end):
            world.blit(sheet_bg, (x_coord + (33 * (i)),
                                  self.y + self.box_size / 2))
            if (i + surface2_offset) % 20 == 0:
                current_time = self.format_time(i + surface2_offset)
                time_text = font.render(current_time, 1, pygame.Color("grey"))
                world.blit(time_text, (x_coord + (33 * (i)), 30))
                world.blit(
                    line_bg, (x_coord + (one_box // 2) + (33 * (i)), self.y + self.box_size / 2))
        for x in range(col_start, col_end):
            for y in range(self.rows):
                rect = (x_coord + (self.box_size + self.border)*x + self.border, self.x +
                        (self.box_size + self.border)*y + self.border, self.box_size, self.box_size)
                if self.items[x + surface2_offset][y]:
                    world.blit(self.items[x + surface2_offset]
                               [y].resize(self.box_size), rect)

    def format_time(self, i):
        # display current time, 100 ms each square
        seconds = i // self.scale
        minutes = seconds // 60
        if minutes:
            if seconds % 60 == 0:
                return f'{minutes} min'
            else:
                return f'{minutes} min {seconds - (minutes * 60)} s'
        else:
            return f'{seconds} s'

    # get the square that the mouse is over
    def Get_pos(self, scroll):
        mouse = pygame.mouse.get_pos()
        x = scroll + mouse[0] - self.x  # adjust for scrollbar
        y = mouse[1] - self.y
        # 1000 comes from testing
        if x > int(((self.col * self.box_size) + (self.col + self.border)) / 2) + 1000:
            x -= 15
        x = x//(self.box_size + self.border)
        y = y//(self.box_size + self.border)
        return (x, y)

    def pos_convert(self, pos):
        return normal_round(((pos / 3000) * self.scale))

    # converts pos back to yakuza time

    def pos_to_game(self, pos):
        return normal_round((pos / self.scale) * 3000)

    # add an item
    def Add(self, Item):
        self.items[Item.x][Item.y] = Item

    def Remove(self, x, y):
        self.items[x][y] = None

    # check whether the mouse in in the grid
    def In_grid(self, x, y):
        if (x < 0) or (y < 0) or (x >= self.col) or (y >= self.rows):
            return False
        return True


def int_to_note_type(i):
    note_list = ['Regular', 'Hold', 'Rapid', 'End']
    return note_list[i]

# https://python-forum.io/thread-403.html


def strip_from_sheet(sheet, start, size, columns, rows):
    frames = []
    for j in range(rows):
        for i in range(columns):
            location = (start[0]+size[0]*i, start[1]+size[1]*j)
            frames.append(sheet.subsurface(pygame.Rect(location, size)))
    return frames


def load_item_tex(button_type, karaoke, selected, dropdown):
    global items
    # load note textures
    tex_name = texture_path + '\\' + assets['Button prompts'][button_type][0]
    image = pygame.image.load(tex_name).convert_alpha()
    buttons = strip_from_sheet(image, (0, 0), (122, 122), 2, 2)
    items = [pygame.Surface((122, 122), pygame.SRCALPHA) for _ in range(6)]
    items[0].blit(buttons[1], (0, 0))  # circle
    items[1].blit(buttons[3], (0, 0))  # cross
    items[2].blit(buttons[2], (0, 0))  # square
    items[3].blit(buttons[0], (0, 0))  # triangle
    pygame.draw.line(items[4], (0, 109, 198), (0, 61), (144, 61), 61)  # hold
    pygame.draw.line(items[5], (198, 0, 99), (0, 61), (144, 61), 61)  # rapid

    for x in range(0, karaoke.col):  # change existing button's texture
        for y in range(karaoke.rows):
            if karaoke.items[x][y]:
                button_id = karaoke.items[x][y].id
                karaoke.items[x][y].surface = items[button_id]

    if selected:
        selected.surface = items[selected.id]

    update_dropdown(dropdown, mode='update all', new_list=assets['Button prompts']
                    [button_type][1], index=dropdown.options_list.index(dropdown.selected_option))


def normal_round(n):  # https://stackoverflow.com/questions/33019698/how-to-properly-round-up-half-float-numbers
    if n - floor(n) < 0.5:
        return floor(n)
    return ceil(n)


def game_to_ms(pos):
    return float(pos / 3)


def ms_to_game(pos):
    return normal_round(pos * 3)


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
            start_pos = karaoke.pos_convert(note['Start position'])
            karaoke.Add(Item(start_pos, note['Vertical position'], note['Button type'], note['Note type'],
                             note['Start position'], end_pos=note['End position'], cue_id=note['Cue ID'], cuesheet_id=note['Cuesheet ID']))
            if note['Note type'] != 'Regular':
                end_pos = karaoke.pos_convert(note['End position'])
                if note['Note type'] == 'Hold':
                    note_id = 4
                else:
                    note_id = 5
                progress_value = 0
                for i in range(start_pos + 1, end_pos):
                    progress_value += 100
                    karaoke.Add(Item(i, note['Vertical position'], note_id,
                                     note['Note type'], note['Start position'] + progress_value))
                karaoke.Add(Item(
                    end_pos, note['Vertical position'], note['Button type'], 'End', note['End position']))
    return karaoke


def write_kbd(file, karaoke):
    data = dict()
    note_list = list()
    x = 0
    while x < len(karaoke.items):
        y = 0
        while y < len(karaoke.items[x]):
            if karaoke.items[x][y] != None:
                if karaoke.items[x][y].id <= 3 and karaoke.items[x][y].note_type != 'End':
                    current_note = karaoke.items[x][y]
                    note = dict()
                    note['Start position'] = current_note.start_pos
                    note['End position'] = 0
                    note['Vertical position'] = y
                    note['Button type'] = current_note.id
                    note['Note type'] = current_note.note_type
                    note['Cue ID'] = current_note.cue_id
                    note['Cuesheet ID'] = current_note.cuesheet_id
                    if current_note.end_pos > 0:
                        note['End position'] = current_note.end_pos
                    else:
                        if karaoke.items[x+1][y] != None:
                            if karaoke.items[x+1][y].id > 3:
                                o = x + 1
                                note['Note type'] = karaoke.items[o][y].note_type
                                while karaoke.items[o][y].id > 3:
                                    o += 1
                                karaoke.items[o][y].note_type = 'End'
                                note['End position'] = karaoke.pos_to_game(o)
                                current_note.end_pos = note['End position']
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
    return fps


def update_text_boxes(note, boxes, dropdowns):
    # set values
    boxes[0].set_text(str(game_to_ms(note.start_pos)))
    boxes[1].set_text(str(game_to_ms(note.end_pos)))
    boxes[2].set_text(str(note.y))
    boxes[3].set_text(str(note.cue_id))
    boxes[4].set_text(str(note.cuesheet_id))
    update_dropdown(dropdowns[0], mode='update selection', index=note.id)
    update_dropdown(dropdowns[1], mode='update selection',
                    index=note.note_type_to_int())


def save_before_closing(note, boxes, dropdowns, karaoke):
    # TODO - clean
    if len(boxes[0].get_text()) > 0:
        new_pos = ms_to_game(float(boxes[0].get_text()))
        if karaoke.pos_convert(new_pos) <= len(karaoke.items):
            note.start_pos = new_pos
            karaoke.items[note.x][note.y] = None
            note.x = karaoke.pos_convert(note.start_pos)
            karaoke.items[note.x][note.y] = note
    if len(boxes[2].get_text()) > 0:
        if int(boxes[2].get_text()) < karaoke.rows:
            karaoke.items[note.x][note.y] = None
            note.y = int(boxes[2].get_text())
            karaoke.items[note.x][note.y] = note
    if len(boxes[3].get_text()) > 0:
        note.cue_id = int(boxes[3].get_text())
    if len(boxes[4].get_text()) > 0:
        note.cuesheet_id = int(boxes[4].get_text())
    note.id = dropdowns[0].options_list.index(dropdowns[0].selected_option)
    note.note_type = dropdowns[1].selected_option
    note.surface = items[note.id]

    if len(boxes[1].get_text()) > 0:
        if note.note_type != 'Regular':
            end_pos = ms_to_game(float(boxes[1].get_text()))
            if end_pos < note.end_pos:
                old_end_pos = karaoke.pos_convert(note.end_pos)
                new_end_pos = karaoke.pos_convert(end_pos)
                start_pos = karaoke.pos_convert(note.start_pos)
                for i in range(old_end_pos + 1, new_end_pos, -1):
                    if i == start_pos:
                        break
                    karaoke.Remove(i, note.y)

            if end_pos > note.start_pos:
                note.end_pos = end_pos
                start_pos = karaoke.pos_convert(note.start_pos)
                end_pos = karaoke.pos_convert(note.end_pos)
                if note.note_type == 'Hold':
                    note_id = 4
                else:
                    note_id = 5
                progress_value = 0
                for i in range(start_pos + 1, end_pos):
                    progress_value += 100
                    karaoke.Add(Item(i, note.y, note_id,
                                     note.note_type, note.start_pos + progress_value))

                karaoke.Add(
                    Item(end_pos, note.y, note.id, 'End', note.end_pos))
            else:
                note.end_pos = 0


# new_list is a list and option is list index
def update_dropdown(dropdown, mode, new_list=list(), index=0):
    if mode == 'update all':
        dropdown.options_list = new_list
        dropdown.menu_states['expanded'].options_list = new_list
        dropdown.menu_states['expanded'].rebuild()
    if (mode == 'update selection') or (mode == 'update all'):
        option = dropdown.options_list[index]
        dropdown.selected_option = option
        dropdown.menu_states['closed'].selected_option = option
        dropdown.menu_states['closed'].finish()
        dropdown.menu_states['closed'].start()
    dropdown.rebuild()


def stop_editing(boxes, box_labels, dropdowns, undo_button):
    for box in boxes:
        box.hide()  # disable text boxes
        for label in box_labels:
            label.hide()
        for dropdown in dropdowns:
            dropdown.hide()
        undo_button.hide()


def main():
    current_controller = config['CONFIG']['BUTTONS']
    if current_controller not in controllers:
        current_controller = controllers[0]
    scr_size = (1600, 480)
    screen = pygame.display.set_mode((scr_size))
    karaoke = Karaoke()
    # FIXME - some notes overflow to the start, minor visual issue.
    accurate_size = (4 + karaoke.col) * (karaoke.box_size + karaoke.border)
    world = pygame.Surface(
        (int(accurate_size / 2), int(scr_size[1])), pygame.SRCALPHA, 32)
    world2 = pygame.Surface(
        (accurate_size - world.get_width(), int(scr_size[1])), pygame.SRCALPHA, 32)

    # menu bar from https://github.com/MyreMylar/pygame_paint
    manager = UIManager(scr_size, theme_path='assets/ui_theme.json')
    menu_data = {'#file_menu': {'display_name': 'File',
                                'items':
                                {
                                    '#new': {'display_name': 'New...'},
                                    '#open': {'display_name': 'Open...'},
                                    '#save': {'display_name': 'Save'},
                                    '#save_as': {'display_name': 'Save As...'}
                                }
                                },
                 '#help_menu': {'display_name': 'Help',
                                    'items':
                                        {
                                            '#how_to_use': {'display_name': 'How to use'},
                                            '#about': {'display_name': 'About'}
                                        }
                                }
                 }
    menu_bar = UIMenuBar(relative_rect=pygame.Rect(0, 0, scr_size[0], 25),
                         menu_item_data=menu_data,
                         manager=manager)

    undo_button = UIButton(relative_rect=pygame.Rect((315, 395), (200, 50)),
                           text='Undo note changes',
                           manager=manager)
    undo_button.hide()
    button_picker = UIDropDownMenu(options_list=controllers,
                                   starting_option=current_controller,
                                   relative_rect=pygame.Rect(10, 390, 200, 30),
                                   manager=manager)

    start_label = UILabel(pygame.Rect((315, 340), (150, 22)),
                          "Start position",
                          manager=manager)
    end_label = UILabel(pygame.Rect((470, 340), (150, 22)),
                        "End position",
                        manager=manager)
    vert_label = UILabel(pygame.Rect((625, 340), (150, 22)),
                         "Vertical position",
                         manager=manager)
    cue_label = UILabel(pygame.Rect((780, 340), (150, 22)),
                        "Cue ID",
                        manager=manager)
    cuesheet_label = UILabel(pygame.Rect((935, 340), (150, 22)),
                             "Cuesheet ID",
                             manager=manager)
    note_button_label = UILabel(pygame.Rect((1090, 340), (150, 22)),
                                "Note button",
                                manager=manager)
    note_type_label = UILabel(pygame.Rect((1245, 340), (150, 22)),
                              "Note type",
                              manager=manager)

    fps_label = UILabel(pygame.Rect((0, 30), (30, 30)),
                        "0",
                        manager=manager)

    valid_chars = [str(x) for x in range(0, 10)] + ['.']
    start_box = UITextEntryLine(relative_rect=pygame.Rect(
        (315, 365), (150, 50)), manager=manager)
    end_box = UITextEntryLine(relative_rect=pygame.Rect(
        (470, 365), (150, 50)), manager=manager)
    vert_box = UITextEntryLine(relative_rect=pygame.Rect(
        (625, 365), (150, 50)), manager=manager)
    cue_box = UITextEntryLine(relative_rect=pygame.Rect(
        (780, 365), (150, 50)), manager=manager)
    cuesheet_box = UITextEntryLine(relative_rect=pygame.Rect(
        (935, 365), (150, 50)), manager=manager)
    note_picker = UIDropDownMenu(options_list=assets['Button prompts'][current_controller][1],
                                 starting_option=assets['Button prompts'][current_controller][1][0],
                                 relative_rect=pygame.Rect(1090, 365, 150, 30),
                                 manager=manager, object_id='#note_picker')
    note_types = ['Regular', 'Hold', 'Rapid', 'End']
    note_type_picker = UIDropDownMenu(options_list=note_types,
                                      starting_option=note_types[0],
                                      relative_rect=pygame.Rect(
                                          1245, 365, 150, 30),
                                      manager=manager, object_id='#type_picker')

    # what the player is holding
    selected = None
    load_item_tex(current_controller, karaoke,
                  selected, note_picker)  # load button textures
    dropdowns = [note_picker, note_type_picker]
    for dropdown in dropdowns:
        dropdown.hide()
    # load sheet textures and scale them
    sheet_tex = texture_path + '\\' + assets['Sheet texture']
    line_tex = texture_path + '\\' + assets['Line texture']
    sheet_bg = pygame.image.load(sheet_tex).convert()
    line_bg = pygame.image.load(line_tex).convert()
    line_bg = pygame.transform.scale(
        line_bg, (2, (karaoke.box_size + karaoke.border) * karaoke.rows))
    sheet_bg = pygame.transform.scale(
        sheet_bg, (karaoke.box_size + karaoke.border, (karaoke.box_size + karaoke.border) * karaoke.rows))

    boxes = [start_box, end_box, vert_box, cue_box, cuesheet_box]
    box_labels = [start_label, end_label, vert_label, cue_label,
                  cuesheet_label, note_button_label, note_type_label]

    for i in range(len(boxes)):
        if i == 2:
            valid_chars.pop()
        boxes[i].set_allowed_characters(valid_chars)
        boxes[i].hide()

    for label in box_labels:
        label.hide()

    # Horizontal ScrollBar
    thick_h = 30
    scrollbar_size = accurate_size - scr_size[0]
    scrollbar = UIHorizontalSlider(relative_rect=pygame.Rect(-3, scr_size[1] - thick_h + 2, 1605, thick_h),
                                   start_value=0,
                                   value_range=(0, scrollbar_size),
                                   manager=manager)

    # what the player is currently editing
    currently_edited = None
    stopped_editing = False
    gui_button_mode = None
    open_file = None
    key_pressed = None  # none of the arrow keys are pressed right now
    note_id = 0  # note that you get when you want to add one, first is circle
    fill_colour = (44, 52, 58)
    FPS = int(config['CONFIG']['FPS'])
    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------
    while True:
        # Clock tick
        time_delta = clock.tick(FPS) / 1000
        scrollbar_value = scrollbar.get_current_value()

        # draw the screen
        if scrollbar_value + 1600 > world.get_width():
            world1_end = world.get_width() - scrollbar_value
            if world1_end > 0:
                world.fill((fill_colour), rect=pygame.Rect(
                    scrollbar_value, 0, world1_end, 480))  # clean the screen
                world2.fill((fill_colour), rect=pygame.Rect(
                    scrollbar_value - world.get_width(), 0, 1600, 480))  # clean the screen
                karaoke.draw(world, 1, scrollbar_value,
                             scr_size[0], sheet_bg, line_bg)
                karaoke.draw(world2, 2, scrollbar_value,
                             scr_size[0], sheet_bg, line_bg)
            else:
                world2.fill((fill_colour), rect=pygame.Rect(
                    scrollbar_value - world.get_width(), 0, 1600, 480))  # clean the screen
                karaoke.draw(world2, 2, scrollbar_value,
                             scr_size[0], sheet_bg, line_bg)
        else:
            world.fill((fill_colour), rect=pygame.Rect(
                scrollbar_value, 0, 1600, 480))  # clean the screen
            karaoke.draw(world, 1, scrollbar_value,
                         scr_size[0], sheet_bg, line_bg)

        mousex, mousey = pygame.mouse.get_pos()
        mousex += scrollbar_value  # adjust for scrollbar

        if key_pressed:
            diff = 10 + scrollbar_add
            scrollbar_add += 1
            if key_pressed == 'right':
                if scrollbar.get_current_value() + diff <= scrollbar_size:
                    scrollbar.set_current_value(
                        scrollbar.get_current_value() + diff)
                else:
                    scrollbar.set_current_value(scrollbar_size)
            elif key_pressed == 'left':
                if scrollbar.get_current_value() - diff >= 0:
                    scrollbar.set_current_value(
                        scrollbar.get_current_value() - diff)
                else:
                    scrollbar.set_current_value(0)

        # if holding something, draw it next to mouse
        if selected:
            if mousex > world.get_width():
                world2.blit(selected.resize(20),
                            (mousex - world.get_width(), mousey))
            else:
                world.blit(selected.resize(20), (mousex, mousey))

        # if editing note params
        if currently_edited:
            x = 2 + karaoke.x + \
                (currently_edited.x * (karaoke.box_size + karaoke.border))
            y = 2 + karaoke.y + \
                (currently_edited.y * (karaoke.box_size + karaoke.border))
            if x > world.get_width():
                pygame.draw.rect(world2, (0, 100, 255), (x - world.get_width() + karaoke.box_size / 2, y, karaoke.box_size + karaoke.border,
                                                         karaoke.box_size + karaoke.border), 3)
            else:
                pygame.draw.rect(world, (0, 100, 255), (x, y, karaoke.box_size + karaoke.border,
                                                        karaoke.box_size + karaoke.border), 3)

        # Application events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                with open(settings_file, 'w') as configfile:  # save config
                    config.write(configfile)
                exit()

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
                    selected = Item(0, 0, note_id, 'Regular', 0)  # add item
                elif event.button == 1:  # left click
                    pos = karaoke.Get_pos(scrollbar_value)
                    if karaoke.In_grid(pos[0], pos[1]):
                        if selected:
                            selected.start_pos = karaoke.pos_to_game(pos[0])
                            selected.x = pos[0]
                            selected.y = pos[1]
                            selected = karaoke.Add(selected)
                        elif karaoke.items[pos[0]][pos[1]]:
                            if karaoke.items[pos[0]][pos[1]] != currently_edited:
                                selected = karaoke.items[pos[0]][pos[1]]
                                karaoke.items[pos[0]][pos[1]] = None

            if event.type == pygame.KEYDOWN:
                # scrollbar moving
                if event.key in [pygame.K_RIGHT, pygame.K_PAGEUP]:
                    key_pressed = 'right'
                    scrollbar_add = 0
                    if scrollbar.get_current_value() + 10 <= scrollbar_size:
                        scrollbar.set_current_value(
                            scrollbar.get_current_value() + 10)
                    else:
                        scrollbar.set_current_value(scrollbar_size)

                if event.key in [pygame.K_LEFT, pygame.K_PAGEDOWN]:
                    key_pressed = 'left'
                    scrollbar_add = 0
                    if scrollbar.get_current_value() - 10 >= 0:
                        scrollbar.set_current_value(
                            scrollbar.get_current_value() - 10)
                    else:
                        scrollbar.set_current_value(0)

                if event.key == pygame.K_HOME:
                    scrollbar.set_current_value(1)

                if event.key == pygame.K_END:
                    exit_loop = False
                    if len(karaoke.items) > 0:
                        for i in range(len(karaoke.items) - 1, 0, -1):
                            for o in range(len(karaoke.items[i])):
                                if karaoke.items[i][o] != None:
                                    exit_loop = True
                                    break
                            if exit_loop:
                                break
                        note_loc = i * (karaoke.box_size +
                                        karaoke.border) + 2 * karaoke.x - screen.get_width()
                        if note_loc < 0:
                            note_loc = 0
                        scrollbar.set_current_value(note_loc)

                if event.key == pygame.K_DELETE:
                    if currently_edited:
                        gui_button_mode = 'Delete'
                        delete_note = UIConfirmationDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc='Are you sure you want to remove this note? This change cannot be undone.', window_title='Delete note')

                    selected = None  # deletes selected note
                if event.key == pygame.K_LCTRL:
                    note_id = 4
                    selected = Item(0, 0, note_id, 'Hold', 0)  # add item
                if event.key == pygame.K_LSHIFT:
                    note_id = 5
                    selected = Item(0, 0, note_id, 'Rapid', 0)  # add item
                if event.key == pygame.K_e:  # property editing mode
                    pos = karaoke.Get_pos(scrollbar_value)
                    if not currently_edited:
                        if karaoke.In_grid(pos[0], pos[1]):
                            if karaoke.items[pos[0]][pos[1]] != None:
                                if karaoke.items[pos[0]][pos[1]].id < 4:
                                    currently_edited = karaoke.items[pos[0]][pos[1]]
                                    for dropdown in dropdowns:
                                        dropdown.show()
                                    undo_button.show()
                                    for label in box_labels:
                                        label.show()
                                    for box in boxes:
                                        box.show()
                                # set values
                                    update_text_boxes(
                                        currently_edited, boxes, dropdowns)  # TODO - cleanup all the generic stuff

                    else:
                        if karaoke.In_grid(pos[0], pos[1]):
                            if karaoke.items[pos[0]][pos[1]] != currently_edited and karaoke.items[pos[0]][pos[1]] != None:
                                if karaoke.items[pos[0]][pos[1]].id < 4:
                                    save_before_closing(
                                        currently_edited, boxes, dropdowns, karaoke)
                                    currently_edited = karaoke.items[pos[0]][pos[1]]
                                    update_text_boxes(
                                        currently_edited, boxes, dropdowns)
                                else:
                                    stopped_editing = True
                            else:
                                stopped_editing = True
                        else:
                            stopped_editing = True
                        if stopped_editing:
                            save_before_closing(
                                currently_edited, boxes, dropdowns, karaoke)
                            stopped_editing = False  # reset value
                            currently_edited = None  # deselect
                            stop_editing(boxes, box_labels,
                                         dropdowns, undo_button)

            if event.type == pygame.KEYUP:
                if event.key in [pygame.K_RIGHT, pygame.K_LEFT, pygame.K_PAGEDOWN, pygame.K_PAGEUP]:
                    key_pressed = None

            if event.type == pygame.USEREVENT:
                # menu bar events
                if (event.type == pygame.USEREVENT
                    and event.user_type == UI_BUTTON_START_PRESS
                        and event.ui_object_id == 'menu_bar.#file_menu_items.#open'):
                    gui_button_mode = 'Input'
                    input_selection = UIFileDialog(
                        rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, allow_existing_files_only=True, window_title='Select an input file (kbd)', initial_file_path=Path(config['PATHS']['Input']))

                if (event.type == pygame.USEREVENT
                    and event.user_type == UI_BUTTON_START_PRESS
                        and event.ui_object_id == 'menu_bar.#file_menu_items.#new'):
                    gui_button_mode = 'Reset'
                    reset_all = UIConfirmationDialog(
                        rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc='Are you sure you want to create a new file? Any unsaved changes will be lost.', window_title='Create a new file')

                if (event.type == pygame.USEREVENT
                        and event.user_type == UI_BUTTON_START_PRESS
                        and event.ui_object_id == 'menu_bar.#file_menu_items.#save'):
                    if open_file != None:
                        gui_button_mode = 'Save'
                        save = UIConfirmationDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=f'Are you sure you want to overwrite {open_file.name}?', window_title='Create a new file')
                    else:
                        gui_button_mode = 'Output'
                        output_selection = UIFileDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, window_title='Select an output file (kbd)', initial_file_path=Path(config['PATHS']['Output']))

                if (event.type == pygame.USEREVENT
                        and event.user_type == UI_BUTTON_START_PRESS
                        and event.ui_object_id == 'menu_bar.#file_menu_items.#save_as'):
                    gui_button_mode = 'Output'
                    output_selection = UIFileDialog(
                        rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, window_title='Select an output file (kbd)', initial_file_path=Path(config['PATHS']['Output']))

                if (event.type == pygame.USEREVENT
                            and event.user_type == UI_BUTTON_START_PRESS
                            and event.ui_object_id == 'menu_bar.#help_menu_items.#how_to_use'
                        ):
                    info_window_rect = pygame.Rect(0, 0, 400, 250)
                    info_window_rect.center = screen.get_rect().center

                    UIMessageWindow(rect=info_window_rect,
                                    html_message='<br><b>How to use</b><br>'
                                    '---------------<br><br>'
                                    '<b>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. </b>',
                                    manager=manager,
                                    window_title='Help')

                if (event.type == pygame.USEREVENT
                        and event.user_type == UI_BUTTON_START_PRESS
                        and event.ui_object_id == 'menu_bar.#help_menu_items.#about'):
                    about_window_rect = pygame.Rect(0, 0, 400, 250)
                    about_window_rect.center = screen.get_rect().center
                    UIMessageWindow(rect=about_window_rect,
                                    html_message='<br><b>KUMA</b><br>'
                                    '---------------<br><br>'
                                    '<b>Version: </b>1.0.0<br>'
                                    '<b>Created by: </b>Timo654<br>',
                                    manager=manager,
                                    window_title='About')

                if event.user_type == UI_DROP_DOWN_MENU_CHANGED:
                    config.set("CONFIG", "BUTTONS", str(
                        button_picker.selected_option))
                    load_item_tex(button_picker.selected_option,
                                  karaoke, selected, note_picker)
                if event.user_type == UI_BUTTON_PRESSED:
                    if gui_button_mode == 'Input':
                        if event.ui_element == input_selection.ok_button:
                            gui_button_mode = None
                            open_file = input_selection.current_file_path
                            config.set("PATHS", "Input", str(
                                input_selection.current_file_path))
                            karaoke = load_kbd(
                                input_selection.current_file_path, karaoke)
                            currently_edited = None

                    if gui_button_mode == 'Output':
                        if event.ui_element == output_selection.ok_button:
                            gui_button_mode = None
                            open_file = output_selection.current_file_path
                            config.set("PATHS", "Output", str(
                                output_selection.current_file_path))
                            write_kbd(
                                output_selection.current_file_path, karaoke)

                    if event.ui_element == undo_button:
                        gui_button_mode = 'Undo'
                        undo_note = UIConfirmationDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc='Are you sure you want to undo changes made to this note?', window_title='Undo changes')
                if event.user_type == UI_CONFIRMATION_DIALOG_CONFIRMED:  # reset event
                    if gui_button_mode == 'Reset':
                        gui_button_mode = None
                        karaoke = Karaoke()
                        if currently_edited:
                            currently_edited = None
                            stop_editing(boxes, box_labels,
                                         dropdowns, undo_button)
                    if gui_button_mode == 'Undo':
                        gui_button_mode = None
                        update_text_boxes(currently_edited,
                                          boxes, dropdowns)
                    if gui_button_mode == 'Delete':
                        karaoke.Remove(currently_edited.x, currently_edited.y)
                        stop_editing(boxes, box_labels, dropdowns, undo_button)
                        currently_edited = None
                    if gui_button_mode == 'Save':
                        if open_file != None:
                            write_kbd(
                                open_file, karaoke)
                        else:
                            raise Exception('No open file, unable to save!')

            manager.process_events(event)

        trunc_world_orig = (scrollbar_value, 0)
        trunc_world = (scr_size[0], scr_size[1] - thick_h + 5)

        if scrollbar_value + 1600 > world.get_width():
            trunc_world2_orig = (
                scrollbar.get_current_value() - world.get_width(), 0)
            world1_end = world.get_width() - trunc_world_orig[0]
            if world1_end > 0:
                screen.blit(world, (0, 0), (trunc_world_orig,
                                            (world1_end, trunc_world[1])))
                screen.blit(world2, (world1_end, 0), ((0, 0),
                                                      (trunc_world[0] - world1_end, trunc_world[1])))
            else:
                screen.blit(world2, (0, 0), (trunc_world2_orig, trunc_world))
        else:
            screen.blit(world, (0, 0), (trunc_world_orig, trunc_world))

        fps_label.set_text(update_fps())
        manager.draw_ui(screen)
        manager.update(time_delta)
        pygame.display.update()


if __name__ == '__main__':
    main()
