from datetime import time

class Availability:
    def __init__(
        self,
        availability_id: str,
        provider_id: str,
        day_of_week: int,  # 0 = Monday, 6 = Sunday
        start_time: time,
        end_time: time,
        is_recurring: bool = True,
    ):
        if not 0 <= day_of_week <= 6:
            raise ValueError("day_of_week must be between 0 (Mon) and 6 (Sun)")

        self.availability_id = availability_id
        self.provider_id = provider_id
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time
        self.is_recurring = is_recurring
