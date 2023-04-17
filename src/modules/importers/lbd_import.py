import modules.parsers.oe.lbd_reader as lbd
from modules.common import Note, Button, get_vert_pos

def get_note_type(end_pos):
    if end_pos == 0:
        return Note.Regular
    else:
        return Note.Hold


def convert_button(button, version):
    if version > 3:  # Y5, convert arrows to normal buttons
        if button == 9:
            return Button.Triangle
        elif button == 10:
            return Button.Cross
        elif button == 11:
            return Button.Circle
        elif button == 12:
            return Button.Square
        else:
            return Button(button)
    else:  # Ishin and Y0
        if button == 2:
            return Button.Triangle
        elif button == 3:
            return Button.Square
        elif button == 4:
            return Button.Circle
        elif button == 5:
            return Button.Cross
        elif button == 6:
            return Button.Triangle
        elif button == 7:
            return Button.Square
        else:
            return Button(button)


def convert_to_kbd(data):
    kbd = dict()

    # HEADER
    kbd['Header'] = dict()
    kbd['Header']['Magic'] = "NTBK"
    kbd['Header']['Version'] = 2
    kbd['Header']['Note count'] = 0
    kbd['Header']['Max score'] = 0
    kbd['Header']['Max score pre-cutscene'] = 0

    notes_list = list()
    for i in range(len(data['Notes'])):
        oldnote = data['Notes'][i]
        if oldnote['Start position'] >= 0:
            newnote = dict()
            newnote['Start position'] = oldnote['Start position']
            newnote['End position'] = oldnote['End position']
            newnote['Button type'] = convert_button(
                oldnote['Button type'], data['Header']['Version'])
            newnote['Vertical position'] = get_vert_pos(newnote['Button type'])
            newnote['Note type'] = get_note_type(oldnote['End position'])
            newnote['Start Cue ID'] = 0
            newnote['Start Cuesheet ID'] = 0
            newnote['End Cue ID'] = 0
            newnote['End Cuesheet ID'] = 0
            if newnote['Button type'] != Button.Unimplemented:
                notes_list.append(newnote)

    kbd['Notes'] = notes_list
    # update header after note list was modified
    kbd['Header']['Note count'] = len(kbd['Notes'])

    return kbd


def load_lbd(file):
    data = lbd.read_file(file)
    return convert_to_kbd(data)
