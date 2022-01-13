from binary_reader import BinaryReader

def write_file(data, filename):
    """Writes the mns from dict to the specified filename.\n
    The first parameter is a dict containing info read from mns and\n
    the second parameter is the filename."""
    mns = BinaryReader(bytearray())
    # writing the header

    mns.write_str('MNS', null=True)
    mns.write_uint32(data['Header']['Field04'])
    mns.write_uint32(data['Header']['Field08'])
    mns.write_uint32(data['Header']['Music ID'])
    mns.write_float(data['Header']['BPM'])
    mns.write_uint16(data['Header']['Music ID Major'])
    mns.write_uint16(data['Header']['Music ID Minor'])
    mns.write_uint32(data['Header']['Field18'])
    mns.write_uint32(data['Header']['Number of notes'])
    mns.write_uint32(data['Header']['Field20'])

    # writing the notes
    for i in range(len(data['Notes'])):
        note = data['Notes'][i]
        mns.write_uint16(note['Beat'])
        mns.write_uint16(note['Measure'])
        mns.write_uint8(note['Button type'])
        mns.write_int8(note['Hold duration'])
        mns.write_int16(note['Type'])
        if note['Type'] != 0:
            print(note['Type'])

    # saving the file
    with open(filename, 'wb') as f:
        f.write(mns.buffer())

def read_file(input_file):
    """Reads the mns file and returns a dict.\n
    The first and only parameter is the filename"""
    # big thanks to TGE for the template https://github.com/TGEnigma/010-Editor-Templates/blob/master/templates/p4d_mns.bt
    # opening the file
    with open(input_file, 'rb') as file:
        mns = BinaryReader(file.read())  # reading file as little endian
    # making a dict for the data
    data = dict()
    data['Header'] = dict()
    # reading the file header
    data['Header']['Magic'] = mns.read_str(4)
    if data['Header']['Magic'] != 'MNS':  # in case it's not a valid file
        raise ValueError('Not a valid mns file')

    # HEADER
    data['Header']['Field04'] = mns.read_uint32()  # always 0
    data['Header']['Field08'] = mns.read_uint32()  # always 1
    data['Header']['Music ID'] = mns.read_uint32()
    data['Header']['BPM'] = mns.read_float()
    # does not always match Music ID
    data['Header']['Music ID Major'] = mns.read_uint16()
    data['Header']['Music ID Minor'] = mns.read_uint16()
    data['Header']['Field18'] = mns.read_uint32()  # always 0
    # does not include duplicates
    data['Header']['Number of notes'] = mns.read_uint32()
    data['Header']['Field20'] = mns.read_uint32()
    data['Header']['Actual note count'] = (mns.size() - mns.pos()) // 8
    # NOTES
    note_list = list()
    for _ in range(data['Header']['Actual note count']):
        note = dict()
        note['Beat'] = mns.read_uint16()
        note['Measure'] = mns.read_uint16()
        note['Button type'] = mns.read_uint8()
        note['Hold duration'] = mns.read_uint8()
        note['Type'] = mns.read_uint16()
        note_list.append(note)

    data['Notes'] = note_list
    return data
