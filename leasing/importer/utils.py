from typing import Any

from psycopg.cursor import Cursor


def rows_to_dict_list(cursor: Cursor) -> list[dict[Any, Any]]:
    columns = [i[0] for i in cursor.description]
    return [dict(zip(columns, row)) for row in cursor]
