from contextlib import contextmanager
from enum import Enum


@contextmanager
def assert_no_difference(func, name=None):
    """Asserts that the function result is unchanged after executing the block"""
    val = func()
    yield
    val_after = func()

    def assertion_msg():
        msg = f"result is not the same! value before {val}, after: {val_after}"
        if name:
            return f"{name}: " + msg
        return msg

    assert val_after == val, assertion_msg()


@contextmanager
def assert_difference(func, diff, name=None):
    """
    Asserts that the function result has changed by `diff` after executing the block
    `diff` can be anything, but addition with the result of `func` must be defined.
    """
    val = func()
    yield
    val_after = func()

    def assertion_msg():
        msg = f"result for did not change by {diff}! value before {val}, after: {val_after}"
        if name:
            return f"{name}: " + msg
        return msg

    assert val_after == val + diff, assertion_msg()


def python_to_deform_value(py_value):
    match py_value:
        case True:
            return "true"
        case False:
            return None
        case None:
            return ""
        case Enum() as enum:
            return enum.name
        case other:
            return str(other)


def assert_deform(response, expected_form_data={}):
    assert "deform" in response.forms
    form = response.forms["deform"]
    missing_fields = []

    for field, value in expected_form_data.items():
        if field == "id":
            continue

        try:
            form[field]
        except AssertionError:
            missing_fields.append(field)
            continue

        form_value = form[field].value

        deform_value = python_to_deform_value(value)
        assert (
            form_value == deform_value
        ), f"form field {field}: form value {form_value} != expected {deform_value}"

    if missing_fields:
        fields_str = ", ".join(missing_fields)
        raise AssertionError(f"missing expected form fields: '{fields_str}'")

    return form


def get_session(app, client):
    serializer = app.browser_session_interface.get_signing_serializer(app)
    assert "session" in client.cookies
    return serializer.loads(client.cookies["session"])


def _set_form_field_value(
    form, data, field_name, enum_field_names, relation_field_names
):
    if field_name in enum_field_names:
        value = data[field_name].name
        form.set(field_name, value)
    elif field_name in relation_field_names:
        value = data[field_name].id
        print(field_name, value)
        form.set(field_name + "_id", value)
    else:
        value = data[field_name]
        form.set(field_name, value)


def fill_form(
    form,
    data,
    field_names=None,
    skip_field_names=[],
    enum_field_names=[],
    relation_field_names=[],
):
    if field_names is None:
        for field_name in data:
            if field_name not in skip_field_names:
                _set_form_field_value(
                    form, data, field_name, enum_field_names, relation_field_names
                )
    else:
        for field_name in field_names:
            _set_form_field_value(
                form, data, field_name, enum_field_names, relation_field_names
            )

    return form
