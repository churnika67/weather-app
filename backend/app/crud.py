import json
from sqlalchemy.orm import Session
from . import models


def create_record(
    db: Session,
    location_input: str,
    resolved_location: str,
    latitude: float,
    longitude: float,
    start_date,
    end_date,
    weather_data,
):
    item = models.WeatherRecord(
        location_input=location_input,
        resolved_location=resolved_location,
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        weather_data=json.dumps(weather_data),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_records(db: Session):
    return db.query(models.WeatherRecord).order_by(models.WeatherRecord.created_at.desc()).all()


def get_record(db: Session, record_id: int):
    return db.query(models.WeatherRecord).filter(models.WeatherRecord.id == record_id).first()


def update_record(
    db: Session,
    record,
    location_input: str,
    resolved_location: str,
    latitude: float,
    longitude: float,
    start_date,
    end_date,
    weather_data,
):
    record.location_input = location_input
    record.resolved_location = resolved_location
    record.latitude = latitude
    record.longitude = longitude
    record.start_date = start_date
    record.end_date = end_date
    record.weather_data = json.dumps(weather_data)

    db.commit()
    db.refresh(record)
    return record


def delete_record(db: Session, record):
    db.delete(record)
    db.commit()
