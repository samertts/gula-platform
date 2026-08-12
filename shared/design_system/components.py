from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ButtonVariant(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    OUTLINE = "outline"
    GHOST = "ghost"
    DANGER = "danger"


class ButtonSize(Enum):
    SM = "sm"
    MD = "md"
    LG = "lg"


class InputType(Enum):
    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    TEL = "tel"
    DATE = "date"
    FILE = "file"
    SELECT = "select"
    TEXTAREA = "textarea"


class TableVariant(Enum):
    STRIPED = "striped"
    BORDERED = "bordered"
    HOVER = "hover"
    COMPACT = "compact"


@dataclass
class ButtonSpec:
    label: str = ""
    variant: ButtonVariant = ButtonVariant.PRIMARY
    size: ButtonSize = ButtonSize.MD
    icon: str = ""
    disabled: bool = False
    loading: bool = False
    full_width: bool = False
    aria_label: str = ""


@dataclass
class CardSpec:
    title: str = ""
    subtitle: str = ""
    elevated: bool = True
    bordered: bool = False
    padding: str = "md"
    header_action: str = ""


@dataclass
class DialogSpec:
    title: str = ""
    description: str = ""
    confirm_label: str = "Confirm"
    cancel_label: str = "Cancel"
    confirm_variant: ButtonVariant = ButtonVariant.PRIMARY
    size: str = "md"
    closable: bool = True
    rtl: bool = True


@dataclass
class FormSpec:
    title: str = ""
    submit_label: str = "Submit"
    cancel_label: str = "Cancel"
    layout: str = "vertical"
    rtl: bool = True
    validate_on_change: bool = True


@dataclass
class InputSpec:
    label: str = ""
    placeholder: str = ""
    input_type: InputType = InputType.TEXT
    required: bool = False
    disabled: bool = False
    error: str = ""
    helper_text: str = ""
    rtl: bool = True
    max_length: int = 0


@dataclass
class TableSpec:
    columns: list[dict[str, Any]] = field(default_factory=list)
    variant: TableVariant = TableVariant.STRIPED
    striped: bool = True
    hoverable: bool = True
    bordered: bool = False
    compact: bool = False
    sortable: bool = True
    filterable: bool = False
    paginated: bool = True
    page_size: int = 20
    rtl: bool = True


@dataclass
class IconSpec:
    name: str = ""
    size: str = "24"
    color: str = "currentColor"
    stroke_width: float = 2.0
