from binary_reader import BinaryReader


def write_file(data, filename):
    """Writes the KARA from dict to the specified filename.\n
    The first parameter is a dict containing info read from KARA and\n
    the second parameter is the filename."""
    kar = BinaryReader(bytearray(), True)
    # writing the header

    # HEADER
    kar.write_str('KARA')  # magic
    kar.write_uint16(0x201)  # endian identifier
    if data['Header']['Version'] > 3:
        kar.write_uint8(len(data['Lines']))
        kar.write_uint8(data['Header']['Unknown 1'])
    else:
        kar.write_uint16(0)
    kar.write_uint32(data['Header']['Unknown 2'])
    kar.write_uint32(0)
    if data['Header']['Version'] == 3:
        kar.write_uint8(len(data['Lines']))
        kar.write_uint8(data['Header']['Unknown 1'])
        kar.write_uint16(0)
        kar.write_uint64(0)
        kar.write_uint32(0)

    # MAIN TABLE
    kar.write_uint32(data['Main table']['Unknown 2'])
    kar.write_uint32(data['Main table']['Unknown 3'])
    kar.write_uint32(data['Main table']['Notes for cutscene'])
    kar.write_uint32(data['Main table']['Unknown 4'])
    kar.write_uint32(data['Main table']['Unknown 5'])
    kar.write_uint32(data['Main table']['Unknown 6'])
    kar.write_uint32(data['Main table']['Unknown 7'])
    kar.write_uint32(data['Main table']['Unknown 8'])
    kar.write_float(data['Main table']['Unknown 9'])
    kar.write_float(data['Main table']['Unknown 10'])
    kar.write_float(data['Main table']['Unknown 11'])
    kar.write_uint32(data['Main table']['Cheer difficulty'])
    kar.write_uint32(data['Main table']['Unknown 12'])
    kar.write_float(data['Main table']['Great range'])
    kar.write_float(data['Main table']['Good range'])
    kar.write_uint32(data['Main table']['Unknown 13'])

    # LINES
    old_pointers = list()

    for i in range(len(data['Lines'])):
        line = data['Lines'][i]
        kar.write_uint32(line['Vertical position'])
        note_pnt_pos = kar.pos()
        kar.write_uint32(0)  # note section pointer
        kar.write_uint32(len(line['Notes']))  # note count

        settings_pnt_pos = kar.pos()
        kar.write_uint32(0)  # settings pointer

        kar.write_uint32(line['Unknown 14'])
        texture_pnt_pos = kar.pos()
        kar.write_uint32(0)  # texture name pointer

        kar.write_uint32(line['Unknown 15'])
        kar.write_uint32(line['Line spawn'])
        kar.write_uint32(line['Line despawn'])
        if i < data['Header']['Line count'] - 1:  # last line doesnt have it
            kar.write_uint32(line['Line page'])
    old_pointers.append((note_pnt_pos, settings_pnt_pos, texture_pnt_pos))

    new_pointers = list()
    for i in range(len(data['Lines'])):
        # line settings
        settings = data['Lines'][i]['Settings']
        settings_pos = kar.pos()
        kar.write_uint32(settings['Line length'])  # 24 = 1.0
        kar.write_uint32(settings['Line start time (ms)'])
        kar.write_uint32(settings['Line end time (ms)'])
        # note settings
        note_pos = kar.pos()

        for o in range(len(data['Lines'][i]['Notes'])):
            note = data['Lines'][i]['Notes'][o]
            kar.write_uint32(note['Note type'])
            kar.write_float(note['Start position'])
            kar.write_float(note['End position'])
            kar.write_uint32(note['Button type'])
            kar.write_uint32(note['Unknown 17'])
            kar.write_uint16(note['Cuesheet ID'])
            kar.write_uint16(note['Cue ID'])
            if data['Header']['Version'] != 1:
                kar.write_uint32(note['Unknown 18'])

        texture_pos = kar.pos()
        kar.write_str(data['Lines'][i]['Texture name'])
        kar.align(0x4)
        if data['Lines'][i]['Texture name'] != "lyric_dmmy.dds":
            kar.write_uint32(0)
            kar.write_uint32(0)
            if data['Header']['Version'] > 3:
                kar.write_uint32(0)
        new_pointers.append((note_pos, settings_pos, texture_pos))

    # update pointers
    for i in range(len(new_pointers)):
        kar.seek(old_pointers[i][0])
        kar.write_uint32(new_pointers[i][0])

        kar.seek(old_pointers[i][1])
        kar.write_uint32(new_pointers[i][1])

        kar.seek(old_pointers[i][2])
        kar.write_uint32(new_pointers[i][2])

    # saving the file
    with open(filename, 'wb') as f:
        f.write(kar.buffer())

