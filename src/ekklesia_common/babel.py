"""Babel extractor for Python enum modules.

For example, the enum

class FirstEnum(Enum):
    A = 'a' # comment
    B = 'b/b'

will produce two translation messages with msgids `first_enum_a` and `first_enum_b_b`.

Add to your babel.cfg (order is important here):

[extractors]
python_enums = ekklesia_common.babel:extract_enums

[python_enums: src/ekklesia_package/enums.py]

[python: **.py]

"""


import ast

from case_conversion import snakecase


def is_enum_node(node):
    if not isinstance(node, ast.ClassDef):
        return False

    return any(b.id == "Enum" for b in node.bases)


def translation_from_enum_assignment(enum_name, assignment):
    comments = [enum_name + "." + assignment.targets[0].id]
    translation = snakecase(enum_name) + "_" + snakecase(assignment.value.s)
    return assignment.lineno, "gettext", translation, comments


def translations_from_enum(enum_node):
    assignments = [n for n in enum_node.body if isinstance(n, ast.Assign)]
    return [translation_from_enum_assignment(enum_node.name, a) for a in assignments]


def extract_enums(fileobj, keywords, comment_tags, options):
    module_node = ast.parse(fileobj.read())
    enum_nodes = [n for n in module_node.body if is_enum_node(n)]
    translations = [translations_from_enum(n) for n in enum_nodes]

    # Flatten list of lists.
    return [t for ts in translations for t in ts]
