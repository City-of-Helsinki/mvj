from django.utils.translation import ugettext_lazy as _
from enumfields import Enum, IntEnum


class CommandType(Enum):
    EXECUTABLE = "executable"
    DJANGO_MANAGE = "django-manage"

    class Labels:
        EXECUTABLE = _("executable or script")
        DJANGO_MANAGE = _("Django management command")


class LogEntryKind(IntEnum):
    STDOUT = 1
    STDERR = 2

    class Labels:
        # Labels of stdout and stderr are not translated, because it
        # breaks the filtering in Django Admin
        STDOUT = "stdout"
        STDERR = "stderr"
