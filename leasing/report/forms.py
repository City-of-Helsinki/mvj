from django import forms


class ReportFormBase(forms.Form):
    def __init__(self, *args, **kwargs):
        input_fields = kwargs.pop('input_fields')
        super().__init__(*args, **kwargs)

        for field_name, field in input_fields.items():
            self.fields[field_name] = field
