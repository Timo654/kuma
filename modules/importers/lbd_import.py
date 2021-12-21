import modules.parsers.oe.lbd_reader as lbd


def get_note_type(end_pos):
    if end_pos == 0:
        return 0
    else:
        return 1


def get_vert_pos(note):
    if note == 0:
        return 4
    elif note == 1:
        return 6
    elif note == 2:
        return 2
    elif note == 3:
        return 0


def convert_button(button, version):
    if version > 3:  # Y5, convert arrows to normal buttons
        if button == 9:
            return 3
        elif button == 10:
            return 1
        elif button == 11:
            return 0
        elif button == 12:
            return 2
        else:
            return button
    else:  # Ishin and Y0
        if button == 2:
            return 3
        elif button == 3:
            return 2
        elif button == 4:
            return 0
        elif button == 5:
            return 1
        elif button == 6:
            return 3
        elif button == 7:
            return 2
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
        if oldnote['Start position'] >= 0:
            newnote = dict()
            newnote['Start position'] = oldnote['Start position']
            newnote['End position'] = oldnote['End position']
            newnote['Button type'] = convert_button(
                oldnote['Button type'], data['Header']['Version'])
            newnote['Vertical position'] = get_vert_pos(newnote['Button type'])
            newnote['Note type'] = get_note_type(oldnote['End position'])
            newnote['Cue ID'] = 0
            newnote['Cuesheet ID'] = 0
            if newnote['Button type'] < 4:
                notes_list.append(newnote)

    kbd['Notes'] = notes_list
    # update header after note list was modified
    kbd['Header']['Note count'] = len(kbd['Notes'])

    return kbd


def load_lbd(file):
    data = lbd.read_file(file)
    return convert_to_kbd(data)
