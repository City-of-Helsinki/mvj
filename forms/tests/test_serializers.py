import pytest

from ..serializers.form import AnswerSerializer, FormSerializer


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
