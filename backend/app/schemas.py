from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator


class WeatherBaseRequest(BaseModel):
    location: str = Field(..., min_length=1, max_length=255)

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Location cannot be empty")
        return cleaned


class WeatherRecordCreate(WeatherBaseRequest):
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end_date: date, info):
        start_date = info.data.get("start_date")
        if start_date and start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        return end_date


class WeatherRecordUpdate(BaseModel):
    location: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Location cannot be empty")
        return cleaned

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, end_date: date, info):
        start_date = info.data.get("start_date")
        if start_date and start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        return end_date


class WeatherRecordResponse(BaseModel):
    id: int
    location_input: str
    resolved_location: str
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    weather_data: Any
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WeatherCurrentResponse(BaseModel):
    location_input: str
    resolved_location: str
    latitude: float
    longitude: float
    current_weather: dict[str, Any]


class WeatherForecastResponse(BaseModel):
    location_input: str
    resolved_location: str
    latitude: float
    longitude: float
    forecast: dict[str, Any]
