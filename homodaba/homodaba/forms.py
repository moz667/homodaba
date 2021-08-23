from django import forms

class AddTagForm(forms.Form):
    movie_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    tag = forms.CharField(
        label='Etiqueta', required=True, 
        help_text='Etiqueta nueva o existente.'
    )
