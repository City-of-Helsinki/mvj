from django import forms


class ReportFormBase(forms.Form):
    """Dynamic form that initializes its fields from `input_fields` parameter"""

    def __init__(self, *args, **kwargs):
        """
        args is expected to contain the query parameters, which in turn contains
        the report settings when the report was requested.

        kwargs is expected to contain a key "input_fields", whose value is a
        dictionary containing the names of the query parameters and the form
        field objects they reference.
        """
        input_fields: dict[str, forms.Field] = kwargs.pop("input_fields")
        super().__init__(*args, **kwargs)

        for field_name, field in input_fields.items():
            self.fields[field_name] = field
