from django import forms

from .models import Child, Chore, ChoreAssignment


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'age']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = ['name', 'description', 'points']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ChoreAssignmentForm(forms.ModelForm):
    class Meta:
        model = ChoreAssignment
        fields = ['child', 'chore', 'date_assigned', 'completed', 'date_completed']
        widgets = {
            'date_assigned': forms.DateInput(attrs={'type': 'date'}),
            'date_completed': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        completed = cleaned_data.get('completed')
        date_completed = cleaned_data.get('date_completed')
        date_assigned = cleaned_data.get('date_assigned')

        if completed and not date_completed:
            self.add_error('date_completed', "Date completed is required when the chore is marked as completed.")

        if date_completed and date_assigned and date_completed < date_assigned:
            self.add_error('date_completed', "Date completed cannot be earlier than the date assigned.")

        return cleaned_data
