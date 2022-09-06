from binary_reader import BinaryReader

def get_dbd_vert(note_id):
    if note_id == 0:
        return 4
    elif note_id == 1:
        return 6
    elif note_id == 2:
        return 2
    elif note_id == 3:
        return 0

def write_file(data, filename, cutscene_start=0):
    """Writes the kbd from dict to the specified filename.\n
    The first parameter is a dict containing info read from kbd,\n
    the second parameter is the filename and third is the cutscene start time (by default 0) from KPM"""
    if data['Header']['Magic'] == "NTBD":
        karaoke = False
    elif data['Header']['Magic'] == "NTBK":
        karaoke = True
    # writing the notes
    max_score = 0  # counting the maximum possible score
    max_cutscene_score = 0
    # this is where we will write the note data
    kbd_n = BinaryReader(bytearray())
    for i in range(len(data['Notes'])):
        note = data['Notes'][i]
        kbd_n.write_uint32(note['Start position'])
        kbd_n.write_uint32(note['End position'])
        if karaoke:
            kbd_n.write_uint32(note['Vertical position'])
        kbd_n.write_uint32(note['Display offset'])
        kbd_n.write_uint32(note['Button type'])
        kbd_n.write_uint32(note['Note type'])  # 0 regular, 1 hold, 2 rapid
        if karaoke:
            kbd_n.write_uint16(note['Start Cue ID'])
            kbd_n.write_uint16(note['Start Cuesheet ID'])
            kbd_n.write_uint16(note['End Cue ID'])
            kbd_n.write_uint16(note['End Cuesheet ID'])
        else:
            kbd_n.write_uint16(note['Unk2'])

        if karaoke:
            # counting score
            if note['Note type'] == 0:
                max_score += 10
            else:
                max_score += 30
            if i > 19:
                max_score += 5  # combo bonus per note
            if (cutscene_start * 1000) * 3 > note['Start position']:
                max_cutscene_score = max_score

    # writing the header
    kbd_h = BinaryReader(bytearray())  # this is where we will write the header
    kbd_h.write_str(data['Header']['Magic'])  # magic will always be NTBK
    kbd_h.write_uint32(0)  # padding
    kbd_h.write_uint32(data['Header']['Version'])
    kbd_h.write_uint32(kbd_n.size())  # size of the notes portion of the file
    kbd_h.write_uint32(len(data['Notes']))  # amount of notes
    if karaoke:
        kbd_h.write_uint32(max_score)
        if data['Header']['Version'] > 1:
            kbd_h.write_uint32(max_cutscene_score)
    else:
        kbd_h.write_uint32(data['Header']['Unk1'])

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
    if data['Header']['Magic'] == "NTBD":
        karaoke = False
    elif data['Header']['Magic'] == "NTBK":
        karaoke = True
    else:  # in case it's not a valid file
        raise ValueError('Not a valid KBD/DBD file')
    kbd.seek(4, 1)  # unused, filler, skipping this
    data['Header']['Version'] = kbd.read_uint32()
    kbd.seek(4, 1)  # file size without header, we're skipping this
    data['Header']['Note count'] = kbd.read_uint32()
    if karaoke:
        data['Header']['Max score'] = kbd.read_uint32()
        if data['Header']['Version'] > 1:  # not present in first version of the format
            data['Header']['Max score pre-cutscene'] = kbd.read_uint32()
    else:
        data['Header']['Unk1'] = kbd.read_uint32()

    # reading the notes
    note_list = list()
    for i in range(data['Header']['Note count']):
        note = dict()
        note['Index'] = i
        # Time is in the 'Yakuza' format, 1 unit is 1/3 ms. Conversion could be handled by the GUI.
        note['Start position'] = kbd.read_uint32()
        note['End position'] = kbd.read_uint32()
        if karaoke:
            note['Vertical position'] = kbd.read_uint32()
        # no clue if it even does anything
        note['Display offset'] = kbd.read_uint32()
        note['Button type'] = kbd.read_uint32()
        if not karaoke:
            note['Vertical position'] = get_dbd_vert(note['Button type'])
        note['Note type'] = kbd.read_uint32()  # 0 regular, 1 hold, 2 rapid
        if karaoke:
            note['Start Cue ID'] = kbd.read_uint16()  # Audio cheer ID
            # Audio cheer container ID
            note['Start Cuesheet ID'] = kbd.read_uint16()
            note['End Cue ID'] = kbd.read_uint16()  # Audio cheer ID
            # Audio cheer container ID
            note['End Cuesheet ID'] = kbd.read_uint16()
        else:
            note['Start Cue ID'] = 0
            note['Start Cuesheet ID'] = 0
            note['End Cue ID'] = 0
            note['End Cuesheet ID'] = 0
            note['Unk2'] = kbd.read_uint32()
        note_list.append(note)

    data['Notes'] = note_list

    return data
