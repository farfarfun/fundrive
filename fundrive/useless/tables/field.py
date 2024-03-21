from enum import Enum


class FieldType(bytes, Enum):
    NONE = (0, ['none', 'NONE'])
    STRING = (10, ['string', 'STRING', 'str', 'STR'])
    VARCHAR = (11, ['varchar', 'VARCHAR'])
    FLOAT = (20, ['float', 'FLOAT'])
    DOUBLE = (30, ['double', 'DOUBLE'])
    BIGINT = (40, ['bigint', 'BIGINT'])
    INTEGER = (50, ['integer', 'int', 'INTEGER', 'INT'])
    TINYINT = (51, ['tinyint', 'TINYINT'])

    def __init__(self, value, names):
        self._value_ = value
        self.names = names

    def __new__(cls, value, names):
        obj = bytes.__new__(cls, [value])
        obj._value_ = value
        obj.names = names
        return obj

    @staticmethod
    def parse(field_type):
        if isinstance(field_type, FieldType):
            return field_type
        for filed in FieldType:
            if field_type in filed.names:
                return filed
        return FieldType.NONE


class Field:
    def __init__(self, name, field_type, comment=""):
        self.name = name
        self.field_type = FieldType.parse(field_type)
        self.comment = comment

    @staticmethod
    def double_field(name, comment=""):
        return Field(name, FieldType.DOUBLE, comment)

    @staticmethod
    def bigint_field(name, comment=""):
        return Field(name, FieldType.BIGINT, comment)

    @staticmethod
    def float_field(name, comment=""):
        return Field(name, FieldType.FLOAT, comment)

    @staticmethod
    def string_field(name, comment=""):
        return Field(name, FieldType.STRING, comment)

    @staticmethod
    def varchar_field(name, comment=""):
        return Field(name, FieldType.VARCHAR, comment)

    @staticmethod
    def integer_field(name, comment=""):
        return Field(name, FieldType.INTEGER, comment)
