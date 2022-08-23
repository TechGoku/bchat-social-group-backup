from ..web import app
from ..model.room import Room
from ..model.exc import NoSuchRoom

from .. import config

from werkzeug.routing import BaseConverter, ValidationError


class RoomTokenConverter(BaseConverter):
    """
    A room token name consisting of `a`-`z`, `A`-`Z`, `0`-`9`, `_`, and `-` characters.
    Max length 64.
    """

    regex = r"[\w-]{1,64}"

    def to_python(self, value):
        try:
            return Room(token=value)
        except NoSuchRoom:
            raise ValidationError()

    def to_value(self, value):
        return value.token


class AnySessionIDConverter(BaseConverter):
    """
    A 66-hex-character bchat ID (`05...`) or blinded bchat ID (`15...`).
    """

    regex = r"bd[0-9a-fA-F]{64}"

    def to_python(self, value):
        return value


class BlindSessionIDConverter(BaseConverter):
    """
    A 66-hex-character blinded bchat ID (`bd...`).  Non-blinded bchat IDs are not permitted.
    """

    regex = r"bd[0-9a-fA-F]{64}"

    def to_python(self, value):
        return value


class UnblindedSessionIDConverter(BaseConverter):
    """
    A 66-hex character unblinded bchat ID (`bd...`).  *Blinded* Bchat IDs are not permitted.
    """

    regex = r"bd[0-9a-fA-F]{64}"

    def to_python(self, value):
        return value


app.url_map.converters['Room'] = RoomTokenConverter
app.url_map.converters['BlindSessionID'] = BlindSessionIDConverter
app.url_map.converters['UnblindedSessionID'] = UnblindedSessionIDConverter
app.url_map.converters['SessionID'] = (
    BlindSessionIDConverter if config.REQUIRE_BLIND_KEYS else AnySessionIDConverter
)
