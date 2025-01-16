from typing import TypedDict


class PlattaClamAvResult(TypedDict):
    name: str
    is_infected: bool
    viruses: list[str]


class PlattaClamAvData(TypedDict):
    result: list[PlattaClamAvResult]


class PlattaClamAvResponse(TypedDict):
    """JSON response structure from Platta's ClamAV API."""

    success: bool
    data: PlattaClamAvData
