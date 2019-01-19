from django import forms

class FilterForm(forms.Form):
    tag = forms.CharField(label='Etiquetas', required=False, max_length=100, initial="trump",
    widget = forms.TextInput(
            attrs = {'class': 'form-control'}
        ))
    pagination = forms.ChoiceField(label='Número de tuits', widget=forms.Select(attrs={'class': 'form-control'}), choices=[(10, 10), (20, 20), (50, 50)])


class AccountForm(forms.Form):
    screen_name = forms.CharField(label='Usuario', required=False, max_length=100,
    widget = forms.TextInput(
            attrs = {'class': 'form-control'}
    ))
    depth = forms.IntegerField(label='Nivel de profundidad', required=False, min_value=1, initial=1,
    widget = forms.TextInput(
            attrs = {'class': 'form-control'}
    ))