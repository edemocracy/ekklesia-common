from io import StringIO

from ekklesia_common.babel import extract_enums

code = """
# Line 2
class FirstEnum(Enum):
    A = 'a' # comment
    B = 'b/b'

class SecondEnum(Enum):
    # comment
    C = 'c c'

class SomethingElse:
    pass
"""


def test_extract_enums():

    translations = extract_enums(StringIO(code), [], [], {})

    expected = [
        (4, "gettext", "first_enum_a", ["FirstEnum.A"]),
        (5, "gettext", "first_enum_b_b", ["FirstEnum.B"]),
        (9, "gettext", "second_enum_c_c", ["SecondEnum.C"]),
    ]

    assert translations == expected
