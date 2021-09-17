import pytest

from ..serializers.form import AnswerSerializer, EntrySerializer, FormSerializer


def find(key, dictionary):
    for k, v in dictionary.iteritems():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in find(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in find(key, d):
                    yield result


@pytest.mark.django_db
def test_form_serializer(basic_template_form):
    serializer = FormSerializer(basic_template_form, read_only=True)
    assert serializer.data["sections"]
    assert find("fields", serializer.data)
    assert find("choices", serializer.data)


@pytest.mark.django_db
def test_answer_serializer(basic_answer):
    serializer = AnswerSerializer(basic_answer)
    assert serializer.data["form"]
    assert serializer.data["entries"]


@pytest.mark.django_db
def test_entry_validators(basic_answer):
    serializer = AnswerSerializer(basic_answer)
    entries = serializer.data["entries"]
    for entry in entries:
        # Check that all entries are unique
        assert entries.count(entry) == 1

    not_unique_entry = {
        "answer": basic_answer,
        "field": basic_answer.entries.first().field,
        "value": basic_answer.entries.first().value,
    }

    serializer = EntrySerializer(data=not_unique_entry)
    assert not serializer.is_valid()
