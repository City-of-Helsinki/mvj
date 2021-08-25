from pathlib import Path

from django.db import migrations


class RunSQLFromFile(migrations.RunSQL):
    def __init__(self, sql_file, reverse_sql_file=None, **kwargs):
        super().__init__(sql="", **kwargs)
        self.sql_file = sql_file
        self.reverse_sql_file = reverse_sql_file
        self._sql = "unread"
        self._reverse_sql = "unread"

    @property
    def sql(self):
        if self._sql == "unread":
            self._sql = self._read_file(self.sql_file)
        return self._sql

    @sql.setter
    def sql(self, value):
        pass

    @property
    def reverse_sql(self):
        if self._reverse_sql == "unread":
            self._reverse_sql = self._read_file(self.reverse_sql_file)
        return self._reverse_sql

    @reverse_sql.setter
    def reverse_sql(self, value):
        pass

    def _read_file(self, filename):
        if filename is None:
            return None
        with open(Path(__file__).parent / filename) as fp:
            return fp.read()


class Migration(migrations.Migration):
    dependencies = [
        ("batchrun", "0010_entry_data_to_text_json"),
    ]

    operations = [
        RunSQLFromFile(
            sql_file="./0011_log_compact_function.sql",
            reverse_sql_file="./0011_drop_log_compact_function.sql",
        ),
    ]
