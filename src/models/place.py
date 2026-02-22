from __future__ import annotations

from pydantic import BaseModel
from typing import Literal

PlaceType = Literal["toilet", "pharmacy", "wifi", "aed", "tourist_info"]


class BilingualName(BaseModel):
    ko: str
    en: str


class Location(BaseModel):
    lat: float
    lng: float
    address_ko: str
    address_en: str
    district: str
    nearest_station: str | None = None


class Hours(BaseModel):
    open: str = "00:00"
    close: str = "24:00"
    is_24h: bool = False
    closed_days: list[str] = []


class Accessibility(BaseModel):
    wheelchair: bool = False
    elevator_nearby: bool = False


class Place(BaseModel):
    id: str
    type: PlaceType
    name: BilingualName
    location: Location
    services: dict = {}
    hours: Hours = Hours()
    accessibility: Accessibility = Accessibility()
    trust_score: float = 0.9
    data_source: str = "data.go.kr"
    last_verified: str = "2026-02-22"
