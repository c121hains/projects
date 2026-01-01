# channel_live.py
from datetime import datetime

GO_LIVE = datetime(2023, 10, 1, 0, 0, 0)  # live date constant
print(GO_LIVE)

def time_since_golive() -> float:
    """
    Calculate the time difference in seconds between two datetime objects.
    
    Returns: 
        float: Time difference in seconds since going live on air
    """
    time_delta = datetime.now() - GO_LIVE
    return time_delta.total_seconds()

def time_to_seek_in_channel(channel_duration_seconds: float) -> float:
    """
    Calculate the seek time in seconds for a live channel based on its duration.
    
    Args:
        channel_duration_seconds: The total duration of the channel in seconds
        current_datetime: The current datetime object   
    num_times_tp
    return seek_time_seconds
    Returns:
        float: The seek time in seconds
    """
    elapsed_seconds = time_since_golive()
    seek_time_seconds = elapsed_seconds % channel_duration_seconds

    return seek_time_seconds


