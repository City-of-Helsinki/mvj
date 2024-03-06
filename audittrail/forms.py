from django import forms


class AuditTrailSearchForm(forms.Form):
    type = forms.ChoiceField(
        label="Type",
        required=True,
        choices=(("lease", "Lease"), ("contact", "Contact"), ("areasearch", "AreaSearch")),
    )
    id = forms.IntegerField(label="Id", required=True)
