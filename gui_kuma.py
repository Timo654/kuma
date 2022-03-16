import pygame
from pygame_gui import UIManager, UI_BUTTON_START_PRESS, UI_BUTTON_PRESSED, UI_DROP_DOWN_MENU_CHANGED, UI_CONFIRMATION_DIALOG_CONFIRMED, UI_HORIZONTAL_SLIDER_MOVED, UI_TEXT_ENTRY_CHANGED
from pygame_gui.windows import UIConfirmationDialog, UIMessageWindow
from pygame_gui.elements import UIDropDownMenu, UILabel, UIButton, UITextEntryLine, UIHorizontalSlider
import modules.parsers.de.kbd_reader as kbd
import modules.parsers.de.kpm_reader as kpm
import modules.importers.detect_filetype as detect_filetype
from modules.ui.ui_menu_bar import UIMenuBar
from pathlib import Path
from math import ceil, floor
import ctypes
from os import name
import tkinter as tk
from tkinter import filedialog
import json
import configparser
import gettext
import locale
import mutagen
import sys

# general info
VERSION = "v0.9.6"
CREATORS = 'Timo654'
TRANSLATORS = 'Timo654, ketrub, Mink, jason098, Capitán Retraso, Kent, Edness, JustAnyone, Tervel, RyuHachii, Foas, Biggelskog'
TESTERS = "ketrub, KaarelJ98, Ono Michio"
print("""
   _     _      _     _      _     _      _     _
  (c).-.(c)    (c).-.(c)    (c).-.(c)    (c).-.(c)
   / ._. \      / ._. \      / ._. \      / ._. \\
 __\( Y )/__  __\( Y )/__  __\( Y )/__  __\( Y )/__
(_.-/'-'\-._)(_.-/'-'\-._)(_.-/'-'\-._)(_.-/'-'\-._)
   || K ||      || U ||      || M ||      || A ||
 _.' `-' '._  _.' `-' '._  _.' `-' '._  _.' `-' '._
(.-./`-'\.-.)(.-./`-'\.-.)(.-./`-'\.-.)(.-./`-'\.-.)
 `-'     `-'  `-'     `-'  `-'     `-'  `-'     `-'   """ + VERSION + '\n\n')

# loading asset data from file
asset_file = 'assets.json'
if Path(asset_file).is_file():
    with open(asset_file, 'r', encoding='UTF-8') as json_file:
        assets = json.load(json_file)
else:
    raise Exception(_('Asset data missing'))
asset_path = assets['Assets folder']
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
    config.set("CONFIG", "RESOLUTION X", str(1600))
    config.set("CONFIG", "RESOLUTION Y", str(500))
    config.set("CONFIG", "FPS", str(100))
    config.set("CONFIG", "FPS COUNTER", str(0))
    config.set("CONFIG", "BUTTONS", controllers[0])
    config.set("CONFIG", "LANGUAGE", get_default_language())
    config.set("CONFIG", "VOLUME", str(1))
    config.set("CONFIG", "UNDO KBD LOAD", str(0))
if not config.has_section("PATHS"):
    config.add_section("PATHS")
    config.set("PATHS", "Input", f'{str(Path().resolve())}')
    config.set("PATHS", "Output", f'{str(Path().resolve())}')
    config.set("PATHS", "KPM_Input",
               f'{str(Path().resolve())}')
    config.set("PATHS", "KPM_Output",
               f'{str(Path().resolve())}')
    config.set("PATHS", "Import_Input",
               f'{str(Path().resolve())}')
    config.set("PATHS", "Music",
               f'{str(Path().resolve())}')
if not config.has_section("ADV. SETTINGS"):
    config.add_section("ADV. SETTINGS")
    config.set("ADV. SETTINGS", "NOTE",
               "DO NOT TOUCH THESE SETTINGS IF YOU DO NOT KNOW WHAT YOU'RE DOING, PLEASE.")
    config.set("ADV. SETTINGS", "NOTE2",
               "Scale is 1000 divided by scale. When editing column and surface values, make sure the column count divides by surface count.")
    config.set("ADV. SETTINGS", "COLUMNS", str(10000))
    config.set("ADV. SETTINGS", "SURFACES", str(8))
    config.set("ADV. SETTINGS", "SCALE", str(20))
    config.set("ADV. SETTINGS", "UNDO COUNT", str(50))

if config["CONFIG"]["FPS COUNTER"] == '1':
    fps_counter = True
else:
    fps_counter = False

# whether you should be able to undo a file load or not
if config["CONFIG"]["UNDO KBD LOAD"] == '1':
    undo_kbd = True
else:
    undo_kbd = False

undo_count = int(config["ADV. SETTINGS"]["UNDO COUNT"])

# fix UI getting too big when using a different scale from 100%
if name == 'nt':
    ctypes.windll.user32.SetProcessDPIAware()
# initialize pygame stuff
pygame.init()
font = pygame.font.SysFont("FiraCode", 22)
clock = pygame.time.Clock()
pygame.display.set_caption('KUMA')
pygame_icon = pygame.image.load(f"{asset_path}/textures/icon_small.png")
pygame.display.set_icon(pygame_icon)
pygame.mixer.music.set_volume(float(config["CONFIG"]["VOLUME"]))


# class for a item, holds the surface and data related to it


class Item:
    # default end pos, cue id and cuesheet id is 0
    def __init__(self, x, y, id, note_type, start_pos, end_pos=0, start_cue_id=0, start_cuesheet_id=0, end_cue_id=0, end_cuesheet_id=0, display_offset=0):
        self.id = id
        self.note_type = note_type
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.start_cue_id = start_cue_id
        self.start_cuesheet_id = start_cuesheet_id
        self.end_cue_id = end_cue_id
        self.end_cuesheet_id = end_cuesheet_id
        self.display_offset = display_offset
        self.surface = items[id]
        self.x = x
        self.y = y

    def resize(self, size):
        return pygame.transform.scale(self.surface, (size, size))


# the karaoke system


