# meeting_app/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import date, timedelta
from .models import Member, Class, Post, Attendance, Interests
import re

class MemberRegistrationForm(forms.ModelForm):
    """회원가입 폼 - 강화된 유효성 검사"""
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': '비밀번호를 다시 입력하세요',
            'autocomplete': 'new-password'
        }),
        label='비밀번호 확인',
        help_text='위에서 입력한 비밀번호를 다시 입력하세요.'
    )
    
    agree_terms = forms.BooleanField(
        required=True,
        label='이용약관 및 개인정보처리방침에 동의합니다.',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        error_messages={
            'required': '이용약관에 동의해야 회원가입이 가능합니다.'
        }
    )
    
    class Meta:
        model = Member
        fields = ['accountID', 'password', 'accountType', 'name', 'phoneNum', 'email', 'birth']
        widgets = {
            'accountID': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '4-20자의 영문, 숫자 조합',
                'autocomplete': 'username',
                'pattern': '[a-zA-Z0-9]+',
                'title': '영문과 숫자만 사용할 수 있습니다.'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '8자 이상의 비밀번호',
                'autocomplete': 'new-password',
                'pattern': '.{8,}',
                'title': '8자 이상의 비밀번호를 입력하세요.'
            }),
            'accountType': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '실명을 입력하세요',
                'autocomplete': 'name',
                'pattern': '[가-힣a-zA-Z\s]+',
                'title': '한글 또는 영문만 사용할 수 있습니다.'
            }),
            'phoneNum': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '010-0000-0000',
                'autocomplete': 'tel',
                'pattern': '01[0-9]-[0-9]{4}-[0-9]{4}',
                'title': '010-0000-0000 형식으로 입력하세요.'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': 'example@email.com',
                'autocomplete': 'email'
            }),
            'birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-custom',
                'max': date.today().isoformat(),
                'min': (date.today() - timedelta(days=365*100)).isoformat()  # 100년 전까지
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
        help_texts = {
            'accountID': '4-20자의 영문, 숫자만 사용 가능합니다.',
            'password': '8자 이상, 영문/숫자/특수문자 조합을 권장합니다.',
            'name': '실명을 입력해주세요.',
            'phoneNum': '010-0000-0000 형식으로 입력하세요.',
            'birth': '만 14세 이상만 가입할 수 있습니다.'
        }
    
    def clean_accountID(self):
        """계정ID 유효성 검사"""
        account_id = self.cleaned_data.get('accountID', '').strip()
        
        if not account_id:
            raise ValidationError('계정ID는 필수입니다.')
        
        if len(account_id) < 4:
            raise ValidationError('계정ID는 4자 이상이어야 합니다.')
        
        if len(account_id) > 20:
            raise ValidationError('계정ID는 20자 이하여야 합니다.')
        
        if not re.match(r'^[a-zA-Z0-9]+$', account_id):
            raise ValidationError('계정ID는 영문과 숫자만 사용할 수 있습니다.')
        
        # 중복 검사
        if Member.objects.filter(accountID=account_id).exists():
            raise ValidationError('이미 사용 중인 계정ID입니다.')
        
        # 금지어 체크
        forbidden_words = ['admin', 'root', 'test', 'guest', 'null', 'undefined']
        if account_id.lower() in forbidden_words:
            raise ValidationError('사용할 수 없는 계정ID입니다.')
        
        return account_id
    
    def clean_password(self):
        """비밀번호 유효성 검사"""
        password = self.cleaned_data.get('password', '')
        
        if len(password) < 8:
            raise ValidationError('비밀번호는 8자 이상이어야 합니다.')
        
        if len(password) > 50:
            raise ValidationError('비밀번호는 50자 이하여야 합니다.')
        
        # 비밀번호 강도 검사 (선택적)
        if password.isdigit():
            raise ValidationError('비밀번호는 숫자만으로 구성될 수 없습니다.')
        
        if password.isalpha():
            raise ValidationError('비밀번호는 문자만으로 구성될 수 없습니다.')
        
        return password
    
    def clean_name(self):
        """이름 유효성 검사"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError('이름은 필수입니다.')
        
        if len(name) < 2:
            raise ValidationError('이름은 2자 이상이어야 합니다.')
        
        if len(name) > 45:
            raise ValidationError('이름은 45자 이하여야 합니다.')
        
        if not re.match(r'^[가-힣a-zA-Z\s]+$', name):
            raise ValidationError('이름은 한글, 영문, 공백만 사용할 수 있습니다.')
        
        return name
    
    def clean_phoneNum(self):
        """전화번호 유효성 검사"""
        phone = self.cleaned_data.get('phoneNum', '').strip()
        
        if not phone:
            raise ValidationError('전화번호는 필수입니다.')
        
        if not re.match(r'^01[0-9]-\d{4}-\d{4}$', phone):
            raise ValidationError('전화번호 형식이 올바르지 않습니다. (예: 010-1234-5678)')
        
        # 중복 검사 (선택적)
        if Member.objects.filter(phoneNum=phone).exists():
            raise ValidationError('이미 등록된 전화번호입니다.')
        
        return phone
    
    def clean_email(self):
        """이메일 유효성 검사"""
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if not email:
            raise ValidationError('이메일은 필수입니다.')
        
        # 중복 검사
        if Member.objects.filter(email=email).exists():
            raise ValidationError('이미 등록된 이메일입니다.')
        
        return email
    
    def clean_birth(self):
        """생년월일 유효성 검사"""
        birth = self.cleaned_data.get('birth')
        
        if not birth:
            raise ValidationError('생년월일은 필수입니다.')
        
        if birth > date.today():
            raise ValidationError('생년월일은 오늘 날짜보다 이전이어야 합니다.')
        
        # 나이 제한 (만 14세 이상)
        age = (date.today() - birth).days // 365
        if age < 14:
            raise ValidationError('만 14세 이상만 가입할 수 있습니다.')
        
        if age > 100:
            raise ValidationError('올바른 생년월일을 입력해주세요.')
        
        return birth
    
    def clean(self):
        """전체 폼 유효성 검사"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError({
                    'password_confirm': '비밀번호가 일치하지 않습니다.'
                })
        
        return cleaned_data

