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
    """Converts button to Yakuza ID.\n
    Returns button ID and button type."""
    button = int(button)
    if button == 0:  # triangle
        return 3, 0
    elif button == 1:  # circle
        return 0, 0
    elif button == 2:  # cross
        return 1, 0
    elif button == 3:  # square
        return 2, 0
    elif button == 4:  # triangle hold
        return 3, 1  # unimplemented
    elif button == 5:  # circle hold
        return 0, 1  # unimplemented
    elif button == 6:  # cross hold
        return 1, 1  # unimplemented
    elif button == 7:  # square hold
        return 2, 1  # unimplemented
    elif button == 12:  # left facing slide
        return 7, 0  # unimplemented
    elif button == 13:  # right facing slide
        return 7, 0  # unimplemented
    else:
        raise ValueError('Unknown button type', button)

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
            if newnote['Button type'] < 4:
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
