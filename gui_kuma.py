
import pygame
from pygame_gui import UIManager, UI_BUTTON_START_PRESS, UI_BUTTON_PRESSED, UI_DROP_DOWN_MENU_CHANGED, UI_CONFIRMATION_DIALOG_CONFIRMED, UI_HORIZONTAL_SLIDER_MOVED, UI_TEXT_ENTRY_CHANGED
from pygame_gui.windows import UIFileDialog, UIConfirmationDialog, UIMessageWindow
from pygame_gui.elements import UIDropDownMenu, UILabel, UIButton, UITextEntryLine, UIHorizontalSlider
import modules.kbd_reader as kbd
import modules.kpm_reader as kpm
from modules.ui_menu_bar import UIMenuBar
from pathlib import Path
from math import ceil, floor
import json
import configparser
import gettext
import locale
import mutagen

VERSION = "v0.9.0"
TRANSLATORS = 'Timo654, ketrub, Mink, jason098, Capitán Retraso'
TESTERS = "ketrub, KaarelJ98"
print("""
   _     _      _     _      _     _      _     _   
  (c).-.(c)    (c).-.(c)    (c).-.(c)    (c).-.(c)  
   / ._. \      / ._. \      / ._. \      / ._. \   
 __\( Y )/__  __\( Y )/__  __\( Y )/__  __\( Y )/__ 
(_.-/'-'\-._)(_.-/'-'\-._)(_.-/'-'\-._)(_.-/'-'\-._)
   || K ||      || U ||      || M ||      || A ||   
 _.' `-' '._  _.' `-' '._  _.' `-' '._  _.' `-' '._ 
(.-./`-'\.-.)(.-./`-'\.-.)(.-./`-'\.-.)(.-./`-'\.-.)
 `-'     `-'  `-'     `-'  `-'     `-'  `-'     `-'   """ + VERSION + '\n\n')

asset_file = 'assets.json'
if Path(asset_file).is_file():
    with open(asset_file, 'r', encoding='UTF-8') as json_file:
        assets = json.load(json_file)
else:
    raise Exception(_('Asset data missing'))

texture_path = assets['Texture folder']
controllers = [key for key in assets['Button prompts']]
languages = [key for key in assets['Languages']]

# get default language


def get_default_language():
    loc = locale.getdefaultlocale()  # get current locale
    lang_code = loc[0].split('_')[0]
    language = list(assets['Languages'].keys())[list(
        assets['Languages'].values()).index(lang_code)]
    return language


# read/create settings
settings_file = 'KUMA_settings.ini'
config = configparser.ConfigParser()
if Path(settings_file).is_file():
    config.read(settings_file, encoding='UTF-8')
if not config.has_section("CONFIG"):
    config.add_section("CONFIG")
    config.set("CONFIG", "FPS", str(60))
    config.set("CONFIG", "BUTTONS", controllers[0])
    config.set("CONFIG", "LANGUAGE", get_default_language())
    config.set("CONFIG", "VOLUME", str(1))
if not config.has_section("PATHS"):
    config.add_section("PATHS")
    config.set("PATHS", "Input", f'{str(Path().resolve())}\\input_file.kbd')
    config.set("PATHS", "Output", f'{str(Path().resolve())}\\output_file.kbd')
    config.set("PATHS", "KPM_Input",
               f'{str(Path().resolve())}\\input_file.kpm')
    config.set("PATHS", "KPM_Output",
               f'{str(Path().resolve())}\\output_file.kpm')
    config.set("PATHS", "Music",
               f'{str(Path().resolve())}\\audio.ogg')

# initialize pygame stuff
pygame.init()
font = pygame.font.SysFont("FiraCode", 22)
clock = pygame.time.Clock()
pygame.display.set_caption('KUMA')
pygame_icon = pygame.image.load(f"{assets['Texture folder']}\\icon_small.png")
pygame.display.set_icon(pygame_icon)
pygame.mixer.music.set_volume(float(config["CONFIG"]["VOLUME"]))


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

    # add an item
    def Add(self, Item):
        self.items[Item.x][Item.y] = Item

    # remove an item
    def Remove(self, x, y):
        self.items[x][y] = None

    def Remove_long(self, x, y, y_pos=None, new_end_pos=0):
        note = self.items[x][y]
        if y_pos == None:
            y_pos = note.y
        old_end_pos = self.pos_convert(note.end_pos)
        start_pos = self.pos_convert(note.start_pos)
        for i in range(old_end_pos + 1, new_end_pos, -1):
            if i == start_pos:
                break
            self.Remove(i, y_pos)
        note = None

    # check whether the mouse in in the grid
    def In_grid(self, x, y):
        if (x < 0) or (y < 0) or (x >= self.col) or (y >= self.rows):
            return False
        return True

    def format_time(self, i):
        # display current time, 100 ms each square
        seconds = i // self.scale
        minutes = seconds // 60
        if minutes:
            if seconds % 60 == 0:
                return _("{min} min").format(min=minutes)
            else:
                seconds = seconds - (minutes * 60)
                return _("{min} min {sec} s").format(min=minutes, sec=seconds)
        else:
            return _("{sec} s").format(sec=seconds)

    # convert positions
    def pos_convert(self, pos):
        return normal_round(((pos / 3000) * self.scale))

    # converts pos back to yakuza time

    def pos_to_game(self, pos):
        return normal_round((pos / self.scale) * 3000)

