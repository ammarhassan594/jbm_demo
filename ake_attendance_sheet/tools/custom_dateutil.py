from datetime import datetime
from dateutil import tz


def convert_to_timezone(from_tz: str, to_tz: str, convert_date: str) -> datetime:
    """Convert a datetime object from one timezone to another.

    :param from_tz: The timezone of the original datetime object, in tz database format (e.g. 'America/New_York').
    :type from_tz: str
    :param to_tz: The timezone to convert the datetime object to, in tz database format.
    :type to_tz: str
    :param convert_date: The datetime object to convert, in the format '%Y-%m-%d %H:%M:%S'.
    :type convert_date: str
    :return: The datetime object converted to the new timezone.
    :rtype: datetime.datetime
    """
    from_zone = tz.gettz(from_tz)
    to_zone = tz.gettz(to_tz)
    date_time = datetime.strptime(str(convert_date), '%Y-%m-%d %H:%M:%S').replace(tzinfo=from_zone)
    return date_time.astimezone(to_zone)


def time_to_float(time_obj):
    """Converts a time object to a float representing the time as a fraction of a day."""
    return time_obj.hour + time_obj.minute / 60
