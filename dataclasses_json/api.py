import abc
import json
from typing import (Callable, Dict, Optional, Tuple, Type, Union)

from dataclasses_json.cfg import config, LetterCase  # noqa: F401
from dataclasses_json.core import (_asdict,
                                   _decode_dataclass)
from dataclasses_json.custom_types import Json
from dataclasses_json.custom_types import A
from dataclasses_json.mm import (JsonData, SchemaType, build_schema)
from dataclasses_json.serialization import Codecs
from dataclasses_json.serialization import DefaultJsonCodecs
from dataclasses_json.undefined import Undefined
from dataclasses_json.utils import (_handle_undefined_parameters_safe,
                                    _undefined_parameter_action_safe)


class DataClassJsonMixin(abc.ABC):
    """
    DataClassJsonMixin is an ABC that functions as a Mixin.

    As with other ABCs, it should not be instantiated directly.
    """
    dataclass_json_config = None

    def to_json(self,
                *,
                skipkeys: bool = False,
                ensure_ascii: bool = True,
                check_circular: bool = True,
                allow_nan: bool = True,
                indent: Optional[Union[int, str]] = None,
                separators: Tuple[str, str] = None,
                default: Callable = None,
                sort_keys: bool = False,
                codecs: Optional[Codecs] = None,
                **kw) -> str:
        return json.dumps(self.to_dict(encode_json=True, codecs=codecs),
                          cls=codecs.encoder if codecs else DefaultJsonCodecs.encoder,
                          skipkeys=skipkeys,
                          ensure_ascii=ensure_ascii,
                          check_circular=check_circular,
                          allow_nan=allow_nan,
                          indent=indent,
                          separators=separators,
                          default=default,
                          sort_keys=sort_keys,
                          **kw)

    @classmethod
    def from_json(cls: Type[A],
                  s: JsonData,
                  *,
                  parse_float=None,
                  parse_int=None,
                  parse_constant=None,
                  infer_missing=False,
                  codecs: Optional[Codecs] = None,
                  **kw) -> A:
        kvs = json.loads(s,
                         parse_float=parse_float,
                         parse_int=parse_int,
                         parse_constant=parse_constant,
                         **kw)
        return cls.from_dict(kvs, infer_missing=infer_missing, codecs=codecs)

    @classmethod
    def from_dict(cls: Type[A],
                  kvs: Json,
                  *,
                  infer_missing=False,
                  codecs: Optional[Codecs] = None) -> A:
        return _decode_dataclass(
            cls, kvs, infer_missing=infer_missing, codecs=codecs or DefaultJsonCodecs
        )

    def to_dict(self, encode_json=False, codecs: Optional[Codecs] = None) -> Dict[str, Json]:
        return _asdict(self, encode_json=encode_json, codecs=codecs or DefaultJsonCodecs)

    @classmethod
    def schema(cls: Type[A],
               *,
               infer_missing: bool = False,
               only=None,
               exclude=(),
               many: bool = False,
               context=None,
               load_only=(),
               dump_only=(),
               partial: bool = False,
               unknown=None) -> SchemaType:
        Schema = build_schema(cls, DataClassJsonMixin, infer_missing, partial)

        if unknown is None:
            undefined_parameter_action = _undefined_parameter_action_safe(cls)
            if undefined_parameter_action is not None:
                # We can just make use of the same-named mm keywords
                unknown = undefined_parameter_action.name.lower()

        return Schema(only=only,
                      exclude=exclude,
                      many=many,
                      context=context,
                      load_only=load_only,
                      dump_only=dump_only,
                      partial=partial,
                      unknown=unknown)


def dataclass_json(_cls=None, *, letter_case=None,
                   undefined: Optional[Union[str, Undefined]] = None):
    """
    Based on the code in the `dataclasses` module to handle optional-parens
    decorators. See example below:

    @dataclass_json
    @dataclass_json(letter_case=LetterCase.CAMEL)
    class Example:
        ...
    """

    def wrap(cls):
        return _process_class(cls, letter_case, undefined)

    if _cls is None:
        return wrap
    return wrap(_cls)


def _process_class(cls, letter_case, undefined):
    if letter_case is not None or undefined is not None:
        cls.dataclass_json_config = config(letter_case=letter_case,
                                           undefined=undefined)[
            'dataclasses_json']

    cls.to_json = DataClassJsonMixin.to_json
    # unwrap and rewrap classmethod to tag it to cls rather than the literal
    # DataClassJsonMixin ABC
    cls.from_json = classmethod(DataClassJsonMixin.from_json.__func__)
    cls.to_dict = DataClassJsonMixin.to_dict
    cls.from_dict = classmethod(DataClassJsonMixin.from_dict.__func__)
    cls.schema = classmethod(DataClassJsonMixin.schema.__func__)

    cls.__init__ = _handle_undefined_parameters_safe(cls, kvs=(), usage="init")
    # register cls as a virtual subclass of DataClassJsonMixin
    DataClassJsonMixin.register(cls)
    return cls
