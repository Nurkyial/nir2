from django.forms import ModelForm
from.models import UserProfile
from django import forms

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        group = cleaned_data.get('group')
        
        if role and role.name != 'student' and group:
            raise forms.ValidationError('Only students can be assigned to a group!!!')
        return cleaned_data