class ClassSearchForm(forms.Form):
    """클래스 검색 폼"""
    keyword = forms.CharField(
        max_length=100,
        required=False,
        label='검색어',
        widget=forms.TextInput(attrs={
            'placeholder': '관심사나 클래스명을 입력하세요',
            'class': 'form-control search-input',
            'autocomplete': 'off'
        }),
        help_text='클래스명, 관심사명으로 검색할 수 있습니다.'
    )
    
    interest = forms.ModelChoiceField(
        queryset=Interests.objects.filter(is_active=True).order_by('interestName'),
        required=False,
        label='관심사 필터',
        empty_label='전체 카테고리',
        widget=forms.Select(attrs={
            'class': 'form-select search-input'
        })
    )
    
    def clean_keyword(self):
        """검색어 정리"""
        keyword = self.cleaned_data.get('keyword', '').strip()
        
        if keyword and len(keyword) < 2:
            raise ValidationError('검색어는 2자 이상 입력해주세요.')
        
        if keyword and len(keyword) > 100:
            raise ValidationError('검색어는 100자 이하로 입력해주세요.')
        
        return keyword

class PostForm(forms.ModelForm):
    """게시글 작성 폼"""
    class Meta:
        model = Post
        fields = ['title', 'content', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '게시글 제목을 입력하세요',
                'maxlength': '200',
                'autocomplete': 'off'
            }),
            'content': forms.Textarea(attrs={
                'rows': 10,
                'class': 'form-control form-control-custom',
                'placeholder': '내용을 입력하세요 (최소 10자)',
                'maxlength': '5000'
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
        help_texts = {
            'title': '2-200자 사이로 입력해주세요.',
            'content': '10자 이상 5000자 이하로 입력해주세요.',
            'category': '게시글의 성격에 맞는 카테고리를 선택해주세요.'
        }
    
    def clean_title(self):
        """제목 유효성 검사"""
        title = self.cleaned_data.get('title', '').strip()
        
        if not title:
            raise ValidationError('제목은 필수입니다.')
        
        if len(title) < 2:
            raise ValidationError('제목은 2자 이상이어야 합니다.')
        
        if len(title) > 200:
            raise ValidationError('제목은 200자 이하여야 합니다.')
        
        # 특수문자 제한 (일부만)
        if re.search(r'[<>{}[\]\\]', title):
            raise ValidationError('제목에 사용할 수 없는 특수문자가 포함되어 있습니다.')
        
        return title
    
    def clean_content(self):
        """내용 유효성 검사"""
        content = self.cleaned_data.get('content', '').strip()
        
        if not content:
            raise ValidationError('내용은 필수입니다.')
        
        if len(content) < 10:
            raise ValidationError('내용은 최소 10자 이상이어야 합니다.')
        
        if len(content) > 5000:
            raise ValidationError('내용은 5000자 이하여야 합니다.')
        
        # 스팸 필터 (기본적인)
        spam_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URL
            r'[가-힣]{10,}',  # 의미없는 긴 한글
            r'(.)\1{10,}',  # 동일 문자 반복
        ]
        
        for pattern in spam_patterns:
            if re.search(pattern, content):
                raise ValidationError('부적절한 내용이 포함되어 있습니다.')
        
        return content

class AttendanceForm(forms.ModelForm):
    """출석 체크 폼"""
    class Meta:
        model = Attendance
        fields = ['attendDate', 'attendanceStatus']
        widgets = {
            'attendDate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-custom',
                'max': date.today().isoformat(),
                'min': (date.today() - timedelta(days=30)).isoformat()  # 30일 전까지
            }),
            'attendanceStatus': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
        }
        labels = {
            'attendDate': '출석일',
            'attendanceStatus': '출석상태',
        }
        help_texts = {
            'attendDate': '출석을 체크할 날짜를 선택하세요.',
            'attendanceStatus': '해당 일자의 출석 상태를 선택하세요.'
        }
    
    def clean_attendDate(self):
        """출석일 유효성 검사"""
        attend_date = self.cleaned_data.get('attendDate')
        
        if not attend_date:
            raise ValidationError('출석일은 필수입니다.')
        
        if attend_date > date.today():
            raise ValidationError('출석일은 오늘 날짜보다 이후일 수 없습니다.')
        
        # 너무 과거 날짜 제한
        if attend_date < (date.today() - timedelta(days=30)):
            raise ValidationError('출석일은 30일 이전일 수 없습니다.')
        
        return attend_date

