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
    button = int(button)
    if button == 0:  # triangle
        return Button.Triangle, Note.Regular
    elif button == 1:  # circle
        return Button.Circle, Note.Regular
    elif button == 2:  # cross
        return Button.Cross, Note.Regular
    elif button == 3:  # square
        return Button.Square, Note.Regular
    elif button == 4:  # triangle hold
        return Button.Triangle, Note.Hold
    elif button == 5:  # circle hold
        return Button.Circle, Note.Hold
    elif button == 6:  # cross hold
        return Button.Cross, Note.Hold
    elif button == 7:  # square hold
        return Button.Square, Note.Hold
    else:
        # Unimplemented button type
        return Button.Unimplemented, Note.Regular

# converts project diva time to yakuza time


def convert_time(pdtime):
    return int((int(pdtime) / 100) * 3)


def read_notes(data):
    current_time = 0
    offset = 0
    notes = list()
    for line in data:
        if line.startswith("TIME("):
            current_time = line
        elif line.startswith("TARGET_FLYING_TIME("):
            offset = int(line[19:-2]) * 100
        elif line.startswith('TARGET('):
            line = line[7:-2].split(", ")
            notes.append(
                (convert_time(int(current_time[5:-2]) + offset), line))
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
    for count, note in enumerate(notes):
        if note[0] != notes[count-1][0]:
            newnote = dict()
            button_type, is_hold = convert_button(note[1][0])
            newnote['Start position'] = note[0]
            if is_hold:
                if count + 1 != len(notes):
                    for i in range(count + 1, len(notes)):
                        if notes[i][0] != note[0]:
                            # 400 milliseconds, should be enough?
                            newnote['End position'] = notes[i][0] - 1200
                            # if hold would be too short
                            if newnote['End position'] - 900 < newnote['Start position']:
                                newnote['End position'] = 0
                                is_hold = False
                            break
                    else:
                        newnote['End position'] = note[0] + 6000
                else:
                    newnote['End position'] = note[0] + 6000
            else:
                newnote['End position'] = 0
            newnote['Button type'] = button_type
            newnote['Vertical position'] = get_vert_pos(newnote['Button type'])
            newnote['Note type'] = is_hold
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


def load_dsc(file):
    with open(file, 'r') as f:
        data = [x.strip() for x in f.readlines()]
    return convert_to_kbd(data)
