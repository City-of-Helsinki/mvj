import json

import pytest

from leasing.enums import ApplicationState
from leasing.serializers import ApplicationSerializer


@pytest.mark.django_db
def test_create_application():
    data = """{
    "type": "detached_house",
    "building_footprints": [
        {
            "use": "use1",
            "area": "11"
        },
        {
            "use": "use2"
        },
        {
            "area": "33"
        }
    ],
    "notes": [
        {
            "title": "Test note",
            "text": "Note test"
        }
    ]
}"""

    serializer = ApplicationSerializer(data=json.loads(data))

    assert serializer.is_valid(raise_exception=True)
    instance = serializer.save()

    assert instance.id
    assert instance.state == ApplicationState.UNHANDLED
    assert len(instance.building_footprints.all()) == 3
    assert len(instance.notes.all()) == 1
