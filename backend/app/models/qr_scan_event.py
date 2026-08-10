from dataclasses import dataclass
from datetime import datetime
from typing import Literal


DeviceType = Literal["desktop", "mobile", "tablet", "bot", "unknown"]


@dataclass(frozen=True, slots=True)
class QrScanEvent:
    id: str
    generation_id: str
    user_id: str
    visitor_hash: str
    device_type: DeviceType
    browser: str
    operating_system: str
    country: str
    city: str
    scanned_at: datetime
