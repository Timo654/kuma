import modules.parsers.oe.wtfl_reader as wtfl


def get_vert_pos(note):
    if note == 0:
        return 4
    elif note == 1:
        return 6
    elif note == 2:
        return 2
    elif note == 3:
        return 0


def convert_button(button):
    if button == 0:
        return 1
    elif button == 1:
        return 0
    else:
        return button


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
            newnote['Cue ID'] = 0
            newnote['Cuesheet ID'] = 0
            if newnote['Button type'] < 4:
                notes_list.append(newnote)

    kbd['Notes'] = notes_list
    # update header after note list was modified
    kbd['Header']['Note count'] = len(kbd['Notes'])

    return kbd


def load_wtfl(file):
    data = wtfl.read_file(file)
    return convert_to_kbd(data)