class LoginForm(forms.Form):
    """로그인 폼"""
    accountID = forms.CharField(
        max_length=50,
        label='계정ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': '계정ID를 입력하세요',
            'autocomplete': 'username',
            'required': True
        }),
        error_messages={
            'required': '계정ID를 입력해주세요.'
        }
    )
    
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': '비밀번호를 입력하세요',
            'autocomplete': 'current-password',
            'required': True
        }),
        error_messages={
            'required': '비밀번호를 입력해주세요.'
        }
    )
    
    remember_me = forms.BooleanField(
        required=False,
        label='로그인 상태 유지',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_accountID(self):
        """계정ID 정리"""
        account_id = self.cleaned_data.get('accountID', '').strip()
        
        if not account_id:
            raise ValidationError('계정ID를 입력해주세요.')
        
        if len(account_id) > 50:
            raise ValidationError('계정ID가 너무 깁니다.')
        
        return account_id
    
    def clean_password(self):
        """비밀번호 정리"""
        password = self.cleaned_data.get('password', '')
        
        if not password:
            raise ValidationError('비밀번호를 입력해주세요.')
        
        if len(password) > 255:
            raise ValidationError('비밀번호가 너무 깁니다.')
        
        return password

# 추가 폼들
class ClassCreationForm(forms.ModelForm):
    """클래스 생성 폼 (관리자용)"""
    class Meta:
        model = Class
        fields = ['className', 'classStartDate', 'classEndDate', 'interestID', 'description', 'max_members']
        widgets = {
            'className': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '클래스명을 입력하세요'
            }),
            'classStartDate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': date.today().isoformat()
            }),
            'classEndDate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': date.today().isoformat()
            }),
            'interestID': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'max_members': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100'
            })
        }
    
    def clean(self):
        """클래스 생성 유효성 검사"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('classStartDate')
        end_date = cleaned_data.get('classEndDate')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError({
                    'classEndDate': '종료일은 시작일보다 이후여야 합니다.'
                })
            
            if (end_date - start_date).days > 365:
                raise ValidationError({
                    'classEndDate': '클래스 기간은 1년을 초과할 수 없습니다.'
                })
        
        return cleaned_data