# Loading textures


def load_item_tex(button_type, karaoke, selected, dropdown):
    global items
    # load note textures
    tex_name = f"{texture_path}\\{assets['Button prompts'][button_type][0]}"
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

# https://python-forum.io/thread-403.html


def strip_from_sheet(sheet, start, size, columns, rows):
    frames = []
    for j in range(rows):
        for i in range(columns):
            location = (start[0]+size[0]*i, start[1]+size[1]*j)
            frames.append(sheet.subsurface(pygame.Rect(location, size)))
    return frames

# various time conversions


def game_to_ms(pos):
    return float(pos / 3)


def ms_to_game(pos):
    return normal_round(pos * 3)


def normal_round(n):  # https://stackoverflow.com/questions/33019698/how-to-properly-round-up-half-float-numbers
    if n - floor(n) < 0.5:
        return floor(n)
    return ceil(n)


def song_pos_to_scroll(position, karaoke):
    if position > 198250 or position < 50:
        diff = 0
    else:
        diff = -50
    return ((position + diff) / 100) * (karaoke.box_size + karaoke.border)


def scroll_to_song_pos(position, karaoke):
    new_pos = int((position * 100) / (karaoke.box_size + karaoke.border))
    if new_pos > 198250:
        return new_pos
    else:
        return new_pos + 50

# KPM code


def load_kpm(file, cutscene_box, refresh=1):
    try:
        data = kpm.read_file(file)
    except(ValueError):
        print(_('Unable to read file.'))
        return False
    except(PermissionError):
        print(_('Unable to open file.'))
        return False
    else:
        if refresh:
            cutscene_box.set_text(
                str(data['Parameters'][0]['Cutscene start time']))
        return data


def save_kpm(file, cutscene_box, data):
    if Path.exists(file):
        data = load_kpm(file, cutscene_box, refresh=0)
    elif data != None:
        data['Parameters'][0]['Cutscene start time'] = float(
            cutscene_box.get_text())
        kpm.write_file(data, file)
        print(_("KPM written to {}").format(file))

# KBD code


def load_kbd(file, karaoke, cutscene_box):
    try:
        data = kbd.read_file(file)
    except(ValueError):
        print(_('Unable to read file.'))
        return karaoke, None
    except(PermissionError):
        print(_('Unable to open file.'))
        return karaoke, None
    else:
        karaoke = Karaoke()  # reset data
        for note in data['Notes']:
            if note['Note type'] < 3:
                start_pos = karaoke.pos_convert(note['Start position'])
                karaoke.Add(Item(start_pos, note['Vertical position'], note['Button type'], note['Note type'],
                                 note['Start position'], end_pos=note['End position'], cue_id=note['Cue ID'], cuesheet_id=note['Cuesheet ID']))
                if note['Note type'] != 0:
                    end_pos = karaoke.pos_convert(note['End position'])
                    if note['Note type'] == 1:
                        note_id = 4
                    else:
                        note_id = 5
                    progress_value = 0
                    for i in range(start_pos + 1, end_pos):
                        progress_value += 100
                        karaoke.Add(Item(i, note['Vertical position'], note_id,
                                         note['Note type'], note['Start position'] + progress_value))
                    karaoke.Add(Item(
                        end_pos, note['Vertical position'], note['Button type'], 3, note['End position']))
        kpm_file = f"{str(file.parent)}\\{file.stem.split('_')[0]}_param.kpm"
        if Path(kpm_file).exists():
            load_kpm(kpm_file, cutscene_box)
    return karaoke, True


def write_kbd(file, karaoke, cutscene_box):
    data = dict()
    note_list = list()
    x = 0
    while x < len(karaoke.items):
        y = 0
        while y < len(karaoke.items[x]):
            if karaoke.items[x][y] != None:
                if karaoke.items[x][y].id <= 3 and karaoke.items[x][y].note_type < 3:  # if not End
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
                                karaoke.items[o][y].note_type = 3  # End
                                note['End position'] = karaoke.pos_to_game(o)
                                current_note.end_pos = note['End position']
                    note_list.append(note)
            y += 1
        x += 1
    data['Notes'] = note_list
    data['Header'] = dict()
    data['Header']['Version'] = 2
    kbd.write_file(data, file, cutscene_start=float(cutscene_box.get_text()))
    print(_("File written to {}").format(file))

