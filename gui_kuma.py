# based on https://github.com/TheBigKahuna353/Inventory_system and https://github.com/ppizarror/pygame-menu/blob/master/pygame_menu/examples/other/scrollbar.py
import pygame
import pygame_menu


from pygame_menu.widgets import ScrollBar

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
        self.rows = 7
        self.col = 500
        self.items = [[None for _ in range(self.rows)]
                      for _ in range(self.col)]
        self.box_size = 20
        self.x = 50
        self.y = 50
        self.border = 3

    # draw everything
    def draw(self, world):
        # draw background
        pygame.draw.rect(world, (100, 100, 100),
                         (self.x, self.y, (self.box_size + self.border)*self.col + self.border, (self.box_size + self.border)*self.rows + self.border))
        for x in range(self.col):
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
        print(xy)
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


def main():
    pygame.display.set_caption('KUMA')
    pygame.mixer.init()  # TODO - playing music
    scr_size = (1600, 480)
    width_multiplier = 8
    screen = pygame.display.set_mode((scr_size))
    world = pygame.Surface(
        (int(scr_size[0] * width_multiplier), int(scr_size[1])), pygame.SRCALPHA, 32)
    screen.fill((120, 90, 130))
    thick_h = 20

    # Horizontal ScrollBar
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

    clock = pygame.time.Clock()
    karaoke = Karaoke()

    # PLACEHOLDER NOTES FOR TESTING PURPOSES
    karaoke.Add([Item(3, 'Regular')], (0, 0))
    karaoke.Add([Item(2, 'Regular')], (0, 2))
    karaoke.Add([Item(0, 'Regular')], (0, 4))
    karaoke.Add([Item(1, 'Regular')], (0, 6))
    karaoke.Add([Item(4, 'Regular')], (0, 1))
    karaoke.Add([Item(5, 'Regular')], (0, 3))
    karaoke.Add([Item(1, 'Regular')], (49, 6))
    # PLACEHOLDER NOTES FOR TESTING PURPOSES

    # what the player is holding
    selected = None
    note_id = -1  # note that you get when you want to add one, first is circle

    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------
    while True:

        # Clock tick
        clock.tick(60)
        # draw the screen
        world.fill((255, 255, 255))
        karaoke.draw(world)

        mousex, mousey = pygame.mouse.get_pos()
        mousex += sb_h.get_value()  # adjust for scrollbar

        # if holding something, draw it next to mouse
        if selected:
            world.blit(selected[0].resize(20), (mousex, mousey))
        pygame.display.update()
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
                if event.button == 3:
                    if note_id < 3:
                        note_id += 1
                    else:
                        note_id = 0
                    selected = [Item(note_id, 'Regular')]  # add item
                elif event.button == 1:
                    pos = karaoke.Get_pos(sb_h.get_value())
                    if karaoke.In_grid(pos[0], pos[1]):
                        if selected:
                            selected = karaoke.Add(selected, pos)
                        elif karaoke.items[pos[0]][pos[1]]:
                            selected = karaoke.items[pos[0]][pos[1]]
                            print(selected[0].id)
                            karaoke.items[pos[0]][pos[1]] = None
                # TODO - implement keybinds for making HOLD and RAPID notes
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DELETE:
                    selected = None  # deletes selected note
                if event.key == pygame.K_LCTRL:
                    note_id = 4
                    selected = [Item(note_id, 'Hold')]  # add item
                if event.key == pygame.K_LSHIFT:
                    note_id = 5
                    selected = [Item(note_id, 'Rapid')]  # add item

        trunc_world_orig = (sb_h.get_value(), 0)
        trunc_world = (scr_size[0], scr_size[1] - thick_h)

        # noinspection PyTypeChecker
        screen.blit(world, (0, 0), (trunc_world_orig, trunc_world))
        pygame.display.update()


if __name__ == '__main__':
    main()
