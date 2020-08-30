"""
LID: lexicographically sortable identifier.
Similar to ULID but only 64 bit to fit in a Postgres bigint and for a shorter string representation
String representation uses base32-crockford-encoded and looks like this: 1EGZX4RJR-31TPR
The first part is a timestamp in milliseconds since the epoch (42 bits).
The second part is a random number (22 bits).
"""

from functools import cached_property, total_ordering
import random
import time
from datetime import datetime
import base32_crockford


def encode_random(val):
    b32 = base32_crockford.encode(val)
    return f"{b32:0>5s}"


def encode_timestamp(val):
    b32 = base32_crockford.encode(val)
    return f"{b32:0>9s}"


@total_ordering
class LID:

    def __init__(self, lid: int = None) -> None:

        if lid is None:
            milliseconds = int(time.time() * 1000)
            rand = random.randrange(0, 2**22)
            lid = (milliseconds << 22) | rand
        else:
            milliseconds = lid >> 22
            rand = lid & (2**22 - 1)

        ts_repr = encode_timestamp(milliseconds)
        rand_repr = encode_random(rand)
        self.repr = ts_repr + "-" + rand_repr
        self.lid = lid
        self.milliseconds = milliseconds

    def __lt__(self, other):
        if isinstance(other, LID):
            return self.lid < other.lid
        elif isinstance(other, int):
            return self.lid < other
        elif isinstance(other, str):
            return self.repr < other

        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, LID):
            return self.lid == other.lid
        elif isinstance(other, int):
            return self.lid == other
        elif isinstance(other, str):
            return self.repr == other

        return NotImplemented

    def __str__(self):
        return self.repr

    def __repr__(self):
        return f"LID({self!s})"

    def __int__(self):
        return self.lid

    def __hash__(self):
        return hash(self.lid)

    @classmethod
    def from_str(cls, lid_str) -> "LID":
        ts_repr, rand_repr = lid_str.split("-")
        milliseconds = base32_crockford.decode(ts_repr)
        rand = base32_crockford.decode(rand_repr)
        return cls((milliseconds << 22) | rand)

    @cached_property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.milliseconds / 1000)

