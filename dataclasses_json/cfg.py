import functools
from enum import Enum
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Union

from marshmallow.fields import Field as MarshmallowField
from dataclasses_json.custom_types import T

from dataclasses_json.stringcase import camelcase  # type: ignore
from dataclasses_json.stringcase import pascalcase
from dataclasses_json.stringcase import snakecase
from dataclasses_json.stringcase import spinalcase
from dataclasses_json.undefined import Undefined
from dataclasses_json.undefined import UndefinedParameterError


class Exclude:
    """
    Pre-defined constants for exclusion. By default, fields are configured to
    be included.
    """
    ALWAYS: Callable[[T], bool] = lambda _: True
    NEVER: Callable[[T], bool] = lambda _: False


class LetterCase(Enum):
    CAMEL = camelcase
    KEBAB = spinalcase
    SNAKE = snakecase
    PASCAL = pascalcase


def config(metadata: dict = None, *,
           # TODO: these can be typed more precisely
           # Specifically, a Callable[A, B], where `B` is bound as a JSON type
           encoder: Callable = None,
           decoder: Callable = None,
           mm_field: MarshmallowField = None,
           letter_case: Union[Callable[[str], str], LetterCase, None] = None,
           undefined: Optional[Union[str, Undefined]] = None,
           field_name: str = None,
           exclude: Union[Callable[[str, T], bool], Exclude, None] = None,
           ) -> Dict[str, dict]:
    if metadata is None:
        metadata = {}

    lib_metadata = metadata.setdefault('dataclasses_json', {})

    if encoder is not None:
        lib_metadata['encoder'] = encoder

    if decoder is not None:
        lib_metadata['decoder'] = decoder

    if mm_field is not None:
        lib_metadata['mm_field'] = mm_field

    if field_name is not None:
        if letter_case is not None:
            @functools.wraps(letter_case)  # type:ignore
            def override(_, _letter_case=letter_case, _field_name=field_name):
                return _letter_case(_field_name)
        else:
            def override(_, _field_name=field_name):  # type:ignore
                return _field_name
        letter_case = override

    if letter_case is not None:
        lib_metadata['letter_case'] = letter_case

    if undefined is not None:
        # Get the corresponding action for undefined parameters
        if isinstance(undefined, str):
            if not hasattr(Undefined, undefined.upper()):
                valid_actions = list(action.name for action in Undefined)
                raise UndefinedParameterError(
                    f"Invalid undefined parameter action, "
                    f"must be one of {valid_actions}")
            undefined = Undefined[undefined.upper()]

        lib_metadata['undefined'] = undefined

    if exclude is not None:
        lib_metadata['exclude'] = exclude

    return metadata