# update values


def update_text_boxes(note, boxes, dropdowns):
    # set values
    boxes[0].set_text(str(game_to_ms(note.start_pos)))
    boxes[1].set_text(str(game_to_ms(note.end_pos)))
    boxes[2].set_text(str(note.y))
    boxes[3].set_text(str(note.cue_id))
    boxes[4].set_text(str(note.cuesheet_id))
    update_dropdown(dropdowns[0], mode='update selection', index=note.id)
    update_dropdown(dropdowns[1], mode='update selection',
                    index=note.note_type)


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


def update_fps():  # fps counter from https://pythonprogramming.altervista.org/pygame-how-to-display-the-frame-rate-fps-on-the-screen/
    fps = str(int(clock.get_fps()))
    return fps

# save parameter when stopping editing


def save_before_closing(note, boxes, dropdowns, karaoke):
    vert_changed = False
    if len(boxes[0].get_text()) > 0:
        new_pos = ms_to_game(float(boxes[0].get_text()))
        if karaoke.pos_convert(new_pos) <= len(karaoke.items):
            note.start_pos = new_pos
            karaoke.items[note.x][note.y] = None
            note.x = karaoke.pos_convert(note.start_pos)
            karaoke.items[note.x][note.y] = note
    if len(boxes[2].get_text()) > 0:
        if int(boxes[2].get_text()) < karaoke.rows:
            if note.y != int(boxes[2].get_text()):
                vert_changed = True
                old_pos = note.y
            karaoke.items[note.x][note.y] = None
            note.y = int(boxes[2].get_text())
            karaoke.items[note.x][note.y] = note
    if len(boxes[3].get_text()) > 0:
        note.cue_id = int(boxes[3].get_text())
    if len(boxes[4].get_text()) > 0:
        note.cuesheet_id = int(boxes[4].get_text())
    note.id = dropdowns[0].options_list.index(dropdowns[0].selected_option)
    note.note_type = dropdowns[1].options_list.index(
        dropdowns[1].selected_option)
    note.surface = items[note.id]
    if len(boxes[1].get_text()) > 0:
        if note.note_type != 0:
            end_pos = ms_to_game(float(boxes[1].get_text()))
        else:
            end_pos = 0
        if end_pos < note.end_pos or vert_changed:
            if vert_changed:
                y_pos = old_pos
                new_end_pos = 0
            else:
                y_pos = note.y
                new_end_pos = karaoke.pos_convert(end_pos)
            karaoke.Remove_long(note.x, note.y, y_pos=y_pos,
                                new_end_pos=new_end_pos)
            if vert_changed:
                y_pos = note.y
                end_pos = ms_to_game(float(boxes[1].get_text()))
        if end_pos > note.start_pos:
            note.end_pos = end_pos
            start_pos = karaoke.pos_convert(note.start_pos)
            end_pos = karaoke.pos_convert(note.end_pos)
            if note.note_type == 1:
                note_id = 4
            else:
                note_id = 5
            progress_value = 0
            for i in range(start_pos + 1, end_pos):
                progress_value += 100
                karaoke.Add(Item(i, note.y, note_id,
                                 note.note_type, note.start_pos + progress_value))
            karaoke.Add(
                Item(end_pos, note.y, note.id, 3, note.end_pos))  # note type 3 is hold/rapid end, not an actual thing in the game
        else:
            note.end_pos = 0


def stop_editing(boxes, box_labels, dropdowns, undo_button):
    for box in boxes:
        box.hide()  # disable text boxes
        for label in box_labels:
            label.hide()
        for dropdown in dropdowns:
            dropdown.hide()
        undo_button.hide()


def load_song(filename, music_elements):
    pygame.mixer.music.unload()
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
    try:
        for element in music_elements:
            element.show()
        pygame.mixer.music.load(filename)
        song = mutagen.File(filename)
        length = round(song.info.length * 1000)
    except(pygame.error):
        for element in music_elements:
            element.hide()
        print(_('Unable to read file.'))
        return False, -1
    return True, length
# language related functions


def switch_language(language, params=None, boot=False):
    lang_code = assets['Languages'][language]
    lang = gettext.translation(
        lang_code, localedir='locales', languages=[lang_code])
    lang.install()
    _ = lang.gettext
    if not boot:
        print(_('Language changed.'))
        update_text(params)


