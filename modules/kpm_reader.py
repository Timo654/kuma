from binary_reader import BinaryReader


def write_file(data, filename):
    """Writes the kpm from dict to the specified filename.\n
    The first parameter is a dict containin info read from the kpm.\n
    The second parameter is the filename."""

    # this is where we will write the parameter data
    kpm_p = BinaryReader(bytearray())
    for param in data['Parameters']:
        kpm_p.write_float(param['Great range (Before)'])
        kpm_p.write_float(param['Good range (Before)'])
        kpm_p.write_float(param['Great range (After)'])
        kpm_p.write_float(param['Good range (After)'])
        kpm_p.write_float(param['Great Hold percentage'])
        kpm_p.write_float(param['Good Hold percentage'])
        kpm_p.write_uint32(param['Great Rapid press'])
        kpm_p.write_uint32(param['Good Rapid press'])
        kpm_p.write_float(param['Scale'])
        kpm_p.write_float(param['Cutscene start time'])
        if data['Header']['Version'] > 0:
            # no idea what it does, was introduced in YLAD
            kpm_p.write_float(param['Unknown 1'])

    # writing the header
    kpm_h = BinaryReader(bytearray())  # this is where we will write the header
    kpm_h.write_str('MRPK')  # magic will always be MRPK
    kpm_h.write_uint32(0)  # padding
    kpm_h.write_uint32(data['Header']['Version'])
    kpm_h.write_uint32(kpm_p.size())  # size of the params portion of the file
    kpm_h.write_uint32(len(data['Parameters']))  # amount of params

    kpm_h.extend(kpm_p.buffer())  # merge header and params
    # saving the file
    with open(filename, 'wb') as f:
        f.write(kpm_h.buffer())


def read_file(input_file):
    """Reads the kpm file and returns a dict.\n
    The first and only parameter is the filename"""
    # opening the file
    with open(input_file, 'rb') as file:
        kpm = BinaryReader(file.read())  # reading file as little endian
    # making a dict for the data
    data = dict()
    data['Header'] = dict()
    # reading the file header
    data['Header']['Magic'] = kpm.read_str(4)  # read 4 characters
    if data['Header']['Magic'] != 'MRPK':  # in case it's not a valid file
        raise Exception('Not a valid DE karaoke file.')
    kpm.seek(4, 1)  # unused, filler, skipping this
    data['Header']['Version'] = kpm.read_uint32()
    kpm.seek(4, 1)  # file size without header, we're skipping this
    data['Header']['Parameter count'] = kpm.read_uint32()

    # reading the parameter(s)
    param_list = list()
    for i in range(data['Header']['Parameter count']):
        param = dict()
        param['Index'] = i
        # before means before the button goes by and after means after it goes by
        param['Great range (Before)'] = kpm.read_float()
        param['Good range (Before)'] = kpm.read_float()
        param['Great range (After)'] = kpm.read_float()
        param['Good range (After)'] = kpm.read_float()
        # how long to hold
        param['Great Hold percentage'] = kpm.read_float()
        param['Good Hold percentage'] = kpm.read_float()
        # how many times to press
        param['Great Rapid press'] = kpm.read_uint32()
        param['Good Rapid press'] = kpm.read_uint32()
        # "zoom" of the params, changes how much of the song you can see
        param['Scale'] = kpm.read_float()
        param['Cutscene start time'] = kpm.read_float()
        if data['Header']['Version'] > 0:
            # no idea what it does, was introduced in YLAD
            param['Unknown 1'] = kpm.read_float()
        param_list.append(param)

    data['Parameters'] = param_list

    return data
