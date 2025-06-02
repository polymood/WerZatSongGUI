import time
from datetime import datetime

def generate_unique():
    """
    Generate a timestamp-based unique string in the format:
    YYYY-MM-DD_HH-MM-SS
    """
    # Use UTC ISO format, replace 'T' with '_', strip off fractional seconds, replace ':' with '-'
    return datetime.now().isoformat().replace('T', '_').split('.')[0].replace(':', '-')

def sleep(seconds):
    """
    Pause execution for the given number of seconds (blocking).
    """
    time.sleep(seconds)

def trim_extension(filename):
    """
    Remove the file extension from a filename string.
    If there is no extension, returns an empty string.
    """
    parts = filename.split('.')
    return '.'.join(parts[:-1])