def get_menu_data():
    return {'#file_menu': {'display_name': _('File'),
                           'items':
                           {
        '#new': {'display_name': _('New...')},
        '#open': {'display_name': _('Open...')},
        '#save': {'display_name': _('Save')},
        '#save_as': {'display_name': _('Save As...')}
    },
    },
        '#music_menu': {'display_name': _('Music'),
                        'items':
                        {
            '#load_song': {'display_name': _('Load song...')}
        },
    },
        '#help_menu': {'display_name': _('Help'),
                       'items':
                       {
            '#how_to_use': {'display_name': _('How to use')},
            '#about': {'display_name': _('About')}
        }
    }
    }


def update_text(params):
    params[0].set_text(_('Undo note changes'))
    params[1].set_text(_('Load time'))
    params[2].set_text(_('Save time'))
    params[3].set_text(_('Cutscene start'))
    params[4].set_text(_('Start position'))
    params[5].set_text(_('Vertical position'))
    params[6].set_text(_('Cue ID'))
    params[7].set_text(_('Cuesheet ID'))
    params[8].set_text(_('Note button'))
    params[9].set_text(_('Note type'))
    params[11].set_text(_('End position'))
    update_dropdown(params[10], mode='update all', new_list=[_('Regular'), _('Hold'), _(
        'Rapid')], index=params[10].options_list.index(params[10].selected_option))
    menu_data = get_menu_data()
    params[12].set_text(menu_data)
    params[13].set_text(_("Song position"))
    params[14].set_text(_("Volume {}").format(
        round(float(config['CONFIG']['VOLUME']) * 100)))


def save_file(open_file, manager):
    if open_file != None:
        gui_button_mode = 'Save'
        save = UIConfirmationDialog(
            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=_("Are you sure you want to overwrite {}?").format(open_file.name), window_title=_('Create a new file'), action_short_name=_('OK'))
        save.cancel_button.set_text(_('Cancel'))
        return gui_button_mode, None
    else:
        gui_button_mode = 'Output'
        output_selection = UIFileDialog(
            rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, window_title=_('Select an output file (kbd)'), initial_file_path=Path(config['PATHS']['Output']))
        output_selection.ok_button.set_text(_('OK'))
        output_selection.cancel_button.set_text(_('Cancel'))
        return gui_button_mode, output_selection


