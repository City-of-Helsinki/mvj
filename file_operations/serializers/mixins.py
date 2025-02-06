import os

from django.urls import reverse


class FileSerializerMixin:
    def get_file_url(self, obj):
        if not obj or not obj.file:
            return None

        request = self.context.get("request", None)
        version_namespace = getattr(request, "version", "v1")
        url_name = self.Meta.download_url_name
        url = reverse(
            f"{version_namespace}:{url_name}",
            args=[obj.id],
        )

        if request is not None:
            return request.build_absolute_uri(url)

        return url

    def get_file_filename(self, obj):
        return os.path.basename(obj.file.name)
