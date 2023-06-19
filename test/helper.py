from datetime import datetime, timezone


def grist_date(y, m, d, tz=timezone.utc):
    """
    Returns a representation of a date returned by the Grist API. It's a
    timestamp with type int. It represents midnight UTC for that date.
    """
    return int(
        datetime(
            y, m, d,
            0, 0, 0,
            tzinfo=timezone.utc
        ).timestamp()
    )
