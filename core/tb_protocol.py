"""Native bridge contract. Independent of the public app version."""
PROTOCOL_VERSION = 1


def compatible(value):
    return type(value) is int and value == PROTOCOL_VERSION
