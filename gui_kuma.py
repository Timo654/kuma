# based on https://github.com/TheBigKahuna353/Inventory_system and https://github.com/ppizarror/pygame-menu/blob/master/pygame_menu/examples/other/scrollbar.py
import pygame
import pygame_menu
import pygame_gui
import json
from pathlib import Path
from pygame_gui.windows.ui_file_dialog import UIFileDialog, UIConfirmationDialog
from pygame_gui.elements import UIDropDownMenu, UILabel, UIButton, UITextEntryLine
from pygame_menu.widgets import ScrollBar
import kbd_reader as kbd
from math import ceil, floor
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
font = pygame.font.SysFont("Comic-Sans", 18)
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

# the karaoke system


class Karaoke:
    def __init__(self):
        self.rows = 8
        self.col = 3970
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
            world.blit(sheet_bg, (x_coord + (33 * (i)), self.y))
            if i % 20 == 0:
                current_time = self.format_time(i, surface2_offset)
                time_text = font.render(current_time, 1, pygame.Color("black"))
                world.blit(time_text, (x_coord + (33 * (i)), 20))
                world.blit(
                    line_bg, (x_coord + (one_box // 2) + (33 * (i)), self.y))
        for x in range(col_start, col_end):
            for y in range(self.rows):
                rect = (x_coord + (self.box_size + self.border)*x + self.border, self.x +
                        (self.box_size + self.border)*y + self.border, self.box_size, self.box_size)
                if self.items[x + surface2_offset][y]:
                    world.blit(self.items[x + surface2_offset]
                               [y].resize(self.box_size), rect)

    def format_time(self, i, surface2_offset):
        # display current time, 100 ms each square
        seconds = (i + surface2_offset) // self.scale
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

    # check whether the mouse in in the grid
    def In_grid(self, x, y):
        if (x < 0) or (y < 0) or (x >= self.col) or (y >= self.rows):
            return False
        return True


# https://python-forum.io/thread-403.html
def strip_from_sheet(sheet, start, size, columns, rows):
    frames = []
    for j in range(rows):
        for i in range(columns):
            location = (start[0]+size[0]*i, start[1]+size[1]*j)
            frames.append(sheet.subsurface(pygame.Rect(location, size)))
    return frames


def load_item_tex(button_type, karaoke, selected):
    global items
    # load note textures
    tex_name = texture_path + '\\' + assets['Button prompts'][button_type]
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
                    progress_value += 300
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
    fps_text = font.render(fps, 1, pygame.Color("black"))
    return fps_text


def update_text_boxes(note, boxes):
    # set values
    boxes[0].set_text(str(game_to_ms(note.start_pos)))
    boxes[1].set_text(str(game_to_ms(note.end_pos)))
    boxes[2].set_text(str(note.cue_id))
    boxes[3].set_text(str(note.cuesheet_id))


def save_before_closing(note, boxes):
    # TODO - clean
    if len(boxes[0].get_text()) > 0:
        note.start_pos = ms_to_game(float(boxes[0].get_text()))
    if len(boxes[1].get_text()) > 0:
        note.end_pos = ms_to_game(float(boxes[1].get_text()))
    if len(boxes[2].get_text()) > 0:
        note.cue_id = int(boxes[2].get_text())
    if len(boxes[3].get_text()) > 0:
        note.cuesheet_id = int(boxes[3].get_text())


def main():
    current_controller = config['CONFIG']['BUTTONS']
    if current_controller not in controllers:
        current_controller = controllers[0]
    scr_size = (1600, 480)
    screen = pygame.display.set_mode((scr_size))
    karaoke = Karaoke()
    accurate_size = (karaoke.col + 4) * (karaoke.box_size + karaoke.border)
    world = pygame.Surface(
        (int(accurate_size / 2), int(scr_size[1])), pygame.SRCALPHA, 32)
    world2 = pygame.Surface(
        (accurate_size - world.get_width(), int(scr_size[1])), pygame.SRCALPHA, 32)

    # what the player is holding
    selected = None
    load_item_tex(current_controller, karaoke, selected)  # load button textures

    # load sheet textures and scale them
    sheet_tex = texture_path + '\\' + assets['Sheet texture']
    line_tex = texture_path + '\\' + assets['Line texture']
    sheet_bg = pygame.image.load(sheet_tex).convert()
    line_bg = pygame.image.load(line_tex).convert()
    line_bg = pygame.transform.scale(
        line_bg, (2, (karaoke.box_size + karaoke.border) * karaoke.rows))
    sheet_bg = pygame.transform.scale(
        sheet_bg, (karaoke.box_size + karaoke.border, (karaoke.box_size + karaoke.border) * karaoke.rows))

    manager = pygame_gui.UIManager(scr_size)
    file_selection_button = UIButton(relative_rect=pygame.Rect((10, 325), (100, 50)),
                                                         text='Open file',
                                                         manager=manager)
    output_selection_button = UIButton(relative_rect=pygame.Rect((110, 325), (100, 50)),
                                                           text='Save file',
                                                           manager=manager)
    reset_button = UIButton(relative_rect=pygame.Rect((210, 325), (100, 50)),
                                                text='Reset',
                                                manager=manager)
    undo_button = UIButton(relative_rect=pygame.Rect((315, 380), (200, 50)),
                                               text='Undo note changes',
                                               manager=manager)
    button_picker = UIDropDownMenu(options_list=controllers,
                                   starting_option=current_controller,
                                   relative_rect=pygame.Rect(10, 375, 200, 30),
                                   manager=manager)


    start_label = UILabel(pygame.Rect((315, 325),(150, 22)),
                                   "Start position",
                                   manager=manager)
    end_label = UILabel(pygame.Rect((470, 325),(150, 22)),
                                   "End position",
                                   manager=manager)
    cue_label = UILabel(pygame.Rect((625, 325),(150, 22)),
                                   "Cue ID",
                                   manager=manager)
    cuesheet_label = UILabel(pygame.Rect((780, 325),(150, 22)),
                                   "Cuesheet ID",
                                   manager=manager)                                                              
    
    valid_chars = [str(x) for x in range(0, 10)] + ['.']
    start_box = UITextEntryLine(relative_rect=pygame.Rect(
        (315, 350), (150, 50)), manager=manager)
    end_box = UITextEntryLine(relative_rect=pygame.Rect(
        (470, 350), (150, 50)), manager=manager)
    cue_box = UITextEntryLine(relative_rect=pygame.Rect(
        (625, 350), (150, 50)), manager=manager)
    cuesheet_box = UITextEntryLine(relative_rect=pygame.Rect(
        (780, 350), (150, 50)), manager=manager)
    boxes = [start_box, end_box, cue_box, cuesheet_box]
    for box in boxes:
        box.set_allowed_characters(valid_chars)
        # box.disable()

    # Horizontal ScrollBar
    thick_h = 20
    sb_h = ScrollBar(
        length=scr_size[0],
        values_range=(50, accurate_size - scr_size[0]),
        slider_pad=2,
        page_ctrl_thick=thick_h
    )

    sb_h.set_shadow(
        color=(0, 0, 0),
        position=pygame_menu.locals.POSITION_SOUTHEAST
    )
    sb_h.set_position(0, scr_size[1] - thick_h)
    sb_h.set_page_step(scr_size[0])

    
    #what the player is currently editing
    currently_edited = None
    stopped_editing = False
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
        if scrollbar_value + 1600 > world.get_width():
            world1_end = world.get_width() - scrollbar_value
            if world1_end > 0:
                world.fill((169, 149, 154), rect=pygame.Rect(
                    scrollbar_value, 0, world1_end, 480))  # clean the screen
                world2.fill((169, 149, 154), rect=pygame.Rect(
                    scrollbar_value - world.get_width(), 0, 1600, 480))  # clean the screen
                karaoke.draw(world, 1, scrollbar_value,
                             scr_size[0], sheet_bg, line_bg)
                karaoke.draw(world2, 2, scrollbar_value,
                             scr_size[0], sheet_bg, line_bg)
            else:
                world2.fill((169, 149, 154), rect=pygame.Rect(
                    scrollbar_value - world.get_width(), 0, 1600, 480))  # clean the screen
                karaoke.draw(world2, 2, scrollbar_value,
                             scr_size[0], sheet_bg, line_bg)
        else:
            world.fill((169, 149, 154), rect=pygame.Rect(
                scrollbar_value, 0, 1600, 480))  # clean the screen
            karaoke.draw(world, 1, scrollbar_value,
                         scr_size[0], sheet_bg, line_bg)

        mousex, mousey = pygame.mouse.get_pos()
        mousex += scrollbar_value  # adjust for scrollbar

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
            pygame.draw.rect(world, (0, 100, 255), (x, y, karaoke.box_size + karaoke.border,
                             karaoke.box_size + karaoke.border), 3)

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
                            selected = karaoke.items[pos[0]][pos[1]]
                            karaoke.items[pos[0]][pos[1]] = None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DELETE:
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
                                currently_edited = karaoke.items[pos[0]][pos[1]]
                                for box in boxes:
                                    box.enable()
                                # set values
                                update_text_boxes(currently_edited, boxes)

                    else:
                        if karaoke.In_grid(pos[0], pos[1]):
                            if karaoke.items[pos[0]][pos[1]] != currently_edited and karaoke.items[pos[0]][pos[1]] != None:
                                save_before_closing(currently_edited, boxes)
                                currently_edited = karaoke.items[pos[0]][pos[1]]
                                update_text_boxes(currently_edited, boxes)
                            else:
                                stopped_editing = True
                        else:
                            stopped_editing = True
                        if stopped_editing:
                            save_before_closing(currently_edited, boxes)
                            currently_edited = None  # deselect
                            # for box in boxes:
                            # box.disable()  # disable text boxes
                            stopped_editing = False  # reset value

            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    config.set("CONFIG", "BUTTONS", str(
                        button_picker.selected_option))
                    load_item_tex(button_picker.selected_option, karaoke, selected)
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == file_selection_button:
                        gui_button_mode = 'Input'
                        input_selection = UIFileDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, allow_existing_files_only=True, window_title='Select an input file (kbd)', initial_file_path=Path(config['PATHS']['Input']))
                    if gui_button_mode == 'Input':
                        if event.ui_element == input_selection.ok_button:
                            gui_button_mode = None
                            config.set("PATHS", "Input", str(
                                input_selection.current_file_path))
                            karaoke = load_kbd(
                                input_selection.current_file_path, karaoke)
                            currently_edited = None

                    if event.ui_element == output_selection_button:
                        gui_button_mode = 'Output'
                        output_selection = UIFileDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, window_title='Select an output file (kbd)', initial_file_path=Path(config['PATHS']['Output']))
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
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc='Are you sure you want to reset? Any unsaved changes will be lost.', window_title='Reset all')
                    if event.ui_element == undo_button:
                        gui_button_mode = 'Undo'
                        undo_note = UIConfirmationDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc='Are you sure you want to undo changes made to this note?', window_title='Undo changes')
                if event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:  # reset event
                    if gui_button_mode == 'Reset':
                        gui_button_mode = None
                        karaoke = Karaoke()
                        currently_edited = None
                    if gui_button_mode == 'Undo':
                        gui_button_mode = None
                        update_text_boxes(currently_edited, boxes)
            manager.process_events(event)

        trunc_world_orig = (scrollbar_value, 0)
        trunc_world = (scr_size[0], scr_size[1] - thick_h)

        if scrollbar_value + 1600 > world.get_width():
            trunc_world2_orig = (sb_h.get_value() - world.get_width(), 0)
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

        screen.blit(update_fps(), (10, 0))
        manager.draw_ui(screen)
        manager.update(time_delta)
        pygame.display.update()


if __name__ == '__main__':
    main()
