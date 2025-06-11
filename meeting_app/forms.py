# meeting_app/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Member, Class, Post, Attendance, Interests
import re
from datetime import date

class MemberRegistrationForm(forms.ModelForm):
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': '비밀번호를 다시 입력하세요'
        }),
        label='비밀번호 확인',
        help_text='위에서 입력한 비밀번호를 다시 입력해주세요.'
    )
    
    class Meta:
        model = Member
        fields = ['accountID', 'password', 'accountType', 'name', 'phoneNum', 'email', 'birth']
        widgets = {
            'accountID': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '4-20자의 영문, 숫자 조합',
                'pattern': '[a-zA-Z0-9]{4,20}',
                'title': '4-20자의 영문, 숫자만 입력 가능합니다.'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '8자 이상의 비밀번호',
                'minlength': '8'
            }),
            'accountType': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '실명을 입력하세요',
                'maxlength': '45'
            }),
            'phoneNum': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '010-0000-0000',
                'pattern': '01[0-9]-[0-9]{4}-[0-9]{4}',
                'title': '010-0000-0000 형식으로 입력해주세요.'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': 'example@email.com'
            }),
            'birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-custom',
                'max': date.today().strftime('%Y-%m-%d')
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
            'accountID': '4-20자의 영문, 숫자 조합 (특수문자 불가)',
            'password': '8자 이상, 영문/숫자/특수문자 조합 권장',
            'phoneNum': '하이픈(-)을 포함하여 입력해주세요.',
            'email': '인증에 사용될 이메일 주소를 입력해주세요.',
        }
    
    def clean_accountID(self):
        account_id = self.cleaned_data.get('accountID')
        if account_id:
            # 영문, 숫자만 허용
            if not re.match(r'^[a-zA-Z0-9]{4,20}$', account_id):
                raise ValidationError('4-20자의 영문, 숫자만 입력 가능합니다.')
            
            # 기존 계정 중복 확인
            if Member.objects.filter(accountID=account_id).exists():
                raise ValidationError('이미 사용 중인 계정ID입니다.')
        
        return account_id
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < 8:
                raise ValidationError('비밀번호는 8자 이상이어야 합니다.')
            
            # 비밀번호 강도 검사 (선택적)
            if password.isdigit():
                raise ValidationError('비밀번호는 숫자만으로 구성할 수 없습니다.')
            
            if password.lower() == password:
                self.add_error('password', '대문자를 포함하는 것을 권장합니다.')
        
        return password
    
    def clean_phoneNum(self):
        phone = self.cleaned_data.get('phoneNum')
        if phone:
            # 전화번호 형식 검증
            if not re.match(r'^01[0-9]-[0-9]{4}-[0-9]{4}$', phone):
                raise ValidationError('010-0000-0000 형식으로 입력해주세요.')
        
        return phone
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # 이메일 중복 확인
            if Member.objects.filter(email=email).exists():
                raise ValidationError('이미 사용 중인 이메일입니다.')
        
        return email
    
    def clean_birth(self):
        birth = self.cleaned_data.get('birth')
        if birth:
            # 생년월일 유효성 검사
            today = date.today()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            
            if birth > today:
                raise ValidationError('생년월일은 오늘 날짜보다 이전이어야 합니다.')
            
            if age > 150:
                raise ValidationError('올바른 생년월일을 입력해주세요.')
            
            if age < 14:
                raise ValidationError('만 14세 이상만 가입 가능합니다.')
        
        return birth
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('비밀번호가 일치하지 않습니다.')
        
        return cleaned_data

