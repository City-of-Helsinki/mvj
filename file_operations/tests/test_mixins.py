from unittest.mock import MagicMock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict
from rest_framework.exceptions import ValidationError

from file_operations.viewsets.mixins import MAX_FILE_SIZE_BYTES, FileExtensionFileMixin


@pytest.fixture
def mixin():
    return FileExtensionFileMixin()


def test_get_allowed_extensions(mixin):
    allowed_extensions = mixin.get_allowed_extensions()
    document_types = [
        "pdf",
        "csv",
        "txt",
        # Word
        "doc",
        "docx",
        "xls",
        "xlsx",
        "ppt",
        "pptx",
        # OpenOffice/LibreOffice
        "odt",
        "fodt",
        "ods",
        "fods",
    ]
    image_types = [
        "jpg",
        "jpeg",
        "jxl",
        "png",
        "gif",
        "tiff",
        "bmp",
        "svg",
        "webp",
    ]
    expected_extensions = document_types + image_types
    # If you make changes to the list of allowed extensions,
    # make sure you update those also in the front-end.
    assert (
        allowed_extensions == expected_extensions
    ), "list of allowed extensions has diverged"


def test_validate_file_extensions_valid(mixin):
    files = MultiValueDict(
        # Might not be valid to have multiple files, but testing it to be sure
        {
            "file1": [
                SimpleUploadedFile(
                    "test.pdf", b"file_content", content_type="application/pdf"
                )
            ],
            "file2": [
                SimpleUploadedFile(
                    "diary.txt", b"file_content", content_type="text/plain"
                )
            ],
        }
    )
    try:
        mixin._validate_file_extensions(files)
    except ValidationError:
        pytest.fail("_validate_file_extensions() raised ValidationError unexpectedly!")


def test_validate_file_extensions_no_extension(mixin):
    files = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test", b"file_content", content_type="application/pdf"
                )
            ]
        }
    )
    with pytest.raises(ValidationError):
        mixin._validate_file_extensions(files)


def test_validate_file_extensions_multiple_dots(mixin):
    files = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.exe.pdf", b"file_content", content_type="application/pdf"
                )
            ]
        }
    )
    try:
        mixin._validate_file_extensions(files)
    except ValidationError:
        pytest.fail("_validate_file_extensions() raised ValidationError unexpectedly!")


def test_validate_file_extensions_invalid_extension(mixin):
    files = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.exe", b"file_content", content_type="application/octet-stream"
                )
            ]
        }
    )
    with pytest.raises(ValidationError):
        mixin._validate_file_extensions(files)


def test_validate_file_extensions_valid_and_invalid_extensions(mixin):
    files = MultiValueDict(
        # Might not be valid to have multiple files, but testing it to be sure
        {
            "file1": [
                SimpleUploadedFile(
                    "test.pdf", b"file_content", content_type="application/pdf"
                )
            ],
            "file2": [
                SimpleUploadedFile(
                    "test.exe", b"file_content", content_type="application/octet-stream"
                )
            ],
        }
    )
    with pytest.raises(ValidationError):
        mixin._validate_file_extensions(files)


def test_file_extension_mixin_create_with_valid_files(mixin):
    request = MagicMock()
    request.FILES = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.pdf", b"file_content", content_type="application/pdf"
                )
            ]
        }
    )
    mixin.create = MagicMock(return_value="created")
    response = mixin.create(request)
    mixin.create.assert_called_once_with(request)
    assert response == "created"


def test_file_extension_mixin_create_with_invalid_files(mixin):
    request = MagicMock()
    request.FILES = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.exe", b"file_content", content_type="application/octet-stream"
                )
            ]
        }
    )
    with pytest.raises(ValidationError):
        mixin.create(request)


def test_file_extension_mixin_update_with_valid_files(mixin):
    request = MagicMock()
    request.FILES = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.pdf", b"file_content", content_type="application/pdf"
                )
            ]
        }
    )
    mixin.update = MagicMock(return_value="updated")
    response = mixin.update(request)
    mixin.update.assert_called_once_with(request)
    assert response == "updated"


def test_file_extension_mixin_update_with_invalid_files(mixin):
    request = MagicMock()
    request.FILES = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.exe", b"file_content", content_type="application/octet-stream"
                )
            ]
        }
    )
    with pytest.raises(ValidationError):
        mixin.update(request)


def test_validate_file_size_valid(mixin):
    bytes_under_max = b"a" * (MAX_FILE_SIZE_BYTES - 1)
    files = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.pdf",
                    bytes_under_max,
                    content_type="application/pdf",
                )
            ]
        }
    )
    try:
        mixin._validate_file_size(files)
    except ValidationError:
        pytest.fail("_validate_file_size() raised ValidationError unexpectedly!")


def test_validate_file_size_exceeds_limit(mixin):
    bytes_over_max = b"a" * (MAX_FILE_SIZE_BYTES + 1)
    files = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.pdf",
                    bytes_over_max,
                    content_type="application/pdf",
                )
            ]
        }
    )
    with pytest.raises(ValidationError):
        mixin._validate_file_size(files)


def test_file_extension_mixin_create_with_valid_file_size(mixin):
    bytes_under_max = b"a" * (MAX_FILE_SIZE_BYTES - 1)
    request = MagicMock()
    request.FILES = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.pdf",
                    bytes_under_max,
                    content_type="application/pdf",
                )
            ]
        }
    )
    mixin.create = MagicMock(return_value="created")
    response = mixin.create(request)
    mixin.create.assert_called_once_with(request)
    assert response == "created"


def test_file_extension_mixin_create_with_too_large_file_size(mixin):
    bytes_over_max = b"a" * (MAX_FILE_SIZE_BYTES + 1)
    request = MagicMock()
    request.FILES = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.pdf",
                    bytes_over_max,
                    content_type="application/pdf",
                )
            ]
        }
    )
    with pytest.raises(ValidationError):
        mixin.create(request)


def test_file_extension_mixin_update_with_valid_file_size(mixin):
    bytes_under_max = b"a" * (MAX_FILE_SIZE_BYTES - 1)
    request = MagicMock()
    request.FILES = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.pdf",
                    bytes_under_max,
                    content_type="application/pdf",
                )
            ]
        }
    )
    mixin.update = MagicMock(return_value="updated")
    response = mixin.update(request)
    mixin.update.assert_called_once_with(request)
    assert response == "updated"


def test_file_extension_mixin_update_with_invalid_file_size(mixin):
    bytes_over_max = b"a" * (MAX_FILE_SIZE_BYTES + 1)
    request = MagicMock()
    request.FILES = MultiValueDict(
        {
            "file": [
                SimpleUploadedFile(
                    "test.pdf",
                    bytes_over_max,
                    content_type="application/pdf",
                )
            ]
        }
    )
    with pytest.raises(ValidationError):
        mixin.update(request)