# functions required for reading


def get_version(content):
    if content == 0:
        return 3  # Yakuza 5 +
    else:
        return 2  # Yakuza 4 and Dead Souls


def get_notes(kar, note_count, version):
    note_list = list()
    for i in range(note_count):
        note = {}
        note['Index'] = i
        note['Note type'] = kar.read_uint32()
        note['Start position'] = kar.read_float()
        note['End position'] = kar.read_float()
        note['Button type'] = kar.read_uint32()
        note['Unknown 17'] = kar.read_uint32()
        note['Cuesheet ID'] = kar.read_uint16()
        note['Cue ID'] = kar.read_uint16()
        if version == 1:
            note['Unknown 18'] = 0
        else:
            note['Unknown 18'] = kar.read_uint32()
        note_list.append(note)
    return note_list


def get_settings(kar):
    settings = dict()
    settings['Line length'] = kar.read_uint32()
    settings['Line start time (ms)'] = kar.read_uint32()
    settings['Line end time (ms)'] = kar.read_uint32()
    return settings


def read_file(input_file, y3_mode=False):
    """Reads the KARA file and returns a dict.\n
    The first parameter is the filename and the second optional parameter is Y3 mode."""
    # opening the file
    with open(input_file, 'rb') as file:
        kar = BinaryReader(file.read(), True)  # reading file as big endian
    # making a dict for the data
    data = dict()
    data['Header'] = dict()
    # reading the file header
    data['Header']['Magic'] = kar.read_str(4)  # read magic
    kar.seek(2, 1)  # endian identifier
    if data['Header']['Magic'] != 'KARA':  # in case it's not a valid file
        raise ValueError('Not a valid KARA file')

    if y3_mode:
        data['Header']['Version'] = 1  # Yakuza 3
    else:
        with kar.seek_to(0, 1):
            data['Header']['Version'] = get_version(kar.read_uint16())

    if data['Header']['Version'] < 3:
        data['Header']['Line count'] = kar.read_uint8()
        data['Header']['Unknown 1'] = kar.read_uint8()
        data['Header']['Unknown 2'] = kar.read_uint32()

    else:
        kar.seek(2, 1)
        data['Header']['Unknown 2'] = kar.read_uint32()

    kar.seek(4, 1)
    if data['Header']['Version'] == 3:
        data['Header']['Line count'] = kar.read_uint8()
        data['Header']['Unknown 1'] = kar.read_uint8()
        kar.seek(14, 1)
    # MAIN TABLE
    data['Main table'] = {}
    data['Main table']['Unknown 2'] = kar.read_uint32()
    data['Main table']['Unknown 3'] = kar.read_uint32()
    data['Main table']['Notes for cutscene'] = kar.read_uint32()
    data['Main table']['Unknown 4'] = kar.read_uint32()
    data['Main table']['Unknown 5'] = kar.read_uint32()
    data['Main table']['Unknown 6'] = kar.read_uint32()
    data['Main table']['Unknown 7'] = kar.read_uint32()
    data['Main table']['Unknown 8'] = kar.read_uint32()
    data['Main table']['Unknown 9'] = kar.read_float()
    data['Main table']['Unknown 10'] = kar.read_float()
    data['Main table']['Unknown 11'] = kar.read_float()
    data['Main table']['Cheer difficulty'] = kar.read_uint32()
    data['Main table']['Unknown 12'] = kar.read_uint32()
    data['Main table']['Great range'] = kar.read_float()
    data['Main table']['Good range'] = kar.read_float()
    data['Main table']['Unknown 13'] = kar.read_uint32()

    # reading the lines
    line_list = list()
    for i in range(data['Header']['Line count']):
        line = dict()
        line['Index'] = i
        line['Vertical position'] = kar.read_uint32()
        note_section_pointer = kar.read_uint32()
        line['Note count'] = kar.read_uint32()

        with kar.seek_to(note_section_pointer):
            line['Notes'] = get_notes(
                kar, line['Note count'], data['Header']['Version'])

        line_settings_pointer = kar.read_uint32()

        with kar.seek_to(line_settings_pointer):
            line['Settings'] = get_settings(kar)

        line['Unknown 14'] = kar.read_uint32()
        texture_name_pointer = kar.read_uint32()
        with kar.seek_to(texture_name_pointer):
            line['Texture name'] = kar.read_str()

        line['Unknown 15'] = kar.read_uint32()
        line['Line spawn'] = kar.read_uint32()
        line['Line despawn'] = kar.read_uint32()
        if i < data['Header']['Line count']:  # doesn't exist for last note
            line['Line page'] = kar.read_uint32()

        line_list.append(line)

    data['Lines'] = line_list

    return data
