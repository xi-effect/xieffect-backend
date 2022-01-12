from __future__ import annotations

from enum import Enum
from typing import Union


class TypeEnum(Enum):
    @classmethod
    def from_string(cls, string: str) -> Union[TypeEnum, None]:
        return cls.__members__.get(string.upper().replace("-", "_"), None)  # TODO NonePointer!!!

    @classmethod
    def get_all_field_names(cls) -> list[str]:
        return [member.lower().replace("_", "-") for member in cls.__members__]

    @classmethod
    def form_whens(cls) -> list[tuple[str, int]]:
        return [(name, value.value) for name, value in cls.__members__.items()]  # TODO IntEnum needed

    def to_string(self) -> str:
        return self.name.lower().replace("_", "-")