class Karaoke:
    def __init__(self):
        self.rows = 8
        # increasing this increases memory usage. only use values that can be divided by 2, please
        self.col = int(config['ADV. SETTINGS']['COLUMNS'])
        self.items = [[None for _ in range(self.rows)]
                      for _ in range(self.col)]
        self.box_size = 30
        self.x = 50
        self.y = 50
        # number to scale by
        self.scaler = int(config['ADV. SETTINGS']['SCALE'])
        # length of one box (ms)
        self.scale = 1000 // self.scaler
        self.border = 3
        self.undo_list = list()

    def undo(self):
        if len(self.undo_list) > 0:
            self.items = self.undo_list[-1]  # set last list as items
            self.undo_list.pop()

    def add_to_undo_list(self, prev_items):
        if prev_items != self.items:
            self.undo_list.append(prev_items)
            # the higher the max undo count, the more RAM it will use
            if len(self.undo_list) > undo_count:
                self.undo_list.pop(0)

    def reset_undo_list(self):
        self.undo_list.clear()

    def get_list(self):  # workaround for copying the list
        prev_list = list()
        for row in self.items:
            prev_list.append(row.copy())
        return prev_list

    # draw everything
    def draw(self, world, surface_nr, scroll, screen_width, sheet_bg, line_bg, world_count):
        # draw background
        surface2_offset = 0
        one_box = self.box_size + self.border
        if surface_nr > 0:
            x_coord = 0
            scroll -= (world.get_width() * surface_nr) - 50
            surface2_offset = int(self.col / world_count) * surface_nr
        else:
            x_coord = self.x

        col_start = (scroll // one_box - 2)
        col_end = col_start + (screen_width // one_box) + 2
        if surface_nr > 0:
            col_end += 2
        if col_end > (self.col // world_count):
            col_end = (self.col // world_count)

        # draw the karaoke sheet and lines every 2 seconds
        for i in range(col_start, col_end):
            world.blit(sheet_bg, (x_coord + (33 * (i)),
                                  self.y + self.box_size / 2))
            if (i + surface2_offset) % (self.scaler * 2) == 0:  # each 2 seconds
                current_time = self.format_time(i + surface2_offset)
                time_text = font.render(current_time, 1, pygame.Color("grey"))
                world.blit(time_text, (x_coord + (33 * (i)), 30))
                world.blit(line_bg, (x_coord + (one_box // 2) +
                                     (33 * (i)), self.y + self.box_size / 2))
        # draw the notes
        for x in range(col_start, col_end):
            for y in range(self.rows):
                rect = (x_coord + (self.box_size + self.border)*x + self.border, self.x +
                        (self.box_size + self.border)*y + self.border, self.box_size, self.box_size)
                if self.items[x + surface2_offset][y]:
                    world.blit(self.items[x + surface2_offset]
                               [y].resize(self.box_size), rect)

    # add a note
    def Add(self, Item):
        self.items[Item.x][Item.y] = Item

    # add a long note
    def Add_long(self, start_pos, end_pos, vert_pos, note_type, note_id):
        grid_start_pos = self.game_to_pos(start_pos)
        grid_end_pos = self.game_to_pos(end_pos)
        if note_type == 1:
            long_note_id = 4
        else:
            long_note_id = 5
        progress_value = 0
        for i in range(grid_start_pos + 1, grid_end_pos):
            progress_value += self.scale
            self.Add(Item(i, vert_pos, long_note_id,
                          note_type, start_pos + progress_value))
        # note type 3 is hold/rapid end, not an actual thing in the game
        self.Add(Item(grid_end_pos, vert_pos, note_id, 3, end_pos))

    # reset items
    def reset(self, file_undo=False):
        if not file_undo:  # if you can undo file loads
            self.reset_undo_list()
        self.items.clear()
        self.items = [[None for _ in range(self.rows)]
                      for _ in range(self.col)]

    # remove a note
    def Remove(self, x, y):
        if x < len(self.items):
            self.items[x][y] = None

    # remove a long note
    def Remove_long(self, x, y, y_pos=None, old_start_pos=None, new_end_pos=0):
        note = self.items[x][y]
        if y_pos == None:
            y_pos = note.y
        old_end_pos = self.game_to_pos(note.end_pos)
        start_pos = self.game_to_pos(note.start_pos)
        for i in range(old_end_pos + 1, new_end_pos, -1):
            if i == start_pos:
                break
            self.Remove(i, y_pos)

        # if there's rapid/hold parts before start position
        old_start_pos = self.game_to_pos(old_start_pos)
        if old_start_pos != None and old_start_pos != start_pos:
            for i in range(start_pos + 1, old_start_pos, -1):
                if i != start_pos:
                    self.Remove(i, y_pos)
        note = None

    # get the square that the mouse is over
    def Get_pos(self, scroll, world):
        mouse = pygame.mouse.get_pos()
        x = scroll + mouse[0]  # adjust for scrollbar
        y = mouse[1] - self.y
        surface_nr = int(x / world.get_width())
        if surface_nr == 0:
            x -= self.x
        x = x//(self.box_size + self.border)
        y = y//(self.box_size + self.border)
        return (x, y)

    # check whether the mouse in in the grid
    def In_grid(self, x, y):
        if (x < 0) or (y < 0) or (x >= self.col) or (y >= self.rows):
            return False
        return True

    def format_time(self, i):
        # display current time
        seconds = i // self.scaler
        minutes = seconds // 60
        if minutes:
            if seconds % 60 == 0:
                return _("{min} min").format(min=minutes)
            else:
                seconds = seconds - (minutes * 60)
                return _("{min} min {sec} s").format(min=minutes, sec=seconds)
        else:
            return _("{sec} s").format(sec=seconds)

    # convert game to grid pos
    def game_to_pos(self, pos):
        return normal_round(((pos / 3000) * self.scaler))

    # converts pos back to yakuza time
    def pos_to_game(self, pos):
        return normal_round((pos / self.scaler) * 3000)

    # convert song (audio) position to scroll
    def song_pos_to_scroll(self, position, world_width):
        scale = self.scale
        new_pos = (position / scale) * (self.box_size + self.border)
        if new_pos > world_width:
            # 1.5x note is difference for other surfaces
            return int(((position - (scale * 1.5)) / scale) * (self.box_size + self.border))
        else:
            return int(new_pos)

    # convert scroll position to song (audio) position
    def scroll_to_song_pos(self, position, world_width):
        scale = self.scale
        new_pos = int((position * (scale)) / (self.box_size + self.border))
        if new_pos < world_width:
            return new_pos
        else:
            return int(new_pos + (scale * 1.5))

# add notes to karaoke
    def add_notes_from_data(self, data):
        if undo_kbd:
            prev_list = self.get_list()
        self.reset(undo_kbd)  # reset data
        for note in data['Notes']:
            if note['Note type'] < 3:  # ignore any note types above 3, because those shouldn't exist
                start_pos = self.game_to_pos(note['Start position'])
                self.Add(Item(start_pos, note['Vertical position'], note['Button type'], note['Note type'],
                              note['Start position'], end_pos=note['End position'], start_cue_id=note['Start Cue ID'], start_cuesheet_id=note['Start Cuesheet ID'], end_cue_id=note['End Cue ID'], end_cuesheet_id=note['End Cuesheet ID']))
                if note['Note type'] != 0:  # if note is hold or rapid
                    self.Add_long(note['Start position'], note['End position'],
                                  note['Vertical position'], note['Note type'], note['Button type'])
        if undo_kbd:
            self.add_to_undo_list(prev_list)

# file importing code
    def import_file(self, file):
        file = Path(file)  # ensure it is actually path
        try:
            data = detect_filetype.load_file(file)
            print(_('File loaded.'))
        # except(ValueError):
        #    print(_('Unable to read file.'))
        #    return
        except(PermissionError):
            print(_('Unable to open file.'))
            return
        else:
            self.add_notes_from_data(data)

    # KBD loading code
    def load_kbd(self, file, cutscene_box):
        file = Path(file)  # ensure it is actually path
        try:
            data = kbd.read_file(file)
            print(_('File loaded.'))
        except(ValueError):
            print(_('Unable to read file.'))
            return False, None
        except(PermissionError):
            print(_('Unable to open file.'))
            return False, None
        else:
            self.add_notes_from_data(data)
            kpm_file = f"{str(file.parent)}/{file.stem.split('_')[0]}_param.kpm"
            if Path(kpm_file).exists():
                kpm_data = load_kpm(kpm_file, cutscene_box)
                return True, kpm_data
        return True, None

    # KBD writing code
    def write_kbd(self, file, cutscene_box):
        data = dict()
        note_list = list()
        x = 0
        while x < len(self.items):
            y = 0
            while y < len(self.items[x]):
                if self.items[x][y] != None:
                    if self.items[x][y].id <= 3 and self.items[x][y].note_type < 3:  # if not End
                        current_note = self.items[x][y]
                        note = dict()
                        note['Start position'] = current_note.start_pos
                        note['End position'] = 0
                        note['Vertical position'] = y
                        note['Button type'] = current_note.id
                        note['Note type'] = current_note.note_type
                        # doesnt seem to do anything
                        note['Display offset'] = current_note.display_offset
                        note['Start Cue ID'] = current_note.start_cue_id
                        note['Start Cuesheet ID'] = current_note.start_cuesheet_id
                        note['End Cue ID'] = current_note.end_cue_id
                        note['End Cuesheet ID'] = current_note.end_cuesheet_id
                        if current_note.end_pos > 0:
                            note['End position'] = current_note.end_pos
                        else:
                            if self.items[x+1][y] != None:
                                if self.items[x+1][y].id > 3:
                                    o = x + 1
                                    note['Note type'] = self.items[o][y].note_type
                                    while self.items[o][y].id > 3:
                                        o += 1
                                    self.items[o][y].note_type = 3  # End
                                    note['End position'] = self.pos_to_game(o)
                                    current_note.end_pos = note['End position']
                        note_list.append(note)
                y += 1
            x += 1
        data['Notes'] = note_list
        data['Header'] = dict()
        data['Header']['Version'] = 2
        kbd.write_file(data, file, cutscene_start=float(
            cutscene_box.get_text()))
        print(_("File written to {}").format(file))

    # draw a square around a note
    def highlight_note(self, note, color, worlds, surface_nr, next_surface):
        x = 2 + (note.x * (self.box_size + self.border))
        y = 2 + self.y + \
            (note.y * (self.box_size + self.border))
        if surface_nr == 0:
            x += self.x
        if x > worlds[0].get_width() * (surface_nr + 1) and len(worlds) > next_surface:
            pygame.draw.rect(worlds[next_surface], color, (x - worlds[0].get_width() * next_surface, y, self.box_size + self.border,
                                                           self.box_size + self.border), 3)
        else:
            pygame.draw.rect(worlds[surface_nr], color, (x - worlds[0].get_width() * surface_nr, y, self.box_size + self.border,
                                                         self.box_size + self.border), 3)

    # save note changes when stopping editing
    def save_note(self, note, boxes, dropdowns):
        prev_list = self.get_list()
        max_pos = (self.col - 1) * self.scale
        vert_changed = False
        old_start_pos = note.start_pos
        # start position
        if len(boxes[0].get_text()) > 0:
            if float(boxes[0].get_text()) <= max_pos:
                new_pos = ms_to_game(float(boxes[0].get_text()))
                if self.game_to_pos(new_pos) <= len(self.items):
                    note.start_pos = new_pos
                    self.items[note.x][note.y] = None
                    note.x = self.game_to_pos(note.start_pos)
                    self.items[note.x][note.y] = note
        # vertical position
        if len(boxes[2].get_text()) > 0:
            if int(boxes[2].get_text()) < self.rows:
                if note.y != int(boxes[2].get_text()):
                    vert_changed = True
                    old_pos = note.y
                self.items[note.x][note.y] = None
                note.y = int(boxes[2].get_text())
                self.items[note.x][note.y] = note
        # start cue id
        if len(boxes[3].get_text()) > 0:
            if int(boxes[3].get_text()) <= 65535:  # uint16 max
                note.start_cue_id = int(boxes[3].get_text())
        # start cuesheet id
        if len(boxes[4].get_text()) > 0:
            if int(boxes[4].get_text()) <= 65535:  # uint16 max
                note.end_cue_id = int(boxes[4].get_text())
        # end cue id
        if len(boxes[5].get_text()) > 0:
            if int(boxes[5].get_text()) <= 65535:  # uint16 max
                note.start_cuesheet_id = int(boxes[5].get_text())
        # end cuesheet id
        if len(boxes[6].get_text()) > 0:
            if int(boxes[6].get_text()) <= 65535:  # uint16 max
                note.end_cuesheet_id = int(boxes[6].get_text())
        # note id
        note.id = dropdowns[0].options_list.index(dropdowns[0].selected_option)
        # note type
        note.note_type = dropdowns[1].options_list.index(
            dropdowns[1].selected_option)
        note.surface = items[note.id]

        # end position
        if len(boxes[1].get_text()) > 0:
            if float(boxes[1].get_text()) <= max_pos:
                if note.note_type != 0:
                    end_pos = ms_to_game(float(boxes[1].get_text()))
                else:
                    end_pos = 0
                if end_pos < note.end_pos or vert_changed or old_start_pos < note.start_pos:
                    if vert_changed:
                        y_pos = old_pos
                        new_end_pos = 0
                    else:
                        y_pos = note.y
                        new_end_pos = self.game_to_pos(end_pos)
                    self.Remove_long(note.x, note.y, y_pos=y_pos, old_start_pos=old_start_pos,
                                     new_end_pos=new_end_pos)
                    if vert_changed:
                        y_pos = note.y
                        end_pos = ms_to_game(float(boxes[1].get_text()))
                if end_pos > note.start_pos:
                    note.end_pos = end_pos
                    self.Add_long(note.start_pos, note.end_pos,
                                  note.y, note.note_type, note.id)
                else:
                    note.end_pos = 0
        self.add_to_undo_list(prev_list)

    # Loading textures
    def load_item_tex(self, button_type, held_note, dropdown):
        global items
        # load note textures
        tex_name = f"{asset_path}/textures/{assets['Button prompts'][button_type][0]}"
        image = pygame.image.load(tex_name).convert_alpha()
        buttons = strip_from_sheet(image, (0, 0), (122, 122), 2, 2)
        items = [pygame.Surface((122, 122), pygame.SRCALPHA) for _ in range(6)]
        items[0].blit(buttons[1], (0, 0))  # circle
        items[1].blit(buttons[3], (0, 0))  # cross
        items[2].blit(buttons[2], (0, 0))  # square
        items[3].blit(buttons[0], (0, 0))  # triangle
        pygame.draw.line(items[4], (0, 109, 198),
                         (0, 61), (144, 61), 61)  # hold
        pygame.draw.line(items[5], (198, 0, 99),
                         (0, 61), (144, 61), 61)  # rapid

        for x in range(0, self.col):  # change existing button's texture
            for y in range(self.rows):
                if self.items[x][y]:
                    button_id = self.items[x][y].id
                    self.items[x][y].surface = items[button_id]

        if held_note:
            held_note.surface = items[held_note.id]

        update_dropdown(dropdown, mode='update all', new_list=assets['Button prompts']
                        [button_type][1], index=dropdown.options_list.index(dropdown.selected_option))

    # paste copied notes
    def paste(self, currently_copied, worlds, scrollbar_value, mode='boring'):
        if mode == 'cooler':  # advanced copy paste
            cool = True
        else:
            cool = False

        if len(currently_copied) > 0:
            prev_list = self.get_list()
            new_notes = list()
            for note in currently_copied:
                new_notes.append(
                    (note.start_pos, note.end_pos, note.y, note.id, note.note_type, note.start_cue_id, note.end_cue_id, note.start_cuesheet_id, note.end_cuesheet_id))
            new_notes.sort()
            x_offset = new_notes[0][0]
            if cool:
                y_offset = new_notes[0][2]
            mouse_pos = self.Get_pos(scrollbar_value, worlds[0])
            current_loc = self.pos_to_game(mouse_pos[0])  # where the cursor is
            for note in new_notes:
                if note[4] != 0:
                    end_pos = note[1] - \
                        x_offset + current_loc
                else:
                    end_pos = 0
                start_pos = note[0] - \
                    x_offset + current_loc
                grid_start_pos = self.game_to_pos(
                    start_pos)
                y_pos = note[2]
                if cool:  # adjust y position
                    y_pos += mouse_pos[1] - y_offset

                if self.In_grid(grid_start_pos, y_pos):
                    self.Add(Item(grid_start_pos, y=y_pos, id=note[3], note_type=note[4],
                                  start_pos=start_pos, end_pos=end_pos, start_cue_id=note[5], end_cue_id=note[6], start_cuesheet_id=note[7], end_cuesheet_id=note[8]))
                    if note[4] != 0:
                        self.Add_long(
                            start_pos, end_pos, y_pos, note[4], note[3])
            self.add_to_undo_list(prev_list)

# strip from sheet https://python-forum.io/thread-403.html


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


# load karaoke param
def load_kpm(file, cutscene_box, refresh=1):
    try:
        data = kpm.read_file(file)
    except(ValueError):
        print(_('Unable to read file.'))
        return None
    except(PermissionError):
        print(_('Unable to open file.'))
        return None
    else:
        if refresh:
            cutscene_box.set_text(
                str(data['Parameters'][0]['Cutscene start time']))
        return data

# save karaoke param


def save_kpm(file, cutscene_box, data):
    if Path.exists(file):
        data = load_kpm(file, cutscene_box, refresh=0)
    if data != None:
        data['Parameters'][0]['Cutscene start time'] = float(
            cutscene_box.get_text())
        kpm.write_file(data, file)
        print(_("KPM written to {}").format(file))
        return data


# update values
def update_text_boxes(note, boxes, dropdowns):
    # set values
    boxes[0].set_text(str(game_to_ms(note.start_pos)))
    boxes[1].set_text(str(game_to_ms(note.end_pos)))
    boxes[2].set_text(str(note.y))
    boxes[3].set_text(str(note.start_cue_id))
    boxes[4].set_text(str(note.end_cue_id))
    boxes[5].set_text(str(note.start_cuesheet_id))
    boxes[6].set_text(str(note.end_cuesheet_id))
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


# hide ui after stopping editing
def stop_editing(boxes, box_labels, dropdowns, undo_button):
    for box in boxes:
        box.hide()
        for label in box_labels:
            label.hide()
        for dropdown in dropdowns:
            dropdown.hide()
        undo_button.hide()


# loading a song
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
        print(_('Song loaded.'))
    except(pygame.error):
        for element in music_elements:
            element.hide()
        print(_('Unable to read file.'))
        return False, -1
    return True, length


# language switching
def switch_language(language, params=None, boot=False):
    lang_code = assets['Languages'][language]
    lang = gettext.translation(
        lang_code, localedir=f'{asset_path}/locales', languages=[lang_code])
    lang.install()
    _ = lang.gettext
    if not boot:
        print(_('Language changed.'))
        update_text(params)

# menu bar data


def get_menu_data():
    return {'#file_menu': {'display_name': _('File'),
                           'items':
                           {
        '#new': {'display_name': _('New...')},
        '#open': {'display_name': _('Open...')},
        '#save': {'display_name': _('Save')},
        '#save_as': {'display_name': _('Save As...')},
        '#import': {'display_name': _('Import')}
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

# update button text


def update_text(params):
    params[0].set_text(_('Undo note changes'))
    params[1].set_text(_('Load time'))
    params[2].set_text(_('Save time'))
    params[3].set_text(_('Cutscene start'))
    params[4].set_text(_('Start position'))
    params[5].set_text(_('Vertical position'))
    params[6].set_text(_('Start Cue ID'))
    params[7].set_text(_('Start Cuesheet ID'))
    params[8].set_text(_('Start Cue ID'))
    params[9].set_text(_('Start Cuesheet ID'))
    params[10].set_text(_('Note button'))
    params[11].set_text(_('Note type'))
    params[13].set_text(_('End position'))
    update_dropdown(params[12], mode='update all', new_list=[_('Regular'), _('Hold'), _(
        'Rapid')], index=params[12].options_list.index(params[12].selected_option))
    menu_data = get_menu_data()
    # params[14].set_text(menu_data)
    params[15].set_text(_("Song position"))
    params[16].set_text(_("Volume {}").format(
        round(float(config['CONFIG']['VOLUME']) * 100)))

# save box


def save_file(open_file, manager, karaoke, cutscene_box):
    if open_file != None:
        save = UIConfirmationDialog(
            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=_("Are you sure you want to overwrite {}?").format(open_file), window_title=_('Save file'), action_short_name=_('OK'), object_id='#save_overwrite')
        save.cancel_button.set_text(_('Cancel'))
        return open_file
    else:
        output_selection = filedialog.asksaveasfilename(
            title='Save karaoke button data', initialdir=config['PATHS']['Output'], defaultextension='.kbd', filetypes=[("Dragon Engine karaoke data", "*.kbd")])
        if len(output_selection) == 0:
            return None  # empty

        print('maybe')
        open_file = output_selection
        config.set("PATHS", "Output", str(
            output_selection))
        karaoke.write_kbd(
            output_selection, cutscene_box)
        return output_selection

# the main loop where all the cool stuff happens


def main():
    # make a tkinter root window for file dialogs
    root = tk.Tk()
    root.withdraw()
    # load language
    current_language = config['CONFIG']['LANGUAGE']
    if current_language not in languages:
        current_language = languages[0]
        config.set("CONFIG", "LANGUAGE", current_language)
    switch_language(current_language, boot=True)

    # get current controller
    current_controller = config['CONFIG']['BUTTONS']
    if current_controller not in controllers:
        current_controller = controllers[0]
        config.set("CONFIG", "BUTTONS", current_controller)

    # size limits, the UI breaks below this
    if int(config["CONFIG"]["RESOLUTION X"]) < 1100:
        config.set("CONFIG", "RESOLUTION X", str(1100))
    if int(config["CONFIG"]["RESOLUTION X"]) < 480:
        config.set("CONFIG", "RESOLUTION Y", str(480))

    scr_size = (int(config["CONFIG"]["RESOLUTION X"]),
                int(config["CONFIG"]["RESOLUTION Y"]))
    screen = pygame.display.set_mode((scr_size))
    karaoke = Karaoke()
    accurate_size = (karaoke.col) * (karaoke.box_size + karaoke.border)

    # number of surfaces, must be able to divide column count, otherwise it will break
    world_count = int(config['ADV. SETTINGS']['SURFACES'])

    if karaoke.col % world_count != 0:
        raise ValueError(
            'Karaoke column amount not dividable by surface count! Please change the values.')

    worlds = [pygame.Surface(
        (int(accurate_size / world_count), int(scr_size[1])), pygame.SRCALPHA, 32) for x in range(world_count)]

    if worlds[0].get_width() > 65535:
        raise ValueError(
            'Surface size is too big! Increase surface or decrease column count!')

    # ui manager
    manager = UIManager(scr_size, theme_path=f'{asset_path}/ui_theme.json')
    # menu bar related things, menu bar from https://github.com/MyreMylar/pygame_paint
    menu_data = get_menu_data()
    menu_bar = UIMenuBar(relative_rect=pygame.Rect(0, 0, scr_size[0], 25),
                         menu_item_data=menu_data,
                         manager=manager)
    # buttons
    undo_button = UIButton(relative_rect=pygame.Rect((1205, 400), (230, 30)),
                           text=_('Undo note changes'),
                           manager=manager, object_id='#undo_button')
    undo_button.hide()
    load_kpm_button = UIButton(relative_rect=pygame.Rect((215, 340), (150, 30)),
                               text=_('Load time'),
                               manager=manager, object_id='#load_kpm')
    save_kpm_button = UIButton(relative_rect=pygame.Rect((215, 365), (150, 30)),
                               text=_('Save time'), object_id='#save_kpm',
                               manager=manager)
    play_button = UIButton(relative_rect=pygame.Rect((345, 400), (30, 30)),
                           text='▶',
                           manager=manager, object_id='#play_button')

    # dropdown menus
    button_picker = UIDropDownMenu(options_list=controllers,
                                   starting_option=current_controller,
                                   relative_rect=pygame.Rect(240, 0, 200, 25),
                                   manager=manager, object_id='#button_picker')

    language_picker = UIDropDownMenu(options_list=languages,
                                     starting_option=current_language,
                                     relative_rect=pygame.Rect(
                                         440, 0, 150, 25),
                                     manager=manager, object_id='#language_picker')

    note_picker = UIDropDownMenu(options_list=assets['Button prompts'][current_controller][1],
                                 starting_option=assets['Button prompts'][current_controller][1][0],
                                 relative_rect=pygame.Rect(700, 365, 150, 30),
                                 manager=manager, object_id='#note_picker')

    note_types = [_('Regular'), _('Hold'), _('Rapid')]
    note_type_picker = UIDropDownMenu(options_list=note_types,
                                      starting_option=note_types[0],
                                      relative_rect=pygame.Rect(
                                          855, 365, 200, 30),
                                      manager=manager, object_id='#type_picker')

    dropdowns = [note_picker, note_type_picker]  # hide some dropdowns
    for dropdown in dropdowns:
        dropdown.hide()

    # textboxes
    valid_chars = [str(x) for x in range(0, 10)] + ['.']
    cutscene_box = UITextEntryLine(relative_rect=pygame.Rect(
        (10, 365), (200, 30)), manager=manager)
    cutscene_box.set_text(str(0))
    start_box = UITextEntryLine(relative_rect=pygame.Rect(
        (385, 365), (150, 30)), manager=manager)
    end_box = UITextEntryLine(relative_rect=pygame.Rect(
        (540, 365), (150, 30)), manager=manager)
    vert_box = UITextEntryLine(relative_rect=pygame.Rect(
        (385, 425), (170, 30)), manager=manager)
    start_cue_box = UITextEntryLine(relative_rect=pygame.Rect(
        (565, 425), (150, 30)), manager=manager)
    start_cuesheet_box = UITextEntryLine(relative_rect=pygame.Rect(
        (725, 425), (150, 30)), manager=manager)
    end_cue_box = UITextEntryLine(relative_rect=pygame.Rect(
        (885, 425), (150, 30)), manager=manager)
    end_cuesheet_box = UITextEntryLine(relative_rect=pygame.Rect(
        (1045, 425), (150, 30)), manager=manager)
    music_box = UITextEntryLine(relative_rect=pygame.Rect(
        (10, 425), (200, 30)), manager=manager, object_id="#song_position")
    music_box.set_text(str(0))

    boxes = [start_box, end_box, vert_box, start_cue_box,
             end_cue_box, start_cuesheet_box, end_cuesheet_box]

    for i in range(len(boxes)):
        if i == 2:
            valid_chars.pop()
        boxes[i].set_allowed_characters(valid_chars)
        boxes[i].hide()
    music_box.set_allowed_characters(valid_chars)

    # labels
    cutscene_label = UILabel(pygame.Rect((10, 340), (-1, 22)),
                             _("Cutscene start"),
                             manager=manager)
    start_label = UILabel(pygame.Rect((385, 340), (-1, 22)),
                          _("Start position"),
                          manager=manager)
    end_label = UILabel(pygame.Rect((540, 340), (-1, 22)),
                        _("End position"),
                        manager=manager)
    vert_label = UILabel(pygame.Rect((385, 400), (-1, 22)),
                         _("Vertical position"),
                         manager=manager)
    start_cue_label = UILabel(pygame.Rect((565, 400), (-1, 22)),
                              _("Start Cue ID"),
                              manager=manager)
    start_cuesheet_label = UILabel(pygame.Rect((725, 400), (-1, 22)),
                                   _("Start Cuesheet ID"),
                                   manager=manager)
    end_cue_label = UILabel(pygame.Rect((885, 400), (-1, 22)),
                            _("End Cue ID"),
                            manager=manager)
    end_cuesheet_label = UILabel(pygame.Rect((1045, 400), (-1, 22)),
                                 _("End Cuesheet ID"),
                                 manager=manager)
    note_button_label = UILabel(pygame.Rect((700, 340), (-1, 22)),
                                _("Note button"),
                                manager=manager)
    note_type_label = UILabel(pygame.Rect((855, 340), (-1, 22)),
                              _("Note type"),
                              manager=manager)
    if fps_counter:
        fps_label = UILabel(pygame.Rect((0, 30), (30, 30)),
                            "0",
                            manager=manager)
    song_label = UILabel(pygame.Rect((10, 400), (-1, 22)),
                         _("Song position"),
                         manager=manager)
    volume_label = UILabel(pygame.Rect((215, 402), (-1, 25)),
                           _("Volume {}").format(
                               round(float(config['CONFIG']['VOLUME']) * 100)),
                           manager=manager)

    box_labels = [start_label, end_label, vert_label, start_cue_label, end_cue_label,
                  start_cuesheet_label, end_cuesheet_label, note_button_label, note_type_label]
    for label in box_labels:
        label.hide()

    karaoke.load_item_tex(current_controller,
                          None, note_picker)  # load button textures

    # load sheet textures and scale them
    sheet_tex = f"{asset_path}/textures/{assets['Sheet texture']}"
    line_tex = f"{asset_path}/textures/{assets['Line texture']}"
    sheet_bg = pygame.image.load(sheet_tex).convert()
    line_bg = pygame.image.load(line_tex).convert()
    line_bg = pygame.transform.scale(
        line_bg, (2, (karaoke.box_size + karaoke.border) * karaoke.rows))
    sheet_bg = pygame.transform.scale(
        sheet_bg, (karaoke.box_size + karaoke.border, (karaoke.box_size + karaoke.border) * karaoke.rows))

    # Horizontal ScrollBar
    thick_h = 30
    scrollbar_size = accurate_size - scr_size[0]
    scrollbar = UIHorizontalSlider(relative_rect=pygame.Rect(-3, scr_size[1] - thick_h + 2, scr_size[0] + 5, thick_h),
                                   start_value=0,
                                   value_range=(0, scrollbar_size),
                                   manager=manager, object_id='#scrollbar')

    # volume slider
    volume_slider = UIHorizontalSlider(relative_rect=pygame.Rect((215, 430), (160, 25)),
                                       start_value=round(
                                           float(config['CONFIG']['VOLUME']) * 100),
                                       value_range=(0, 100),
                                       manager=manager, object_id="#volume_slider")
    music_elements = [song_label, volume_label,
                      play_button, volume_slider, music_box]
    for item in music_elements:
        item.hide()

    if len(sys.argv) > 1:
        if Path(sys.argv[1]).is_file():
            can_save, kpm_data = karaoke.load_kbd(
                sys.argv[1], cutscene_box)
    else:
        kpm_data = None

    # what the player is holding
    held_note = None
    # what the player is currently editing
    currently_edited = None
    currently_selected = list()  # make lists
    currently_copied = list()
    stopped_editing = False
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
        surface_nr = int(scrollbar_value / worlds[0].get_width())
        next_surface = int(
            (scrollbar_value + screen.get_width() + 50) / worlds[0].get_width())
        # draw surfaces
        if surface_nr != next_surface and world_count > next_surface:
            world_end = worlds[0].get_width(
            ) - (scrollbar_value - (worlds[0].get_width() * surface_nr))
            if world_end > 0:
                worlds[surface_nr].fill((fill_colour), rect=pygame.Rect(
                    scrollbar_value - worlds[0].get_width() * surface_nr, 0, world_end, scr_size[1]))  # clean the screen
                worlds[next_surface].fill((fill_colour), rect=pygame.Rect(
                    scrollbar_value - worlds[0].get_width() * next_surface, 0, scr_size[0], scr_size[1]))  # clean the screen
                karaoke.draw(worlds[surface_nr], surface_nr, scrollbar_value,
                             scr_size[0], sheet_bg, line_bg, world_count)
                karaoke.draw(worlds[next_surface], next_surface, scrollbar_value,
                             scr_size[0], sheet_bg, line_bg, world_count)
        else:
            worlds[surface_nr].fill((fill_colour), rect=pygame.Rect(
                scrollbar_value - worlds[0].get_width() * surface_nr, 0, scr_size[0], scr_size[1]))  # clean the screen
            karaoke.draw(worlds[surface_nr], surface_nr, scrollbar_value,
                         scr_size[0], sheet_bg, line_bg, world_count)

        mousex, mousey = pygame.mouse.get_pos()
        mousex += scrollbar_value  # adjust for scrollbar

        # scrollbar moving with arrow/page keys
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
        if held_note:
            if mousex > worlds[0].get_width() * (surface_nr + 1) and world_count > next_surface:
                worlds[next_surface].blit(held_note.resize(20),
                                          (mousex - worlds[0].get_width() * next_surface, mousey))
            else:
                worlds[surface_nr].blit(held_note.resize(
                    20), (mousex - worlds[0].get_width() * surface_nr, mousey))

        # if editing note params
        if currently_edited:
            karaoke.highlight_note(currently_edited,
                                   (0, 100, 255), worlds, surface_nr, next_surface)

        for note in currently_selected:
            karaoke.highlight_note(note, (255, 0, 0),
                                   worlds, surface_nr, next_surface)

        # Application events
        events = pygame.event.get()
        for event in events:
            # quit the app
            if event.type == pygame.QUIT:
                with open(settings_file, 'w', encoding='UTF-8') as configfile:  # save config
                    config.write(configfile)
                print('(^ _ ^)/')
                sys.exit()
            # add / move notes
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # if right clicked, get a note
                if event.button == 3:  # right click
                    if held_note == None:
                        pass
                    else:
                        if note_id < 3:
                            note_id += 1
                        else:
                            note_id = 0
                    held_note = Item(0, 0, note_id, 0, 0)  # add item
                elif event.button == 1:  # left click
                    prev_list = karaoke.get_list()
                    pos = karaoke.Get_pos(
                        scrollbar_value, worlds[0])
                    if karaoke.In_grid(pos[0], pos[1]):
                        if held_note:
                            held_note.start_pos = karaoke.pos_to_game(pos[0])
                            held_note.x = pos[0]
                            held_note.y = pos[1]
                            held_note = karaoke.Add(held_note)
                        elif karaoke.items[pos[0]][pos[1]]:
                            if karaoke.items[pos[0]][pos[1]] != currently_edited:
                                held_note = karaoke.items[pos[0]][pos[1]]
                                karaoke.items[pos[0]][pos[1]] = None
                    karaoke.add_to_undo_list(prev_list)

            # key no longer pressed
            if event.type == pygame.KEYUP:
                if keys[pygame.K_RIGHT] or keys[pygame.K_LEFT] or keys[pygame.K_PAGEDOWN] or keys[pygame.K_PAGEUP]:
                    key_pressed = None  # to stop scrollbars from scrolling
            # key presses
            elif event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                # scrollbar moving
                # scroll right
                if keys[pygame.K_RIGHT] or keys[pygame.K_PAGEUP]:
                    key_pressed = 'right'
                    scrollbar_add = 0
                    if scrollbar.get_current_value() + 1 <= scrollbar_size:
                        scrollbar.set_current_value(
                            scrollbar.get_current_value() + 1)
                    else:
                        scrollbar.set_current_value(scrollbar_size)
                # scroll left
                elif keys[pygame.K_LEFT] or keys[pygame.K_PAGEDOWN]:
                    key_pressed = 'left'
                    scrollbar_add = 0
                    if scrollbar.get_current_value() - 1 >= 0:
                        scrollbar.set_current_value(
                            scrollbar.get_current_value() - 1)
                    else:
                        scrollbar.set_current_value(0)

                # go back to the start
                elif keys[pygame.K_HOME]:
                    scrollbar.set_current_value(1)

                # move scrollbar to last note
                elif keys[pygame.K_END]:
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

                # UI related functions
                # delete notes
                elif keys[pygame.K_DELETE]:
                    if currently_edited:
                        delete_note = UIConfirmationDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=_('Are you sure you want to remove this note?'), window_title=_('Delete note'), action_short_name=_('OK'), object_id='#delete_one')
                        delete_note.cancel_button.set_text(_('Cancel'))
                    elif currently_selected:
                        delete_note = UIConfirmationDialog(
                            rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=_('Are you sure you want to remove these notes?'), window_title=_('Delete note'), action_short_name=_('OK'), object_id='#delete_multi')
                        delete_note.cancel_button.set_text(_('Cancel'))

                    held_note = None  # deletes selected note

                # save file
                elif keys[pygame.K_LCTRL] and keys[pygame.K_s]:
                    output_selection = save_file(
                        open_file, manager, karaoke, cutscene_box)
                    open_file = output_selection
                # select notes
                elif keys[pygame.K_LCTRL] and keys[pygame.K_f]:  # select notes
                    pos = karaoke.Get_pos(scrollbar_value, worlds[0])
                    if karaoke.items[pos[0]][pos[1]] not in currently_selected:
                        if karaoke.In_grid(pos[0], pos[1]):
                            if not currently_edited:
                                if karaoke.items[pos[0]][pos[1]] != None:
                                    if karaoke.items[pos[0]][pos[1]].id < 4 and karaoke.items[pos[0]][pos[1]].note_type < 3:
                                        currently_selected.append(
                                            karaoke.items[pos[0]][pos[1]])
                    else:
                        currently_selected.remove(
                            karaoke.items[pos[0]][pos[1]])

                elif keys[pygame.K_LCTRL] and keys[pygame.K_c]:  # copy notes
                    currently_copied = currently_selected.copy()

                elif keys[pygame.K_LCTRL] and keys[pygame.K_v] and keys[pygame.K_LSHIFT]:  # paste notes
                    karaoke.paste(currently_copied, worlds,
                                  scrollbar_value, mode='cooler')

                elif keys[pygame.K_LCTRL] and keys[pygame.K_v]:  # paste notes
                    karaoke.paste(currently_copied, worlds, scrollbar_value)

                elif keys[pygame.K_LCTRL] and keys[pygame.K_z]:  # undo
                    karaoke.undo()

                elif event.key == pygame.K_ESCAPE:
                    currently_selected.clear()  # empty list

                elif event.key == pygame.K_e:  # property editing mode
                    pos = karaoke.Get_pos(
                        scrollbar_value, worlds[0])
                    if not currently_edited:
                        if karaoke.In_grid(pos[0], pos[1]):
                            if karaoke.items[pos[0]][pos[1]] not in currently_selected:
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
                                            currently_edited, boxes, dropdowns)

                    else:
                        if karaoke.In_grid(pos[0], pos[1]):
                            if karaoke.items[pos[0]][pos[1]] != currently_edited and karaoke.items[pos[0]][pos[1]] != None:
                                if karaoke.items[pos[0]][pos[1]].id < 4 and karaoke.items[pos[0]][pos[1]].note_type < 3:
                                    karaoke.save_note(
                                        currently_edited, boxes, dropdowns)
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
                            karaoke.save_note(
                                currently_edited, boxes, dropdowns)
                            stopped_editing = False  # reset value
                            currently_edited = None  # deselect
                            stop_editing(boxes, box_labels,
                                         dropdowns, undo_button)

            elif event.type == UI_BUTTON_START_PRESS:
                # delete held button when entering menu bar to prevent accidentally adding notes
                if event.ui_element in menu_bar.menu_bar_container.elements:
                    held_note = None
                elif event.ui_element == load_kpm_button:
                    kpm_input_selection = filedialog.askopenfilename(title='Select a karaoke parameter file', filetypes=[
                                                                     ("Karaoke parameter", "*.kpm")], initialdir=config['PATHS']['KPM_Input'])
                    if len(kpm_input_selection) != 0:
                        kpm_data = load_kpm(
                            kpm_input_selection, cutscene_box)
                        if kpm_data:
                            config.set("PATHS", "KPM_Input", str(
                                kpm_input_selection))
                elif event.ui_element == save_kpm_button:
                    kpm_output_selection = filedialog.asksaveasfilename(
                        title='Save karaoke parameter file', initialdir=config['PATHS']['KPM_Output'], defaultextension='.kpm', filetypes=[("Karaoke parameter", "*.kpm")])
                    if len(kpm_output_selection) != 0:
                        config.set("PATHS", "KPM_Output", str(
                            kpm_output_selection))
                        kpm_data = save_kpm(
                            kpm_output_selection, cutscene_box, kpm_data)
                # music buttons
                elif event.ui_element == play_button:
                    if loaded:
                        if pygame.mixer.music.get_busy():  # if song is playing
                            play_button.set_text('▶')
                            pygame.mixer.music.stop()
                        else:
                            if len(music_box.get_text()) > 0:
                                audio_start_pos = int(music_box.get_text())
                            else:
                                audio_start_pos = 0

                            # TODO - get a nicer pause button, might not be possible before pygame-gui 6
                            play_button.set_text('▌▌')
                            try:
                                pygame.mixer.music.play(
                                    start=(audio_start_pos / 1000))
                            except(pygame.error):  # Position not implemented for music type
                                print(
                                    _('Unable to play the song from the given position, restarting from the beginning.'))
                                audio_start_pos = 0
                                pygame.mixer.music.play()
                if event.ui_element == undo_button:
                    undo_note = UIConfirmationDialog(
                        rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=_('Are you sure you want to undo changes made to this note?'), window_title=_('Undo changes'), action_short_name=_('OK'), object_id='#undo_note')
                    undo_note.cancel_button.set_text(_('Cancel'))
                # menu bar item related code
                # importing maps
                elif event.ui_object_id == 'menu_bar.#file_menu_items.#import':
                    import_selection = filedialog.askopenfilename(title='Select a rhythm minigame file', filetypes=[(
                        "Persona 4 Dancing map", "*.bin"), (
                        "Kenzan waterfall training", "*.bin"), (
                        "OE Karaoke", "*.bin"), ("Yakuza Rhythm Format", "*.lbd")], initialdir=config['PATHS']['Import_Input'])
                    if len(import_selection) != 0:
                        config.set("PATHS", "Import_Input", str(
                            import_selection))
                        karaoke.import_file(
                            import_selection)
                        currently_selected.clear()  # empty the list
                        currently_edited = None
                        stop_editing(boxes, box_labels,
                                     dropdowns, undo_button)
                # open file
                elif event.ui_object_id == 'menu_bar.#file_menu_items.#open':
                    input_selection = filedialog.askopenfilename(title='Select karaoke button data', filetypes=[
                                                                 ("Dragon Engine karaoke data", "*.kbd")], initialdir=config['PATHS']['Input'])
                    if len(input_selection) != 0:
                        if currently_edited:
                            stop_editing(boxes, box_labels,
                                         dropdowns, undo_button)
                            currently_edited = None
                        can_save, kpm_data = karaoke.load_kbd(
                            input_selection, cutscene_box)
                        currently_selected.clear()  # empty the list
                        if can_save:
                            config.set("PATHS", "Input", str(
                                input_selection))
                        currently_edited = None
                        open_file = input_selection

                # create a new file
                elif event.ui_object_id == 'menu_bar.#file_menu_items.#new':
                    reset_all = UIConfirmationDialog(
                        rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=_('Are you sure you want to create a new file? Any unsaved changes will be lost.'), window_title=_('Create a new file'), action_short_name=_('OK'), object_id='#reset')
                    reset_all.cancel_button.set_text(_('Cancel'))
                # save
                elif event.ui_object_id == 'menu_bar.#file_menu_items.#save':
                    output_selection = save_file(
                        open_file, manager, karaoke, cutscene_box)
                    open_file = output_selection
                # load song
                elif event.ui_object_id == 'menu_bar.#music_menu_items.#load_song':
                    music_selection = filedialog.askopenfilename(title='Select a music file', filetypes=[(
                        "MP3", "*.mp3"), ("OGG", "*.ogg"), ("FLAC", "*.flac")], initialdir=config['PATHS']['Music'])
                    if len(music_selection) != 0:
                        loaded, length = load_song(
                            music_selection, music_elements)
                        if loaded:
                            config.set("PATHS", "Music", str(
                                music_selection))

                # save as
                elif event.ui_object_id == 'menu_bar.#file_menu_items.#save_as':
                    output_selection = save_file(
                        None, manager, karaoke, cutscene_box)
                    open_file = output_selection
                # how to use page
                elif event.ui_object_id == 'menu_bar.#help_menu_items.#how_to_use':
                    info_window_rect = pygame.Rect(0, 0, 500, 400)
                    info_window_rect.center = screen.get_rect().center
                    # separated text so it would be easier for translators
                    how_1 = _('How to use')
                    how_2 = _(
                        'KUMA - A karaoke editor for Dragon Engine games.')
                    how_3 = _(
                        'To begin using the tool, you can add start by loading an existing file from <b>File</b> -> <b>Open</b> or just by adding notes to a new file.')
                    how_4 = _(
                        'You can choose your preferred <b>controller type</b> and <b>language</b> using the dropdown menus at the top of the screen.')
                    how_5 = _('When placing a note, the accuracy is <b>{ms} milliseconds</b>. You can change the position more accurately in <b>note edit mode.').format(
                        ms=karaoke.scale)
                    how_6 = _(
                        'You can play songs by loading them from the <b>Music</b> tab and then pressing the <b>Play</b> button in the left corner.')
                    how_7 = _(
                        'If you want to save, you can save by going to <b>File</b> -> <b>Save</b> or <b>Save as...</b> to either create a new file or overwrite an existing one.')
                    how_8 = _('Key binds')
                    how_9 = _(
                        '<b>Left click</b> - Place and pick up notes.')
                    how_10 = _(
                        '<b>Right click</b> - Change held note type.')
                    how_11 = _(
                        '<b>E</b> - Note edit mode. You can accurately change note timings, position, type and more. Pressing E again saves the note.')
                    how_12 = _(
                        '<b>Arrow keys, Page Up, Page Down</b> - Move the scrollbar.')
                    how_13 = _(
                        '<b>Delete</b> - Removes currently selected/edited note.')
                    how_14 = _('<b>End</b> - Jump to the last note.')
                    how_15 = _('<b>Left Ctrl + S</b> - Save.')
                    how_16 = _('<b>Left Ctrl + Z</b> - Undo.')
                    how_17 = _('<b>Left Ctrl + F</b> - Select a note.')
                    how_18 = _(
                        '<b>Left Ctrl + C</b> - Copy selected notes.')
                    how_19 = _(
                        '<b>Left Ctrl + V</b> - Paste copied notes (Vertical position does not change).')
                    how_20 = _(
                        '<b>Left Ctrl + Left Shift + V</b> - Paste copied notes (Vertical position changes).')

                    help_window = UIMessageWindow(rect=info_window_rect,
                                                  html_message=(
                                                      f'<b>{how_1}</b><br>---------------<br><b>{how_2}</b><br>{how_3}.<br>{how_4}<br>{how_5}</b><br>{how_6}<br>{how_7}<br>---------------<br><br><b>{how_8}</b><br>---------------<br><br>{how_9}<br>{how_10}<br>{how_11}<br>{how_12}<br>{how_13}<br>{how_14}<br>{how_15}<br>{how_16}<br>{how_17}<br>{how_18}<br>{how_19}<br>{how_20}'),
                                                  manager=manager,
                                                  window_title=_('Help'))
                    help_window.dismiss_button.set_text(_('Close'))
                # about page
                elif event.ui_object_id == 'menu_bar.#help_menu_items.#about':
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
                                                                  '<b>Translators: </b>{translators}<br>').format(ver=VERSION, mink='Mink', creators=CREATORS, testers=TESTERS, translators=TRANSLATORS),
                                                   manager=manager,
                                                   window_title=_('About'))
                    about_window.dismiss_button.set_text(_('Close'))
            # more stuff to do after pressing confirm button
            elif event.type == UI_CONFIRMATION_DIALOG_CONFIRMED:
                # reset file
                if event.ui_object_id == '#reset':
                    karaoke.reset(undo_kbd)
                    currently_selected.clear()  # empty the list
                    if currently_edited:
                        currently_edited = None
                        stop_editing(boxes, box_labels,
                                     dropdowns, undo_button)
                # undo note changes
                elif event.ui_object_id == '#undo_note':
                    update_text_boxes(currently_edited,
                                      boxes, dropdowns)
                # delete a single note
                elif event.ui_object_id == '#delete_one':
                    if currently_edited.note_type != 0:
                        karaoke.Remove_long(
                            currently_edited.x, currently_edited.y)
                    karaoke.Remove(currently_edited.x, currently_edited.y)
                    stop_editing(boxes, box_labels, dropdowns, undo_button)
                    currently_edited = None
                # delete multiple notes
                elif event.ui_object_id == '#delete_multi':
                    for note in currently_selected:
                        if note.note_type != 0:
                            karaoke.Remove_long(
                                note.x, note.y)
                        karaoke.Remove(note.x, note.y)
                    currently_selected.clear()  # empty the list
                # save file
                elif event.ui_object_id in ['#select_output', '#save_overwrite']:
                    if open_file != None:
                        karaoke.write_kbd(
                            open_file, cutscene_box)
                    else:
                        raise Exception(_('No open file, unable to save!'))
                elif event.ui_object_id == '#drag_file':
                    open_file = drag_file
                    if currently_edited:
                        stop_editing(boxes, box_labels,
                                     dropdowns, undo_button)
                        currently_edited = None
                    can_save, kpm_data = karaoke.load_kbd(
                        open_file, cutscene_box)
                    currently_selected.clear()  # empty the list
                    if can_save:
                        config.set("PATHS", "Input", str(
                            open_file))
                    currently_edited = None
            # dropdown menu stuff
            elif event.type == UI_DROP_DOWN_MENU_CHANGED:
                # buttons changed
                if event.ui_object_id == '#button_picker':
                    config.set("CONFIG", "BUTTONS", str(
                        button_picker.selected_option))
                    karaoke.load_item_tex(
                        button_picker.selected_option, held_note, note_picker)
                # language changed
                elif event.ui_object_id == '#language_picker':
                    config.set("CONFIG", "LANGUAGE", str(
                        language_picker.selected_option))
                    switch_language(language_picker.selected_option, params=[undo_button, load_kpm_button, save_kpm_button, cutscene_label, start_label,
                                                                             vert_label, start_cue_label, end_cue_label, start_cuesheet_label, end_cuesheet_label, note_button_label, note_type_label, note_type_picker, end_label, menu_bar, song_label, volume_label])
            # adjust song position
            elif event.type == UI_TEXT_ENTRY_CHANGED and event.ui_object_id == "#song_position":
                if not pygame.mixer.get_busy():
                    new_value = music_box.get_text()
                    if len(new_value) > 0:
                        new_pos = karaoke.song_pos_to_scroll(
                            int(music_box.get_text()), worlds[0].get_width())
                        scrollbar.set_current_value(new_pos)
            # adjust volume
            elif event.type == UI_HORIZONTAL_SLIDER_MOVED:
                if event.ui_object_id == '#volume_slider':
                    volume_value = volume_slider.get_current_value() / 100
                    pygame.mixer.music.set_volume(volume_value)
                    config.set("CONFIG", "VOLUME", str(volume_value))
                    volume_label.set_text(_('Volume {}').format(
                        volume_slider.get_current_value()))
                elif event.ui_object_id == '#scrollbar':
                    scrollbar_moved = True

            # drag and drop support
            elif event.type == pygame.DROPFILE:
                drag_file = event.file
                input_selection = UIConfirmationDialog(
                    rect=pygame.Rect(0, 0, 300, 300), manager=manager, action_long_desc=_('Are you sure you want to load this file?'), window_title=_('Open file'), action_short_name=_('OK'), object_id='#drag_file')
                input_selection.cancel_button.set_text(_('Cancel'))
            # process UI events
            manager.process_events(event)

        trunc_world_orig = (
            scrollbar_value - worlds[0].get_width() * surface_nr, 0)
        trunc_world = (scr_size[0], scr_size[1] - thick_h + 5)
        if surface_nr != next_surface and world_count > next_surface:
            world1_end = worlds[0].get_width() - trunc_world_orig[0]
            if world1_end > 0:
                screen.blit(worlds[surface_nr], (0, 0),
                            (trunc_world_orig, (world1_end, trunc_world[1])))
                screen.blit(worlds[next_surface], (world1_end, 0), ((
                    0, 0), (trunc_world[0] - world1_end, trunc_world[1])))
        else:
            screen.blit(worlds[surface_nr], (0, 0),
                        (trunc_world_orig, trunc_world))

        if pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos() + audio_start_pos
            music_box.set_text(str(current_time))
            # makes the scrollbar move when song is playing
            converted_time = karaoke.song_pos_to_scroll(
                current_time, worlds[0].get_width())
            scrollbar.set_current_value(converted_time)
        elif play_button.text != "▶":  # when song ends, change button to play button
            play_button.set_text('▶')
        pygame.draw.line(screen, (222, 175, 74), (karaoke.x, karaoke.y + 10), (karaoke.x, ((
            karaoke.box_size + karaoke.border) * karaoke.rows) + 70), width=5)  # helpful line for music
        if scrollbar_moved:
            if loaded and not pygame.mixer.music.get_busy():
                # change the time when scrolling
                converted_scroll = karaoke.scroll_to_song_pos(
                    scrollbar.get_current_value(), worlds[0].get_width())
                if converted_scroll > length:
                    converted_scroll = length

                music_box.set_text(str(converted_scroll))
            scrollbar_moved = False

        if fps_counter:
            fps_label.set_text(update_fps())
        manager.draw_ui(screen)
        manager.update(time_delta)
        pygame.display.update()


if __name__ == '__main__':
    main()
