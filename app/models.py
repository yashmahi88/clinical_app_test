import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _validate_time(value: str) -> str:
    if not TIME_RE.match(value):
        raise ValueError("must be HH:MM in 24-hour format")
    return value


class DoctorIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    specialization: str = Field(min_length=1, max_length=120)


class Doctor(DoctorIn):
    id: int


class PatientIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str = Field(min_length=5, max_length=30, pattern=r"^[0-9+\-() ]+$")


class Patient(PatientIn):
    id: int


class AvailabilityIn(BaseModel):
    doctor_id: int
    weekday: int = Field(ge=0, le=6, description="0 = Monday, 6 = Sunday")
    start_time: str
    end_time: str

    _check_start = field_validator("start_time")(_validate_time)
    _check_end = field_validator("end_time")(_validate_time)

    @field_validator("end_time")
    def end_after_start(cls, v: str, info) -> str:
        start = info.data.get("start_time")
        if start and TIME_RE.match(start) and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class Availability(AvailabilityIn):
    id: int


class AppointmentIn(BaseModel):
    doctor_id: int
    patient_id: int
    start: datetime
    end: datetime

    @field_validator("end")
    def end_after_start(cls, v: datetime, info) -> datetime:
        start = info.data.get("start")
        if start and v <= start:
            raise ValueError("end must be after start")
        return v


class Appointment(AppointmentIn):
    id: int
    status: str = "booked"


class RescheduleIn(BaseModel):
    start: datetime
    end: datetime

    @field_validator("end")
    def end_after_start(cls, v: datetime, info) -> datetime:
        start = info.data.get("start")
        if start and v <= start:
            raise ValueError("end must be after start")
        return v
