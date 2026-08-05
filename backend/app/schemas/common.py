from datetime import timedelta
from typing import Annotated

from pydantic import PlainSerializer

# A timedelta serialized as total seconds (a plain number) instead of
# Pydantic's default ISO 8601 duration string ("PT1M35S"). The frontend
# sends/expects durations as seconds everywhere.
SecondsTimedelta = Annotated[
    timedelta,
    PlainSerializer(lambda td: td.total_seconds(), return_type=float, when_used="json"),
]
