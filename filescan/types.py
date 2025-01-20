from typing import Protocol, TypedDict

from django.db import models


# TODO different protocols to cover models with different filepath column names?
class FileModelProtocol(Protocol):
    """
    Protocol to represent models with the column `attachment` that holds the
    filepath to the physical file.
    """

    @property
    def id(self) -> int:  # noqa: E701
        ...

    @property
    def attachment(self) -> models.FileField:  # noqa: E701
        ...


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
