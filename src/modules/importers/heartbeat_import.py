from modules.common import Note, Button, get_vert_pos


def byPos(note):
    return note["Start position"]


def sort_notes(note_list):
    note_list.sort(key=byPos)
    i = 0
    prev_start_pos = 0
    prev_end_pos = 0
    while i < len(note_list):
        note = note_list[i]
        if prev_end_pos != 0:
            if prev_start_pos <= note['Start position'] <= prev_end_pos:
                note_list.pop(i)
            else:
                prev_start_pos = note['Start position']
                prev_end_pos = note['End position']
                i += 1
        else:
            if note['Start position'] == prev_start_pos:
                note_list.pop(i)
            else:
                prev_start_pos = note['Start position']
                prev_end_pos = note['End position']
                i += 1


def convert_button(button):
    """Converts button to Yakuza ID.\n
    Returns button ID and button type."""
    if button == "UP":  # triangle
        return Button.Triangle
    elif button == "RIGHT":  # circle
        return Button.Circle
    elif button == "DOWN":  # cross
        return Button.Cross
    elif button == "LEFT":  # square
        return Button.Square
    else:
        # Unimplemented button type
        return Button.Unimplemented


def read_notes(data):
    notes = list()
    for item in data["layers"]:
        button_type = convert_button(item["name"])
        for element in item["timing_points"]:
            note = dict()
            note["Start position"] = element["time"] * 3
            note['Button type'] = button_type
            notes.append(note)
    return notes


def convert_to_kbd(data):
    notes = read_notes(data)
    kbd = dict()
    # HEADER
    kbd['Header'] = dict()
    kbd['Header']['Magic'] = "NTBK"
    kbd['Header']['Version'] = 2
    kbd['Header']['Note count'] = 0
    kbd['Header']['Max score'] = 0
    kbd['Header']['Max score pre-cutscene'] = 0
    notes_list = list()
    for note in notes:
        newnote = dict()
        newnote['Start position'] = note["Start position"]
        newnote['End position'] = 0  # NOTE: No hold support for now
        newnote['Button type'] = note['Button type']
        newnote['Vertical position'] = get_vert_pos(newnote['Button type'])
        newnote['Note type'] = 0  # NOTE: No hold support for now
        newnote['Start Cue ID'] = 0
        newnote['Start Cuesheet ID'] = 0
        newnote['End Cue ID'] = 0
        newnote['End Cuesheet ID'] = 0
        if newnote['Button type'] != Button.Unimplemented:
            notes_list.append(newnote)
    sort_notes(notes_list)
    kbd['Notes'] = notes_list
    # update header after note list was modified
    kbd['Header']['Note count'] = len(kbd['Notes'])
    return kbd


def load_hb(data):
    return convert_to_kbd(data)
