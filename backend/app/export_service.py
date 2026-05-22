import csv
import io
import json


def records_to_json(records):
    result = []
    for record in records:
        result.append(
            {
                "id": record.id,
                "location_input": record.location_input,
                "resolved_location": record.resolved_location,
                "latitude": record.latitude,
                "longitude": record.longitude,
                "start_date": record.start_date.isoformat(),
                "end_date": record.end_date.isoformat(),
                "weather_data": json.loads(record.weather_data),
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
            }
        )
    return result


def records_to_csv(records):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "location_input",
            "resolved_location",
            "latitude",
            "longitude",
            "start_date",
            "end_date",
            "weather_data",
            "created_at",
            "updated_at",
        ]
    )

    for record in records:
        writer.writerow(
            [
                record.id,
                record.location_input,
                record.resolved_location,
                record.latitude,
                record.longitude,
                record.start_date.isoformat(),
                record.end_date.isoformat(),
                record.weather_data,
                record.created_at.isoformat(),
                record.updated_at.isoformat(),
            ]
        )

    return output.getvalue()