def main():
    switch_language(config['CONFIG']['LANGUAGE'], boot=True)
    current_controller = config['CONFIG']['BUTTONS']
    if current_controller not in controllers:
        current_controller = controllers[0]
    current_language = config['CONFIG']['LANGUAGE']
    if current_language not in languages:
        current_language = languages[0]

    scr_size = (1600, 490)
    screen = pygame.display.set_mode((scr_size))
    karaoke = Karaoke()
    # FIXME - some notes overflow to the start, minor visual issue.
    accurate_size = (4 + karaoke.col) * (karaoke.box_size + karaoke.border)
    world = pygame.Surface(
        (int(accurate_size / 2), int(scr_size[1])), pygame.SRCALPHA, 32)
    world2 = pygame.Surface(
        (accurate_size - world.get_width(), int(scr_size[1])), pygame.SRCALPHA, 32)

    # ui manager
    manager = UIManager(scr_size, theme_path='assets/ui_theme.json')
    # menu bar related things, menu bar from https://github.com/MyreMylar/pygame_paint
    menu_data = get_menu_data()
    menu_bar = UIMenuBar(relative_rect=pygame.Rect(0, 0, scr_size[0], 25),
                         menu_item_data=menu_data,
                         manager=manager)

    # buttons
    undo_button = UIButton(relative_rect=pygame.Rect((425, 400), (200, 30)),
                           text=_('Undo note changes'),
                           manager=manager)
    undo_button.hide()

    load_kpm_button = UIButton(relative_rect=pygame.Rect((225, 340), (120, 30)),
                               text=_('Load time'),
                               manager=manager)
    save_kpm_button = UIButton(relative_rect=pygame.Rect((225, 365), (120, 30)),
                               text=_('Save time'),
                               manager=manager)

    play_button = UIButton(relative_rect=pygame.Rect((355, 400), (30, 30)),
                           text='▶',
                           manager=manager)

    # dropdown menus
    button_picker = UIDropDownMenu(options_list=controllers,
                                   starting_option=current_controller,
                                   relative_rect=pygame.Rect(180, 0, 200, 25),
                                   manager=manager, object_id='#button_picker')

    language_picker = UIDropDownMenu(options_list=languages,
                                     starting_option=current_language,
                                     relative_rect=pygame.Rect(
                                         380, 0, 150, 25),
                                     manager=manager, object_id='#language_picker')

    note_picker = UIDropDownMenu(options_list=assets['Button prompts'][current_controller][1],
                                 starting_option=assets['Button prompts'][current_controller][1][0],
                                 relative_rect=pygame.Rect(1140, 365, 150, 30),
                                 manager=manager, object_id='#note_picker')

    note_types = [_('Regular'), _('Hold'), _('Rapid')]
    note_type_picker = UIDropDownMenu(options_list=note_types,
                                      starting_option=note_types[0],
                                      relative_rect=pygame.Rect(
                                          1295, 365, 200, 30),
                                      manager=manager, object_id='#type_picker')

    dropdowns = [note_picker, note_type_picker]  # hide some dropdowns
    for dropdown in dropdowns:
        dropdown.hide()

    # textboxes
    valid_chars = [str(x) for x in range(0, 10)] + ['.']
    cutscene_box = UITextEntryLine(relative_rect=pygame.Rect(
        (10, 365), (200, 50)), manager=manager)
    cutscene_box.set_text(str(0))
    start_box = UITextEntryLine(relative_rect=pygame.Rect(
        (365, 365), (150, 50)), manager=manager)
    end_box = UITextEntryLine(relative_rect=pygame.Rect(
        (520, 365), (150, 50)), manager=manager)
    vert_box = UITextEntryLine(relative_rect=pygame.Rect(
        (675, 365), (150, 50)), manager=manager)
    cue_box = UITextEntryLine(relative_rect=pygame.Rect(
        (830, 365), (150, 50)), manager=manager)
    cuesheet_box = UITextEntryLine(relative_rect=pygame.Rect(
        (985, 365), (150, 50)), manager=manager)

    music_box = UITextEntryLine(relative_rect=pygame.Rect(
        (10, 425), (200, 50)), manager=manager, object_id="#song_position")
    music_box.set_text(str(0))

    boxes = [start_box, end_box, vert_box, cue_box, cuesheet_box]

    for i in range(len(boxes)):
        if i == 2:
            valid_chars.pop()
        boxes[i].set_allowed_characters(valid_chars)
        boxes[i].hide()
    music_box.set_allowed_characters(valid_chars)

    # labels
    cutscene_label = UILabel(pygame.Rect((10, 340), (200, 22)),
                             _("Cutscene start"),
                             manager=manager)
    start_label = UILabel(pygame.Rect((365, 340), (150, 22)),
                          _("Start position"),
                          manager=manager)
    end_label = UILabel(pygame.Rect((520, 340), (150, 22)),
                        _("End position"),
                        manager=manager)
    vert_label = UILabel(pygame.Rect((675, 340), (150, 22)),
                         _("Vertical position"),
                         manager=manager)
    cue_label = UILabel(pygame.Rect((830, 340), (150, 22)),
                        _("Cue ID"),
                        manager=manager)
    cuesheet_label = UILabel(pygame.Rect((985, 340), (150, 22)),
                             _("Cuesheet ID"),
                             manager=manager)
    note_button_label = UILabel(pygame.Rect((1140, 340), (150, 22)),
                                _("Note button"),
                                manager=manager)
    note_type_label = UILabel(pygame.Rect((1295, 340), (200, 22)),
                              _("Note type"),
                              manager=manager)
    fps_label = UILabel(pygame.Rect((0, 30), (30, 30)),
                        "0",
                        manager=manager)
    song_label = UILabel(pygame.Rect((10, 400), (200, 22)),
                         _("Song position"),
                         manager=manager)
    volume_label = UILabel(pygame.Rect((225, 402), (130, 25)),
                           _("Volume {}").format(
                               round(float(config['CONFIG']['VOLUME']) * 100)),
                           manager=manager)

    box_labels = [start_label, end_label, vert_label, cue_label,
                  cuesheet_label, note_button_label, note_type_label]
    for label in box_labels:
        label.hide()

    # what the player is holding
    selected = None
    load_item_tex(current_controller, karaoke,
                  selected, note_picker)  # load button textures

    # load sheet textures and scale them
    sheet_tex = f"{texture_path}\\{assets['Sheet texture']}"
    line_tex = f"{texture_path}\\{assets['Line texture']}"
    sheet_bg = pygame.image.load(sheet_tex).convert()
    line_bg = pygame.image.load(line_tex).convert()
    line_bg = pygame.transform.scale(
        line_bg, (2, (karaoke.box_size + karaoke.border) * karaoke.rows))
    sheet_bg = pygame.transform.scale(
        sheet_bg, (karaoke.box_size + karaoke.border, (karaoke.box_size + karaoke.border) * karaoke.rows))

    # Horizontal ScrollBar
    thick_h = 30
    scrollbar_size = accurate_size - scr_size[0]
    scrollbar = UIHorizontalSlider(relative_rect=pygame.Rect(-3, scr_size[1] - thick_h + 2, 1605, thick_h),
                                   start_value=0,
                                   value_range=(0, scrollbar_size),
                                   manager=manager, object_id='#scrollbar')

    # volume slider
    volume_slider = UIHorizontalSlider(relative_rect=pygame.Rect((225, 430), (160, 25)),
                                       start_value=round(
                                           float(config['CONFIG']['VOLUME']) * 100),
                                       value_range=(0, 100),
                                       manager=manager, object_id="#volume_slider")
    music_elements = [song_label, volume_label,
                      play_button, volume_slider, music_box]
    for item in music_elements:
        item.hide()
    # what the player is currently editing
    currently_edited = None
    stopped_editing = False
    gui_button_mode = None
    open_file = None
    scrollbar_moved = False  # has scrollbar been moved yet
    loaded = False  # is audio file loaded
    audio_start_pos = 0  # audio start position
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
            scrollbar_moved = True
            scrollbar_add += 1
            diff = scrollbar_add // 4
            if key_pressed == 'right':
                if scrollbar.get_current_value() + diff <= scrollbar_size:
                    scrollbar.set_current_value(
                        scrollbar.get_current_value() + scrollbar_add)
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
                with open(settings_file, 'w', encoding='UTF-8') as configfile:  # save config
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
                    selected = Item(0, 0, note_id, 0, 0)  # add item
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
                    if scrollbar.get_current_value() + 1 <= scrollbar_size:
                        scrollbar.set_current_value(
                            scrollbar.get_current_value() + 1)
                    else:
                        scrollbar.set_current_value(scrollbar_size)

                if event.key in [pygame.K_LEFT, pygame.K_PAGEDOWN]:
                    key_pressed = 'left'
                    scrollbar_add = 0
                    if scrollbar.get_current_value() - 1 >= 0:
                        scrollbar.set_current_value(
                            scrollbar.get_current_value() - 1)
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
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=_('Are you sure you want to remove this note? This change cannot be undone.'), window_title=_('Delete note'), action_short_name=_('OK'))
                        delete_note.cancel_button.set_text(_('Cancel'))

                    selected = None  # deletes selected note
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LCTRL] and keys[pygame.K_s]:
                    gui_button_mode, output_selection = save_file(
                        open_file, manager)
                if event.key == pygame.K_LALT:
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
                                if karaoke.items[pos[0]][pos[1]].id < 4 and karaoke.items[pos[0]][pos[1]].note_type < 3:
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
                                if karaoke.items[pos[0]][pos[1]].id < 4 and karaoke.items[pos[0]][pos[1]].note_type < 3:
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
                if event.user_type == UI_BUTTON_START_PRESS:
                    if event.ui_element == load_kpm_button:
                        gui_button_mode = 'KPM_Input'
                        kpm_input_selection = UIFileDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, allow_existing_files_only=True, window_title=_('Select a parameter file (kpm)'), initial_file_path=Path(config['PATHS']['KPM_Input']))
                        kpm_input_selection.ok_button.set_text(_('OK'))
                        kpm_input_selection.cancel_button.set_text(_('Cancel'))

                    if event.ui_element == save_kpm_button:
                        gui_button_mode = 'KPM_Output'
                        kpm_output_selection = UIFileDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, window_title=_('Select an output file (kpm)'), initial_file_path=Path(config['PATHS']['KPM_Output']))
                        kpm_output_selection.ok_button.set_text(_('OK'))
                        kpm_output_selection.cancel_button.set_text(
                            _('Cancel'))
                    # music buttons
                    if event.ui_element == play_button:
                        if loaded:
                            if pygame.mixer.music.get_busy():  # if song is playing
                                play_button.set_text('▶')
                                pygame.mixer.music.stop()
                            else:
                                audio_start_pos = int(music_box.get_text())
                                # TODO - get a nicer button
                                play_button.set_text('▌▌')
                                try:
                                    pygame.mixer.music.play(
                                        start=(audio_start_pos / 1000))
                                except(pygame.error):  # Position not implemented for music type
                                    print(
                                        _('Unable to play the song from the given position, restarting from the beginning.'))
                                    audio_start_pos = 0
                                    pygame.mixer.music.play()
                    if event.ui_object_id == 'menu_bar.#file_menu_items.#open':
                        gui_button_mode = 'Input'
                        input_selection = UIFileDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, allow_existing_files_only=True, window_title=_('Select an input file (kbd)'), initial_file_path=Path(config['PATHS']['Input']))
                        input_selection.ok_button.set_text(_('OK'))
                        input_selection.cancel_button.set_text(_('Cancel'))
                    if event.ui_object_id == 'menu_bar.#file_menu_items.#new':
                        gui_button_mode = 'Reset'
                        reset_all = UIConfirmationDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=_('Are you sure you want to create a new file? Any unsaved changes will be lost.'), window_title=_('Create a new file'), action_short_name=_('OK'))
                        reset_all.cancel_button.set_text(_('Cancel'))
                    if event.ui_object_id == 'menu_bar.#file_menu_items.#save':
                        gui_button_mode, output_selection = save_file(
                            open_file, manager)
                    if event.ui_object_id == 'menu_bar.#music_menu_items.#load_song':
                        gui_button_mode = 'Music'
                        music_selection = UIFileDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, allow_existing_files_only=True, window_title=_('Select an audio file (mp3/ogg)'), initial_file_path=Path(config['PATHS']['Music']))
                        music_selection.ok_button.set_text(_('OK'))
                        music_selection.cancel_button.set_text(_('Cancel'))

                    if event.ui_object_id == 'menu_bar.#file_menu_items.#save_as':
                        gui_button_mode = 'Output'
                        output_selection = UIFileDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True, window_title=_('Select an output file (kbd)'), initial_file_path=Path(config['PATHS']['Output']))
                        output_selection.ok_button.set_text(_('OK'))
                        output_selection.cancel_button.set_text(_('Cancel'))

                    if event.ui_object_id == 'menu_bar.#help_menu_items.#how_to_use':
                        info_window_rect = pygame.Rect(0, 0, 500, 400)
                        info_window_rect.center = screen.get_rect().center

                        help_window = UIMessageWindow(rect=info_window_rect,
                                                      html_message=_('<b>How to use</b><br>'
                                                                     '---------------<br>'
                                                                     '<b>KUMA - A karaoke editor for Dragon Engine games.</b><br>'
                                                                     'To begin using the tool, you can add start by loading an existing file from <b>File</b> -> <b>Open</b> or just by adding notes to a new file.<br>'
                                                                     'You can choose your preferred <b>controller type</b> and <b>language</b> using the dropdown menus at the top of the screen.<br>'
                                                                     'When placing a note, the accuracy is <b>100 milliseconds</b>. You can change the position more accurately in <b>note edit mode.</b><br>'
                                                                     'You can play songs by loading them from the <b>Music</b> tab and then pressing the <b>Play</b> button in the left corner.<br>'
                                                                     'If you want to save, you can save by going to <b>File</b> -> <b>Save</b> or <b>Save as...</b> to either create a new file or overwrite an existing one.<br>'
                                                                     '---------------<br><br>'
                                                                     '<b>Key binds</b><br>'
                                                                     '---------------<br><br>'
                                                                     '<b>Left click</b> - Place and pick up notes.<br>'
                                                                     '<b>Right click</b> - Change held note type.<br>'
                                                                     '<b>Left Alt</b> - Change held note type to "Hold" note.<br>'
                                                                     '<b>Left Shift</b> - Change held note type to "Rapid" note.<br>'
                                                                     '<b>E</b> - Note edit mode. You can accurately change note timings, position, type and more. Pressing E again saves the note.<br>'
                                                                     '<b>Arrow keys, Page Up, Page Down</b> - Move the scrollbar.<br>'
                                                                     '<b>Delete</b> - Removes currently selected/edited note.<br>'
                                                                     '<b>End</b> - Jump to the last note.'),
                                                      manager=manager,
                                                      window_title=_('Help'))
                        help_window.dismiss_button.set_text(_('Close'))

                    if event.ui_object_id == 'menu_bar.#help_menu_items.#about':
                        about_window_rect = pygame.Rect(0, 0, 400, 300)
                        about_window_rect.center = screen.get_rect().center
                        about_window = UIMessageWindow(rect=about_window_rect,
                                                       html_message=_('<br><b>KUMA</b><br>'
                                                                      '---------------<br><br>'
                                                                      '<b>A karaoke editor for Dragon Engine games.<br>'
                                                                      '<b>Version: </b>{ver}<br>'
                                                                      '<b>Created by: </b>{creators}<br>'
                                                                      '<b>Icon by: </b>{mink}<br>'
                                                                      '<b>Testers: </b>{testers}<br>'
                                                                      '<b>Translators: </b>{translators}<br>').format(ver=VERSION, mink='Mink', creators='Timo654', testers=TESTERS, translators=TRANSLATORS),
                                                       manager=manager,
                                                       window_title=_('About'))
                        about_window.dismiss_button.set_text(_('Close'))

                if event.user_type == UI_TEXT_ENTRY_CHANGED and event.ui_object_id == "#song_position":
                    if not pygame.mixer.get_busy():
                        new_value = music_box.get_text()
                        if len(new_value) > 0:
                            new_pos = int(song_pos_to_scroll(
                                int(music_box.get_text()), karaoke))
                            scrollbar.set_current_value(new_pos)

                if event.user_type == UI_HORIZONTAL_SLIDER_MOVED and event.ui_object_id == '#volume_slider':
                    volume_value = volume_slider.get_current_value() / 100
                    pygame.mixer.music.set_volume(volume_value)
                    config.set("CONFIG", "VOLUME", str(volume_value))
                    volume_label.set_text(_('Volume {}').format(
                        volume_slider.get_current_value()))
                if event.ui_object_id == '#scrollbar':
                    scrollbar_moved = True

                if event.user_type == UI_BUTTON_PRESSED:
                    if gui_button_mode == 'Input':
                        if event.ui_element == input_selection.ok_button:
                            gui_button_mode = None
                            open_file = input_selection.current_file_path
                            if currently_edited:
                                stop_editing(boxes, box_labels,
                                             dropdowns, undo_button)
                                currently_edited = None
                            karaoke, can_save = load_kbd(
                                input_selection.current_file_path, karaoke, cutscene_box)
                            if can_save:
                                config.set("PATHS", "Input", str(
                                    input_selection.current_file_path))
                            currently_edited = None

                    if gui_button_mode == 'Output':
                        if event.ui_element == output_selection.ok_button:
                            gui_button_mode = None
                            open_file = output_selection.current_file_path
                            config.set("PATHS", "Output", str(
                                output_selection.current_file_path))
                            write_kbd(
                                output_selection.current_file_path, karaoke, cutscene_box)

                    if gui_button_mode == 'KPM_Input':
                        if event.ui_element == kpm_input_selection.ok_button:
                            kpm_data = load_kpm(
                                kpm_input_selection.current_file_path, cutscene_box)
                            if kpm_data:
                                config.set("PATHS", "KPM_Input", str(
                                    kpm_input_selection.current_file_path))
                    if gui_button_mode == 'KPM_Output':
                        if event.ui_element == kpm_output_selection.ok_button:
                            config.set("PATHS", "KPM_Output", str(
                                kpm_output_selection.current_file_path))
                            save_kpm(
                                kpm_output_selection.current_file_path, cutscene_box, kpm_data)

                    if gui_button_mode == 'Music':
                        if event.ui_element == music_selection.ok_button:
                            loaded, length = load_song(
                                music_selection.current_file_path, music_elements)
                            if loaded:
                                config.set("PATHS", "Music", str(
                                    music_selection.current_file_path))

                    if event.ui_element == undo_button:
                        gui_button_mode = 'Undo'
                        undo_note = UIConfirmationDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=_('Are you sure you want to undo changes made to this note?'), window_title=_('Undo changes'), action_short_name=_('OK'))
                        undo_note.cancel_button.set_text(_('Cancel'))

                if (event.user_type == UI_DROP_DOWN_MENU_CHANGED and event.ui_object_id == '#button_picker'):
                    config.set("CONFIG", "BUTTONS", str(
                        button_picker.selected_option))
                    load_item_tex(button_picker.selected_option,
                                  karaoke, selected, note_picker)
                if (event.user_type == UI_DROP_DOWN_MENU_CHANGED and event.ui_object_id == '#language_picker'):
                    config.set("CONFIG", "LANGUAGE", str(
                        language_picker.selected_option))
                    switch_language(language_picker.selected_option, params=[undo_button, load_kpm_button, save_kpm_button, cutscene_label, start_label,
                                                                             vert_label, cue_label, cuesheet_label, note_button_label, note_type_label, note_type_picker, end_label, menu_bar, song_label, volume_label])
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
                        if currently_edited.note_type != 0:
                            karaoke.Remove_long(
                                currently_edited.x, currently_edited.y)
                        karaoke.Remove(currently_edited.x, currently_edited.y)
                        stop_editing(boxes, box_labels, dropdowns, undo_button)
                        currently_edited = None
                    if gui_button_mode == 'Save':
                        if open_file != None:
                            write_kbd(
                                open_file, karaoke, cutscene_box)
                        else:
                            raise Exception(_('No open file, unable to save!'))

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

        if pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos() + audio_start_pos
            music_box.set_text(str(current_time))
            # make the scrollbar move when song is playing
            converted_time = song_pos_to_scroll(current_time, karaoke)
            scrollbar.set_current_value(converted_time)
        pygame.draw.line(screen, (222, 175, 74), (karaoke.x + karaoke.box_size // 2, karaoke.y + 10), (karaoke.x +
                                                                                                       karaoke.box_size // 2, ((karaoke.box_size + karaoke.border) * karaoke.rows) + 70), width=5)  # helpful line for music
        if scrollbar_moved:
            if loaded and not pygame.mixer.music.get_busy():
                # change the time when scrolling
                converted_scroll = scroll_to_song_pos(
                    scrollbar.get_current_value(), karaoke)
                if converted_scroll > length:
                    converted_scroll = length
                music_box.set_text(str(converted_scroll))
            scrollbar_moved = False

        fps_label.set_text(update_fps())
        manager.draw_ui(screen)
        manager.update(time_delta)
        pygame.display.update()


if __name__ == '__main__':
    main()
