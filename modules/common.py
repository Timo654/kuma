from enum import IntEnum

class ExtendedEnum(IntEnum):
# https://stackoverflow.com/questions/29503339/how-to-get-all-values-from-python-enum-class
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

class Button(ExtendedEnum):
    """Note enums"""
    Circle = 0
    Cross = 1
    Square = 2
    Triangle = 3
    DPad_Button = 4
    BlueAny = 5
    GoldAny = 6
    RapidLine = 50
    HoldLine = 51
    Unimplemented = 99

class Note(ExtendedEnum):
    "Note type enum"
    Regular = 0
    Hold = 1
    Rapid = 2
    DPad = 3
    End = 98
    Unimplemented = 99


def get_vert_pos(button):
    if button == Button.Circle:
        return 4
    elif button == Button.Cross:
        return 6
    elif button == Button.Square:
        return 2
    elif button == Button.Triangle:
        return 0