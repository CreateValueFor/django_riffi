from django import forms

class ExtractFileForm(forms.Form):
    file = forms.FileField()
    output_types = forms.CharField(max_length=255)