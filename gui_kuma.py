# based on https://github.com/TheBigKahuna353/Inventory_system and https://github.com/ppizarror/pygame-menu/blob/master/pygame_menu/examples/other/scrollbar.py
import pygame
import pygame_menu
import pygame_gui
from pygame_gui.windows.ui_file_dialog import UIFileDialog, UIConfirmationDialog
from pygame_gui.elements.ui_button import UIButton
from pygame.rect import Rect
from pygame_menu.widgets import ScrollBar
import kbd_reader as kbd

# initialize pygame stuff
pygame.init()
font = pygame.font.SysFont("Comic-Sans", 18)
clock = pygame.time.Clock()
pygame.display.set_caption('KUMA')

# these are the notes, colors are placeholder
items = [pygame.Surface((50, 50), pygame.SRCALPHA) for _ in range(6)]
pygame.draw.circle(items[0], (245, 97, 32), (25, 25), 25)  # circle
pygame.draw.circle(items[1], (54, 162, 248), (25, 25), 25)  # cross
pygame.draw.circle(items[2], (247, 184, 241), (25, 25), 25)  # square
pygame.draw.circle(items[3], (141, 213, 184), (25, 25), 25)  # triangle
pygame.draw.line(items[4], (0, 109, 198), (0, 25), (50, 25), 25)  # hold
pygame.draw.line(items[5], (198, 0, 99), (0, 25), (50, 25), 25)  # rapid

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
        self.col = 1040
        self.items = [[None for _ in range(self.rows)]
                      for _ in range(self.col)]
        self.box_size = 20
        self.x = 50
        self.y = 50
        self.border = 3

    # draw everything
    def draw(self, world, scroll):
        # draw background
        col_start = scroll // (self.box_size + self.border) - 2
        col_end = col_start + 70
        if col_end > self.col:
            col_end = self.col

        pygame.draw.rect(world, (100, 100, 100),
                         (self.x, self.y, (self.box_size + self.border)*self.col + self.border, (self.box_size + self.border)*self.rows + self.border))
        for x in range(col_start, col_end): #drawing only the columns we can see, for performance reasons
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

# changes scale to 200ms per square


def pos_convert(pos):
    return int(((pos / 3000) * 5))

# converts pos back to yakuza time


def pos_to_game(pos):
    return int((pos / 5) * 3000)


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
                note = dict()
                note['Start position'] = pos_to_game(x)
                note['End position'] = 0
                note['Vertical position'] = y
                note['Button type'] = karaoke.items[x][y][0].id
                note['Note type'] = karaoke.items[x][y][0].note_type
                note['Cue ID'] = 0  # TODO - audio support
                note['Cuesheet ID'] = 0  # TODO - audio support
                # add end position for holds/rapids
                if karaoke.items[x][y][0].note_type != 'Regular':
                    x += 1
                    while karaoke.items[x][y][0].id > 3:
                        x += 1
                    note['End position'] = pos_to_game(x)
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

    scr_size = (1600, 480)
    width_multiplier = 15
    screen = pygame.display.set_mode((scr_size))
    world = pygame.Surface(
        (int(scr_size[0] * width_multiplier), int(scr_size[1])), pygame.SRCALPHA, 32)

    manager = pygame_gui.UIManager(scr_size)
    file_selection_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 250), (100, 50)),
                                                         text='Open file',
                                                         manager=manager)
    output_selection_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((110, 250), (100, 50)),
                                                           text='Save file',
                                                           manager=manager)
    reset_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((210, 250), (100, 50)),
                                                text='Reset',
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

    karaoke = Karaoke()

    # what the player is holding
    selected = None
    gui_button_mode = None
    note_id = 0  # note that you get when you want to add one, first is circle

    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------
    while True:
        # Clock tick
        time_delta = clock.tick(60)/1000.0
        scrollbar_value = sb_h.get_value()
        # draw the screen
        world.fill((169, 149, 154))  # clean the screen
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
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == file_selection_button:
                        gui_button_mode = 'Input'
                        input_selection = UIFileDialog(
                            rect=Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True)
                    if gui_button_mode == 'Input':
                        if event.ui_element == input_selection.ok_button:
                            gui_button_mode = None
                            karaoke = load_kbd(
                                input_selection.current_file_path, karaoke)

                    if event.ui_element == output_selection_button:
                        gui_button_mode = 'Output'
                        output_selection = UIFileDialog(
                            rect=Rect(0, 0, 300, 300), manager=manager, allow_picking_directories=True)
                    if gui_button_mode == 'Output':
                        if event.ui_element == output_selection.ok_button:
                            gui_button_mode = None
                            write_kbd(
                                output_selection.current_file_path, karaoke)

                    if event.ui_element == reset_button:
                        gui_button_mode = 'Reset'
                        reset_all = UIConfirmationDialog(
                            rect=Rect(0, 0, 300, 300), manager=manager, action_long_desc='Are you sure you want to reset? Any unsaved changes will be lost.')
                if event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:  # reset event
                    if gui_button_mode == 'Reset':
                        gui_button_mode = None
                        karaoke = Karaoke()

            manager.process_events(event)

        manager.update(time_delta)
        trunc_world_orig = (scrollbar_value, 0)
        trunc_world = (scr_size[0], scr_size[1] - thick_h)
        screen.blit(world, (0, 0), (trunc_world_orig, trunc_world))
        screen.blit(update_fps(), (10, 0))
        manager.draw_ui(screen)
        pygame.display.update()


if __name__ == '__main__':
    main()
