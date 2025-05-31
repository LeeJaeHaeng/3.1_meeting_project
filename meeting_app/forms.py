 
# meeting_app/forms.py
from django import forms
from .models import Member, Class, Post, Attendance, Interests

class MemberRegistrationForm(forms.ModelForm):
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': '비밀번호를 다시 입력하세요'
        }),
        label='비밀번호 확인'
    )
    
    class Meta:
        model = Member
        fields = ['accountID', 'password', 'accountType', 'name', 'phoneNum', 'email', 'birth']
        widgets = {
            'accountID': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '4-20자의 영문, 숫자 조합'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '8자 이상의 비밀번호'
            }),
            'accountType': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '실명을 입력하세요'
            }),
            'phoneNum': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '010-0000-0000'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': 'example@email.com'
            }),
            'birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-custom'
            }),
        }
        labels = {
            'accountID': '계정ID',
            'password': '비밀번호',
            'accountType': '계정타입',
            'name': '이름',
            'phoneNum': '전화번호',
            'email': '이메일',
            'birth': '생년월일',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password != password_confirm:
            raise forms.ValidationError('비밀번호가 일치하지 않습니다.')
        
        return cleaned_data

class ClassSearchForm(forms.Form):
    keyword = forms.CharField(
        max_length=100,
        required=False,
        label='검색어',
        widget=forms.TextInput(attrs={
            'placeholder': '관심사나 클래스명을 입력하세요',
            'class': 'form-control search-input'
        })
    )
    interest = forms.ModelChoiceField(
        queryset=Interests.objects.all(),
        required=False,
        label='관심사 필터',
        empty_label='전체 카테고리',
        widget=forms.Select(attrs={
            'class': 'form-select search-input'
        })
    )

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '게시글 제목을 입력하세요'
            }),
            'content': forms.Textarea(attrs={
                'rows': 10,
                'class': 'form-control form-control-custom',
                'placeholder': '내용을 입력하세요 (최소 30자)'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
        }
        labels = {
            'title': '제목',
            'content': '내용',
            'category': '카테고리',
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 30:
            raise forms.ValidationError('내용은 최소 30자 이상이어야 합니다.')
        return content

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['attendDate', 'attendanceStatus']
        widgets = {
            'attendDate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-custom'
            }),
            'attendanceStatus': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
        }
        labels = {
            'attendDate': '출석일',
            'attendanceStatus': '출석상태',
        }

class LoginForm(forms.Form):
    accountID = forms.CharField(
        max_length=50,
        label='계정ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': '계정ID를 입력하세요'
        })
    )
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': '비밀번호를 입력하세요'
        })
    )