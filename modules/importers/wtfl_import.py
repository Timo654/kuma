import modules.parsers.oe.wtfl_reader as wtfl
from modules.common import Button, get_vert_pos

def convert_button(button):
    if button == 0:
        return Button.Cross
    elif button == 1:
        return Button.Circle
    elif button > 4:
        return Button.Unimplemented
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
        if oldnote['Position'] >= 0:
            newnote = dict()
            newnote['Start position'] = oldnote['Position'] * 3000
            newnote['End position'] = 0
            newnote['Button type'] = convert_button(oldnote['Button type'])
            newnote['Vertical position'] = get_vert_pos(newnote['Button type'])
            newnote['Note type'] = 0  # no other types exist in Kenzan
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


def load_wtfl(file):
    data = wtfl.read_file(file)
    return convert_to_kbd(data)
