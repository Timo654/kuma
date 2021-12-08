from binary_reader import BinaryReader


def read_note_type(note_type):
    """Gets the note type ID and returns it as string."""
    if note_type == 0:
        return 'Regular'
    elif note_type == 1:
        return 'Hold'
    elif note_type == 2:
        return 'Rapid'
    else:
        raise Exception(f'Invalid note type ID {note_type}')


def write_note_type(note_type):
    """Gets the note type string and returns it as ID."""
    if note_type == 'Regular':
        return 0
    elif note_type == 'Hold':
        return 1
    elif note_type == 'Rapid':
        return 2
    else:
        raise Exception(f'Invalid note type {note_type}')

def write_file(data, filename, cutscene_start=0):
    """Writes the kbd from dict to the specified filename.\n
    The first parameter is a dict containin info read from kbd,\n
    the second parameter is the filename and third is the cutscene start time (by default 0) from KPM"""

    # writing the notes
    max_score = 0  # counting the maximum possible score
    max_cutscene_score = 0  
    # this is where we will write the note data
    kbd_n = BinaryReader(bytearray())
    for i in range(len(data['Notes'])):
        note = data['Notes'][i]
        kbd_n.write_uint32(note['Start position'])
        kbd_n.write_uint32(note['End position'])
        kbd_n.write_uint32(note['Vertical position'])
        kbd_n.write_uint32(0)  # Padding
        kbd_n.write_uint32(note['Button type'])
        kbd_n.write_uint32(write_note_type(note['Note type']))
        kbd_n.write_uint16(note['Cue ID'])
        kbd_n.write_uint16(note['Cuesheet ID'])
        kbd_n.write_uint32(0)  # Padding

        # counting score
        if note['Note type'] == 'Regular':
            max_score += 10
        else:
            max_score += 30
        if i > 19:
            max_score += 5  # combo bonus per note
        if cutscene_start > note['Start position']:
            max_cutscene_score = max_score

    # writing the header
    kbd_h = BinaryReader(bytearray())  # this is where we will write the header
    kbd_h.write_str('NTBK')  # magic will always be NTBK
    kbd_h.write_uint32(0)  # padding
    kbd_h.write_uint32(data['Header']['Version'])
    kbd_h.write_uint32(kbd_n.size())  # size of the notes portion of the file
    kbd_h.write_uint32(len(data['Notes']))  # amount of notes
    kbd_h.write_uint32(max_score)
    if data['Header']['Version'] > 1:
        kbd_h.write_uint32(max_cutscene_score)

    kbd_h.extend(kbd_n.buffer())  # merge header and notes
    # saving the file
    with open(filename, 'wb') as f:
        f.write(kbd_h.buffer())


def read_file(input_file):
    """Reads the kbd file and returns a dict.\n
    The first and only parameter is the filename"""
    # opening the file
    with open(input_file, 'rb') as file:
        kbd = BinaryReader(file.read())  # reading file as little endian
    # making a dict for the data
    data = dict()
    data['Header'] = dict()
    # reading the file header
    data['Header']['Magic'] = kbd.read_str(4)  # read 4 characters
    if data['Header']['Magic'] != 'NTBK':  # in case it's not a valid file
        raise ValueError('Not a valid KBD file')
    kbd.seek(4, 1)  # unused, filler, skipping this
    data['Header']['Version'] = kbd.read_uint32()
    kbd.seek(4, 1)  # file size without header, we're skipping this
    data['Header']['Note count'] = kbd.read_uint32()
    data['Header']['Max score'] = kbd.read_uint32()
    if data['Header']['Version'] > 1:  # not present in first version of the format
        data['Header']['Max score pre-cutscene'] = kbd.read_uint32()

    # reading the notes
    note_list = list()
    for i in range(data['Header']['Note count']):
        note = dict()
        note['Index'] = i
        # Time is in the 'Yakuza' format, 1 unit is 1/3 ms. Conversion could be handled by the GUI.
        note['Start position'] = kbd.read_uint32()
        note['End position'] = kbd.read_uint32()
        note['Vertical position'] = kbd.read_uint32()
        kbd.seek(4, 1)  # unused, so we're skipping it
        note['Button type'] = kbd.read_uint32()
        note['Note type'] = read_note_type(kbd.read_uint32())
        note['Cue ID'] = kbd.read_uint16()  # Audio cheer ID
        note['Cuesheet ID'] = kbd.read_uint16()  # Audio cheer container ID
        kbd.seek(4, 1)  # unused, so we're skipping it
        note_list.append(note)

    data['Notes'] = note_list

    return data
