from io import UnsupportedOperation
from binary_reader import BinaryReader
from modules.importers.lbd_import import load_lbd
from modules.importers.kara_import import load_kara
from modules.importers.mns_import import load_mns
from modules.importers.wtfl_import import load_wtfl


def load_file(filename):
    if str(filename).endswith('lbd'):
        return load_lbd(filename)
    with open(filename, 'rb') as file:
        br = BinaryReader(file.read())
    magic = br.read_uint32()
    if magic == 5459533:  # MNS
        return load_mns(filename)
    elif magic == 1095909707:  # KARA
        return load_kara(filename)
    elif magic == 1465140812:  # WTFL
        return load_wtfl(filename)
    else:
        raise UnsupportedOperation('Unsupported file format.')
