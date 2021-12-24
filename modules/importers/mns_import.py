import modules.parsers.other.mns_reader as mns
# big thanks to TGE for helping with this


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
    if button == 0:  # down
        return 1
    elif button == 1:  # cross
        return 1
    elif button == 2:  # left
        return 2
    elif button == 3:  # circle
        return 0
    elif button == 4:  # up
        return 3
    elif button == 5:  # triangle
        return 3
    elif button == 8:  # scratch
        return 1


def convert_to_kbd(data):
    kbd = dict()

    # HEADER
    kbd['Header'] = dict()
    kbd['Header']['Magic'] = "NTBK"
    kbd['Header']['Version'] = 2
    kbd['Header']['Note count'] = len(data['Notes'])
    kbd['Header']['Max score'] = 0
    kbd['Header']['Max score pre-cutscene'] = 0
    bpm = data['Header']['BPM']
    bps = bpm / 60
    half = 0x8000
    notes_list = list()
    for i in range(len(data['Notes'])):
        oldnote = data['Notes'][i]
        newnote = dict()
        beat_decimal = oldnote['Beat']
        if (oldnote['Beat'] & half):
            beat_decimal = (oldnote['Beat'] & ~half) + 0.5
        total_ms = ((oldnote['Measure'] * 4) +
                    beat_decimal) * (60.0 / bpm) * 1000

        newnote['Start position'] = int(total_ms * 3)
        if oldnote['Hold duration']:
            hold_length = (oldnote['Hold duration'] / 4) / bps
            newnote['End position'] = int((total_ms + (hold_length * 500)) * 3)
            newnote['Note type'] = 1
        else:
            newnote['End position'] = 0
            newnote['Note type'] = 0
        newnote['Button type'] = convert_button(oldnote['Button type'])
        newnote['Vertical position'] = get_vert_pos(newnote['Button type'])
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


def load_mns(file):
    data = mns.read_file(file)
    return convert_to_kbd(data)
