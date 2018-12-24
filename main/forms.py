from django import forms

class FilterForm(forms.Form):
    tag = forms.CharField(label='Etiquetas', required=False, max_length=100,
    widget = forms.TextInput(
            attrs = {'class': 'form-control'}
        ))