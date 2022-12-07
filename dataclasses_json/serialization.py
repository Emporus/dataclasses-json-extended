import sys
from datetime import datetime
from datetime import timezone
from decimal import Decimal
from enum import Enum
from json import JSONEncoder
from typing import Collection
from typing import Dict
from typing import Mapping
from typing import Optional
from typing import Type
from uuid import UUID

from dataclasses_json.custom_types import *
from dataclasses_json.utils import _isinstance_safe
from dataclasses_json.utils import optional

__all__ = ["Codecs", "DefaultJsonCodecs"]


class Codecs:
    def __init__(
        self,
        encoders: Optional[Dict[Union[type, str], Callable]] = None,
        decoders: Optional[Dict[Union[type, str], Callable]] = None,
        mm_fields: Optional[Dict[Union[type, str], Callable]] = None,
    ) -> None:
        self.encoders: Dict[Union[type, str], Callable] = dict(encoders or dict())
        self.decoders: Dict[Union[type, str], Callable] = dict(decoders or dict())
        self.mm_fields: Dict[Union[type, str], Callable] = dict(mm_fields or dict())

        embed = self  # Get self reference to embed on custom JSONEncoder

        class EncoderForMarshmallow(JSONEncoder):
            codecs = embed  # Embed Codecs instance into EncoderForMarshmallow

            def __init__(
                self,
                *,
                skipkeys=False,
                ensure_ascii=True,
                check_circular=True,
                allow_nan=True,
                sort_keys=False,
                indent=None,
                separators=None,
                default=None,
                codecs: Optional["Codecs"] = None,
            ) -> None:
                super().__init__(
                    skipkeys=skipkeys,
                    ensure_ascii=ensure_ascii,
                    check_circular=check_circular,
                    allow_nan=allow_nan,
                    sort_keys=sort_keys,
                    indent=indent,
                    separators=separators,
                    default=default,
                )
                self.codecs = codecs

            def default(self, o) -> Json:
                result: Json
                coders: Dict[Union[type, str], Callable[Any, Json]] = self.__class__.codecs.encoders
                if _isinstance_safe(o, Collection):
                    if _isinstance_safe(o, Mapping):
                        result = dict(o)
                    else:
                        result = list(o)
                elif _isinstance_safe(o, Enum):
                    result = o.value
                elif type(o) in coders:  # If type recognized on injected codecs, use its encoder
                    result = coders[type(o)](o)
                else:
                    return super().default(o)
                return result

        self.encoder = EncoderForMarshmallow

    def set_json(self, kind: Union[Type, str], enc: Convert[A, B], dec: Convert[B, A]) -> None:
        self.encoders[kind] = enc
        self.decoders[kind] = dec
        self.encoders[Optional[kind]] = optional(enc)
        self.decoders[Optional[kind]] = optional(dec)

        if isinstance(kind, str):
            return

        if sys.version_info[1] == 8:
            if kind.__class__.__name__ in ("_GenericAlias",):
                string = str(kind)
            else:
                string = kind.__name__
        elif sys.version_info[1] == 9:
            if kind.__class__.__name__ in ("_UnionGenericAlias", "_GenericAlias"):
                string = str(kind)
            else:
                string = kind.__name__
        else:
            string = str(kind)
            self.encoders[kind.__name__] = enc
            self.decoders[kind.__name__] = dec

        self.encoders[string] = enc
        self.decoders[string] = dec

    def set_mm(self, kind: Union[Type, str], mm_field: Callable[[A], B]) -> None:
        self.mm_fields[kind] = mm_field

        if isinstance(kind, str):
            return

        if sys.version_info[1] == 8:
            if kind.__class__.__name__ in ("_GenericAlias",):
                string = str(kind)
            else:
                string = kind.__name__
        elif sys.version_info[1] == 9:
            if kind.__class__.__name__ in ("_UnionGenericAlias", "_GenericAlias"):
                string = str(kind)
            else:
                string = kind.__name__
        else:
            string = str(kind)
            self.mm_fields[kind.__name__] = mm_field

        self.mm_fields[string] = mm_field


DefaultJsonCodecs = Codecs()

DefaultJsonCodecs.set_json(UUID, lambda it: str(it), lambda it: UUID(it))
DefaultJsonCodecs.set_json(
    datetime, lambda it: it.timestamp(), lambda it: datetime.fromtimestamp(it, tz=timezone.utc)
)
DefaultJsonCodecs.set_json(Decimal, lambda it: str(it), lambda it: Decimal(str(it)))

# Support python Arrow if installed
try:
    import arrow

    DefaultJsonCodecs.set_json(arrow.Arrow, lambda it: it.int_timestamp, lambda it: arrow.get(it))

except ImportError:
    pass

# Support hyperlink URL if installed
try:
    from hyperlink import URL

    DefaultJsonCodecs.set_json(URL, lambda it: str(it), lambda it: URL.from_text(it))

except ImportError:
    pass

# Support yarl URL if installed
try:
    from yarl import URL

    DefaultJsonCodecs.set_json(URL, lambda it: str(it), lambda it: URL(it))

except ImportError:
    pass
