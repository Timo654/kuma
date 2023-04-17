from binary_reader import BinaryReader


def write_file(data, filename):
    """Writes the wtfl from dict to the specified filename.\n
    The first parameter is a dict containing info read from wtfl and\n
    the second parameter is the filename."""
    wtfl = BinaryReader(bytearray(), True)
    # writing the header

    # HEADER
    wtfl.write_str('LFTW')  # magic
    wtfl.write_uint16(0x201)  # endian check
    wtfl.write_uint8(len(data['Notes']))  # note count
    wtfl.write_uint8(data['Header']['Unknown 1'])
    wtfl.write_uint32(int(data['Header']['Version'], 16))
    wtfl.write_uint32(0)  # padding
    if int(data['Header']['Version'], 16) > 0x1000000:
        wtfl.write_str(data['Header']['Stage'])

    # NOTES
    for i in range(len(data['Notes'])):
        note = data['Notes'][i]
        wtfl.write_uint32(note['Button type'])
        wtfl.write_float(note['Position'])

    # saving the file
    with open(filename, 'wb') as f:
        f.write(wtfl.buffer())


def read_file(input_file):
    """Reads the wtfl file and returns a dict.\n
    The first and only parameter is the filename"""
    # opening the file
    with open(input_file, 'rb') as file:
        wtfl = BinaryReader(file.read(), True)  # reading file as big endian
    # making a dict for the data
    data = dict()
    data['Header'] = dict()
    # reading the file header
    data['Header']['Magic'] = wtfl.read_str(4)
    if data['Header']['Magic'] != 'LFTW':  # in case it's not a valid file
        raise ValueError('Not a valid WTFL file')

    # HEADER
    wtfl.seek(2, 1)  # endian check
    data['Header']['Number of notes'] = wtfl.read_uint8()
    data['Header']['Unknown 1'] = wtfl.read_uint8()
    data['Header']['Version'] = hex(wtfl.read_uint32())
    wtfl.seek(4, 1)
    if int(data['Header']['Version'], 16) > 0x1000000:
        data['Header']['Stage'] = wtfl.read_str(13)

    # NOTES
    note_list = list()
    for i in range(data['Header']['Number of notes']):
        note = dict()
        note['Button type'] = wtfl.read_uint32()
        note['Position'] = wtfl.read_float()  # time is seconds
        note_list.append(note)

    data['Notes'] = note_list
    return data
