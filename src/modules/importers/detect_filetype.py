from io import UnsupportedOperation
from binary_reader import BinaryReader
import json
from modules.importers.lbd_import import load_lbd
from modules.importers.kara_import import load_kara
from modules.importers.mns_import import load_mns
from modules.importers.wtfl_import import load_wtfl
from modules.importers.dsc_import import load_dsc


def load_file(filename):
    filename_str = str(filename)
    if filename_str.endswith('txt'):
        return load_dsc(filename)
    if filename_str.endswith('lbd'):
        return load_lbd(filename)
    elif filename_str.endswith('json'):
        with open(filename, 'r') as f:
            return json.loads(f.read())
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
