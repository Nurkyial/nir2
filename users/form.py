from django.forms import ModelForm
from.models import UserProfile
from base.models import Submission, File, Assignment
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field

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

class UploadFileForm(ModelForm):
    class Meta:
        model = File
        fields = ('filename',)
        
    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Div(
                Field('filename', css_class='form-control', id='formFile'),
                css_class='mb-3'
            ),
            Submit('submit', 'Отправить', css_class='btn btn-secondary')
        )
        
        
class ChooseTeacherForm(ModelForm):
    class Meta:
        model = Assignment
        fields = ['student', 'teacher', 'text']
        
    def __init__(self, *args, **kwargs):
        super(UploadFileForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.add_input(Submit('submit', 'Submit', css_class='btn btn-secondary'))
        self.helper.label_class = 'form-label'
        self.helper.field_class = 'form-control'
        