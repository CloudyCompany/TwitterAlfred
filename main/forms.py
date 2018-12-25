from django import forms

class FilterForm(forms.Form):
    tag = forms.CharField(label='Etiquetas', required=False, max_length=100,
    widget = forms.TextInput(
            attrs = {'class': 'form-control'}
        ))
    pagination = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}), choices=[(10, 10), (20, 20), (50, 50)])