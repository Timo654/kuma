from binary_reader import BinaryReader


def write_file(data, filename):
    """Writes the lbd from dict to the specified filename.\n
    The first parameter is a dict containing info read from lbd and\n
    the second parameter is the filename."""
    lbd = BinaryReader(bytearray(), True)
    # writing the header

    lbd.write_uint16(data['Header']['Version'])
    if data['Header']['Version'] == 0:
        lbd.write_uint16(len(data['Notes']))
    else:
        lbd.write_uint16(0xFFFF)
        lbd.write_uint32(len(data['Notes']))
    lbd.write_uint32(data['Header']['Climax heat'])
    lbd.write_uint32(data['Header']['Unknown 1'])
    lbd.write_int32(data['Header']['Hit Range (Before)'])
    lbd.write_int32(data['Header']['Good Range (Before)'])
    lbd.write_int32(data['Header']['Great Range (Before)'])
    lbd.write_int32(data['Header']['Special Mode Start'])
    lbd.write_uint32(data['Header']['Special Mode Length'])
    if data['Header']['Version'] > 0:
        lbd.write_uint32(data['Header']['Scale'])
        lbd.write_int32(data['Header']['Good Range (After)'])
        lbd.write_int32(data['Header']['Great Range (After)'])
        lbd.write_int32(data['Header']['Hit Range (After)'])

    if data['Header']['Version'] > 3:
        lbd.write_uint64(0)
        lbd.write_uint32(0)

    # writing the notes
    for i in range(len(data['Notes'])):
        note = data['Notes'][i]
        lbd.write_uint8(note['Unknown 2'])
        lbd.write_uint8(note['Line'])
        lbd.write_uint8(note['Unknown 3'])
        lbd.write_uint8(note['Button type'])
        lbd.write_int32(note['Start position'])
        lbd.write_int32(note['End position'])

        if data['Header']['Version'] > 3:
            lbd.write_uint32(note['Grid position'])

    if data['Header']['Climax heat']:
        lbd.write_int32(data['Header']['Costume Switch Start'])
        lbd.write_int32(data['Header']['Costume Switch End'])

    # saving the file
    with open(filename, 'wb') as f:
        f.write(lbd.buffer())


def read_file(input_file):
    """Reads the lbd file and returns a dict.\n
    The first and only parameter is the filename"""
    # opening the file
    with open(input_file, 'rb') as file:
        lbd = BinaryReader(file.read(), True)  # reading file as big endian
    # making a dict for the data
    data = dict()
    data['Header'] = dict()
    # reading the file header
    data['Header']['Version'] = lbd.read_uint16()  # read version number

    if data['Header']['Version'] > 4:  # in case it's not a valid file
        raise ValueError('Not a valid LBD file')

    if data['Header']['Version'] == 0:  # different in first version
        data['Header']['Note count'] = lbd.read_uint32()
    else:
        data['Header']['Filler'] = lbd.read_uint16()  # filler
        if data['Header']['Filler'] != 65535:  # in case it's not a valid file
            raise ValueError('Not a valid LBD file')

        data['Header']['Note count'] = lbd.read_uint32()
    data['Header']['Climax heat'] = bool(lbd.read_uint32())
    data['Header']['Unknown 1'] = lbd.read_uint32()
    data['Header']['Hit Range (Before)'] = lbd.read_int32()
    data['Header']['Good Range (Before)'] = lbd.read_int32()
    data['Header']['Great Range (Before)'] = lbd.read_int32()
    data['Header']['Special Mode Start'] = lbd.read_int32()
    data['Header']['Special Mode Length'] = lbd.read_uint32()
    if data['Header']['Version'] > 0:
        data['Header']['Scale'] = lbd.read_uint32()
        data['Header']['Good Range (After)'] = lbd.read_int32()
        data['Header']['Great Range (After)'] = lbd.read_int32()
        data['Header']['Hit Range (After)'] = lbd.read_int32()

    if data['Header']['Version'] > 3:
        lbd.seek(12, 1)  # padding

    # reading the notes
    note_list = list()
    for i in range(data['Header']['Note count']):
        note = dict()
        note['Index'] = i
        note['Unknown 2'] = lbd.read_uint8()
        note['Line'] = lbd.read_uint8()
        note['Unknown 3'] = lbd.read_uint8()
        note['Button type'] = lbd.read_uint8()
        # Time is in the 'Yakuza' format, 1 unit is 1/3 ms. Conversion could be handled by the GUI.
        note['Start position'] = lbd.read_int32()
        note['End position'] = lbd.read_int32()

        if data['Header']['Version'] > 3:
            note['Grid position'] = lbd.read_uint32()
        note_list.append(note)

    data['Notes'] = note_list
    # Time is in the 'Yakuza' format
    if data['Header']['Climax heat']:
        data['Header']['Costume Switch Start'] = lbd.read_uint32()
        data['Header']['Costume Switch End'] = lbd.read_uint32()

    return data
