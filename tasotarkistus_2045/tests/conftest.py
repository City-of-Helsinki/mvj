# Import factories from another app, to allow their usage in this app's tests
from leasing.tests.conftest import (
    IndexPointFigureYearlyFactory,
    OldDwellingsInHousingCompaniesPriceIndexFactory,
    RentFactory,
)
