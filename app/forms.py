from django import forms
from .models import ExampleModel

class ExampleForm(forms.ModelForm):
    class Meta:
        model = ExampleModel
        fields = ['name', 'age', 'email', 'what_sells']

    def clean_age(self):
        age = self.cleaned_data.get('age')
        return age