class ClassSearchForm(forms.Form):
    keyword = forms.CharField(
        max_length=100,
        required=False,
        label='검색어',
        widget=forms.TextInput(attrs={
            'placeholder': '클래스명, 설명, 관심사를 검색하세요',
            'class': 'form-control search-input',
            'autocomplete': 'off'
        })
    )
    
    interest = forms.ModelChoiceField(
        queryset=None,  # __init__에서 설정
        required=False,
        label='관심사 필터',
        empty_label='전체 카테고리',
        widget=forms.Select(attrs={
            'class': 'form-select search-input'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('all', '전체'),
            ('active', '진행중'),
            ('upcoming', '예정'),
            ('available', '신청가능'),
        ],
        required=False,
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-select search-input'
        }),
        label='상태'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 관심사 쿼리셋 설정 (클래스가 있는 관심사만)
        try:
            self.fields['interest'].queryset = Interests.objects.filter(
                classes__isnull=False
            ).distinct().order_by('interestName')
        except Exception:
            self.fields['interest'].queryset = Interests.objects.none()

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-custom',
                'placeholder': '게시글 제목을 입력하세요',
                'maxlength': '200'
            }),
            'content': forms.Textarea(attrs={
                'rows': 12,
                'class': 'form-control form-control-custom',
                'placeholder': '내용을 입력하세요 (최소 10자 이상)',
                'style': 'resize: vertical;'
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
            'title': '명확하고 구체적인 제목을 작성해주세요.',
            'content': '다른 회원들에게 도움이 되는 내용을 작성해주세요.',
            'category': '게시글 성격에 맞는 카테고리를 선택해주세요.',
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            title = title.strip()
            if len(title) < 5:
                raise ValidationError('제목은 5자 이상 입력해주세요.')
            
            # 금지어 검사 (예시)
            forbidden_words = ['스팸', '광고', '홍보']
            for word in forbidden_words:
                if word in title:
                    raise ValidationError(f'제목에 "{word}"가 포함될 수 없습니다.')
        
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content:
            content = content.strip()
            if len(content) < 10:
                raise ValidationError('내용은 10자 이상 입력해주세요.')
            
            if len(content) > 10000:
                raise ValidationError('내용은 10,000자를 초과할 수 없습니다.')
            
            # 금지어 검사 (예시)
            forbidden_words = ['스팸', '광고', '홍보']
            for word in forbidden_words:
                if word in content:
                    raise ValidationError(f'내용에 "{word}"가 포함될 수 없습니다.')
        
        return content

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['attendDate', 'attendanceStatus', 'notes']
        widgets = {
            'attendDate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-custom',
                'max': date.today().strftime('%Y-%m-%d')
            }),
            'attendanceStatus': forms.Select(attrs={
                'class': 'form-select form-control-custom'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-custom',
                'placeholder': '특이사항이 있으면 입력하세요 (선택사항)'
            }),
        }
        labels = {
            'attendDate': '출석일',
            'attendanceStatus': '출석상태',
            'notes': '비고',
        }
    
    def clean_attendDate(self):
        attend_date = self.cleaned_data.get('attendDate')
        if attend_date:
            if attend_date > date.today():
                raise ValidationError('출석일은 오늘 날짜보다 이후일 수 없습니다.')
        
        return attend_date

class LoginForm(forms.Form):
    accountID = forms.CharField(
        max_length=50,
        label='계정ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': '계정ID를 입력하세요',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label='비밀번호',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-custom',
            'placeholder': '비밀번호를 입력하세요',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label='로그인 상태 유지',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_accountID(self):
        account_id = self.cleaned_data.get('accountID')
        if account_id:
            account_id = account_id.strip()
            if not account_id:
                raise ValidationError('계정ID를 입력해주세요.')
        
        return account_id
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            if len(password.strip()) == 0:
                raise ValidationError('비밀번호를 입력해주세요.')
        
        return password

class ClassCreateForm(forms.ModelForm):
    """클래스 생성 폼 (관리자/강사용)"""
    class Meta:
        model = Class
        fields = ['className', 'classDescription', 'classStartDate', 'classEndDate', 
                 'maxMembers', 'interestID', 'instructor']
        widgets = {
            'className': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '클래스명을 입력하세요'
            }),
            'classDescription': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '클래스에 대한 설명을 입력하세요'
            }),
            'classStartDate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': date.today().strftime('%Y-%m-%d')
            }),
            'classEndDate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': date.today().strftime('%Y-%m-%d')
            }),
            'maxMembers': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'value': '20'
            }),
            'interestID': forms.Select(attrs={
                'class': 'form-select'
            }),
            'instructor': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'className': '클래스명',
            'classDescription': '클래스 설명',
            'classStartDate': '시작일',
            'classEndDate': '종료일',
            'maxMembers': '최대 인원',
            'interestID': '관심사',
            'instructor': '강사',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 강사만 선택 가능하도록 필터링
        self.fields['instructor'].queryset = Member.objects.filter(
            accountType__in=['instructor', 'admin']
        ).order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('classStartDate')
        end_date = cleaned_data.get('classEndDate')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise ValidationError('종료일은 시작일보다 이후여야 합니다.')
            
            if start_date < date.today():
                raise ValidationError('시작일은 오늘 날짜 이후여야 합니다.')
        
        return cleaned_data

class InterestForm(forms.ModelForm):
    """관심사 생성/수정 폼"""
    class Meta:
        model = Interests
        fields = ['interestName', 'description']
        widgets = {
            'interestName': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '관심사명을 입력하세요'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '관심사에 대한 설명을 입력하세요'
            }),
        }
        labels = {
            'interestName': '관심사명',
            'description': '설명',
        }
    
    def clean_interestName(self):
        interest_name = self.cleaned_data.get('interestName')
        if interest_name:
            interest_name = interest_name.strip()
            
            # 중복 확인 (수정시에는 자기 자신 제외)
            queryset = Interests.objects.filter(interestName=interest_name)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError('이미 존재하는 관심사명입니다.')
        
        return interest_name