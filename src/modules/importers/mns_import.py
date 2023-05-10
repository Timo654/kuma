import modules.parsers.other.mns_reader as mns
from modules.common import Note, Button, get_vert_pos, sort_notes
# big thanks to TGE for helping with this

def convert_button(button):
    if button == 0:  # down
        return Button.Cross
    elif button == 1:  # cross
        return Button.Cross
    elif button == 2:  # left
        return Button.Square
    elif button == 3:  # circle
        return Button.Circle
    elif button == 4:  # up
        return Button.Triangle
    elif button == 5:  # triangle
        return Button.Triangle
    elif button == 8:  # scratch
        return Button.Cross
    else:
        return Button.Unimplemented

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
    bps = 60 / bpm
    half = 0x8000
    notes_list = list()
    for i in range(len(data['Notes'])):
        oldnote = data['Notes'][i]
        newnote = dict()
        beat_decimal = oldnote['Beat']
        if (oldnote['Beat'] & half):
            beat_decimal = (oldnote['Beat'] & ~half) + 0.5
        total_ms = ((oldnote['Measure'] * 4) +
                    beat_decimal) * bps * 1000

        newnote['Start position'] = int(total_ms * 3)
        if oldnote['Hold duration']:
            hold_length = (((oldnote['Hold duration'] / 8 ) ) * bps) * 1000
            newnote['End position'] = int((total_ms + (hold_length)) * 3)
            newnote['Note type'] = Note.Hold
        else:
            newnote['End position'] = 0
            newnote['Note type'] = Note.Regular
        newnote['Button type'] = convert_button(oldnote['Button type'])
        newnote['Vertical position'] = get_vert_pos(newnote['Button type'])
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


def load_mns(file):
    data = mns.read_file(file)
    return convert_to_kbd(data)
