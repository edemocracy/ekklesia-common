from deform import Form
from deform.widget import HiddenWidget
from ekklesia_portal.enums import ArgumentType
from ekklesia_portal.helper.contract import enum_property, string_property, int_property
from ekklesia_portal.concepts.argument.argument_contracts import argument_widgets, ArgumentSchema


class ArgumentForPropositionSchema(ArgumentSchema):
    proposition_id = int_property()
    relation_type = enum_property(ArgumentType)


class ArgumentForPropositionForm(Form):

    def __init__(self, request, action):
        super().__init__(ArgumentForPropositionSchema(), request, action, buttons=("submit", ))
        self.set_widgets({
            'proposition_id': HiddenWidget(),
            'relation_type': HiddenWidget(),
            **argument_widgets
        })
