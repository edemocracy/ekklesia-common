from datetime import datetime, timezone

from freezegun import freeze_time

from ekklesia_common.lid import LID


def test_from_lid_from_int():
    lid_int = 6705847306369952472
    lid = LID(lid_int)
    assert lid.milliseconds == 1598798586456
    assert lid.repr == "1EGZX4RJR-31TPR"
    assert lid.datetime == datetime(2020, 8, 30, 14, 43, 6, 456000, tzinfo=timezone.utc)


def test_create_lid():
    with freeze_time("2020-08-31 12:00:01"):
        lid = LID()
    ts_str, rand_str = lid.repr.split("-")
    assert len(ts_str) == 9
    assert len(rand_str) == 5
    assert lid.datetime
    assert lid.milliseconds


def test_compare_lid():
    with freeze_time("2020-08-31 12:00:01"):
        lid1 = LID()

    with freeze_time("2020-08-31 12:00:02"):
        lid2 = LID()

    assert lid1 < lid2
    assert lid2 > lid1


def test_lid_equality():
    lid = LID()
    assert lid == LID(lid.lid)
    assert lid == lid.lid


def test_lid_from_str():
    lid_str = "1EGZX4RJR-31TPR"
    lid = LID.from_str(lid_str)
    assert lid.repr == lid_str
    assert lid == lid_str
