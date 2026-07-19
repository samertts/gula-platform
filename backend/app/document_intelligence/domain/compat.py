from enum import Enum as _Enum


class StrEnum(str, _Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[str]) -> str:
        return name
