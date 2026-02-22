from __future__ import annotations

from pydantic import BaseModel


class BilingualName(BaseModel):
    ko: str
    en: str


class TrainEntry(BaseModel):
    time: str
    destination: str
    type: str = "normal"


class DirectionTimetable(BaseModel):
    up: list[TrainEntry] = []
    down: list[TrainEntry] = []


class Timetable(BaseModel):
    weekday: DirectionTimetable = DirectionTimetable()
    saturday: DirectionTimetable = DirectionTimetable()
    holiday: DirectionTimetable = DirectionTimetable()


class SubwayStation(BaseModel):
    station_id: str
    station_name: BilingualName
    line: str
    line_name: BilingualName
    timetable: Timetable
    transfer_lines: list[str] = []
    data_source: str = "data.seoul.go.kr"
    last_verified: str = "2026-02-22"
