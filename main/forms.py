from django import forms

from .models import Record


class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ("name", "code", "price", "active", "on_date")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "on_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
        }

    def clean_name(self):
        value = (self.cleaned_data.get("name") or "").strip()
        if not value:
            raise forms.ValidationError("Название обязательно.")
        return value

    def clean_price(self):
        value = self.cleaned_data.get("price")
        if value is not None and value <= 0:
            raise forms.ValidationError("Сумма должна быть больше 0.")
        return value
