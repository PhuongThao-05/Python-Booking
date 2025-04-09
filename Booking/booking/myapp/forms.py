import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from .models import account, users

class RegisterForm(forms.ModelForm):
    class Meta:
        model = account
        fields = ['email', 'password', 'idrole']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email không được để trống.")
        try:
            EmailValidator()(email)  # Kiểm tra email hợp lệ
        except ValidationError:
            raise ValidationError("Email không hợp lệ.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        # Kiểm tra độ dài mật khẩu
        if not re.fullmatch(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[\W_]).{6,}$', password):
            raise ValidationError(
                "Mật khẩu phải có ít nhất 6 ký tự, bao gồm chữ cái, chữ số và ký tự đặc biệt."
            )
        return password

    def clean_idrole(self):
        idrole = self.cleaned_data.get('idrole')
        # Kiểm tra nếu người dùng không chọn idrole
        if not idrole:
            raise ValidationError("Vui lòng chọn một vai trò.")
        return idrole

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        idrole = cleaned_data.get('idrole')
        # Thực hiện các kiểm tra bổ sung tại đây nếu cần
        return cleaned_data
    
class UserInfoForm(forms.ModelForm):
    class Meta:
        model = users
        fields = ['email', 'name', 'phonenumber']
    def __init__(self, *args, **kwargs):
        initial_email = kwargs.pop('initial_email', None)
        super().__init__(*args, **kwargs)
        if initial_email:
            self.fields['email'].initial = initial_email
            self.fields['email'].disabled = True 

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise ValidationError("Vui lòng nhập tên của bạn.")
        return name
    def clean_phonenumber(self):
        phonenumber = self.cleaned_data.get('phonenumber')
        if not re.fullmatch(r'0\d{9}', phonenumber):
            raise ValidationError("Vui lòng nhập đúng số điện thoại.")
        return phonenumber
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        name = cleaned_data.get('name')
        phonenumber = cleaned_data.get('phonenumber')

        return cleaned_data