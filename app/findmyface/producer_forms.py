from django import forms


class EventCreationForm(forms.Form):
    event_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Wedding of John and Jane'
        })
    )

    event_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date'
        })
    )

    event_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Describe the event...'
        })
    )