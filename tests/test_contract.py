import json
import colander
from pytest import raises
from ekklesia_common.contract import JSONObject


def test_json_object_serialize():
    obj = JSONObject()
    appstruct = {'a': 4, 'b': 6}
    assert obj.serialize(None, appstruct) == json.dumps(appstruct)


def test_json_object_deserialize():
    obj = JSONObject()
    cstruct = '{"a": 4, "b": 6}'
    assert obj.deserialize(None, cstruct) == json.loads(cstruct)


def test_json_object_not_serializable():
    obj = JSONObject()
    appstruct = []

    with raises(colander.Invalid):
         obj.serialize(None, appstruct)


def test_json_object_not_deserializable():
    obj = JSONObject()
    cstruct = '"a 6}'

    with raises(colander.Invalid):
         obj.deserialize(None, cstruct)

    cstruct = '[]'

    with raises(colander.Invalid):
         obj.deserialize(None, cstruct)

