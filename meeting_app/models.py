# meeting_app/models.py
from django.db import models
from django.core.validators import MinLengthValidator, EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
import re

class Member(models.Model):
    """회원 모델 - MySQL 최적화"""
    ACCOUNT_TYPE_CHOICES = [
        ('student', '학생'),
        ('instructor', '강사'),
        ('admin', '관리자'),
    ]
    
    accountID = models.CharField(
        max_length=50, 
        primary_key=True, 
        verbose_name='계정ID',
        validators=[
            MinLengthValidator(4, message='계정ID는 4자 이상이어야 합니다.'),
            RegexValidator(
                regex=r'^[a-zA-Z0-9]+$',
                message='계정ID는 영문과 숫자만 사용할 수 있습니다.'
            )
        ],
        help_text='4-50자의 영문, 숫자 조합'
    )
    
    password = models.CharField(
        max_length=255, 
        verbose_name='비밀번호',
        validators=[MinLengthValidator(8, message='비밀번호는 8자 이상이어야 합니다.')]
    )
    
    accountType = models.CharField(
        max_length=20, 
        choices=ACCOUNT_TYPE_CHOICES, 
        default='student',
        verbose_name='계정타입',
        db_index=True  # 인덱스 추가
    )
    
    joinDate = models.DateField(
        auto_now_add=True, 
        verbose_name='가입일',
        db_index=True  # 정렬용 인덱스
    )
    
    name = models.CharField(
        max_length=45, 
        verbose_name='이름',
        db_index=True,  # 검색용 인덱스
        validators=[
            RegexValidator(
                regex=r'^[가-힣a-zA-Z\s]+$',
                message='이름은 한글, 영문만 사용할 수 있습니다.'
            )
        ]
    )
    
    phoneNum = models.CharField(
        max_length=45, 
        verbose_name='전화번호',
        validators=[
            RegexValidator(
                regex=r'^01[0-9]-\d{4}-\d{4}$',
                message='전화번호 형식이 올바르지 않습니다. (예: 010-1234-5678)'
            )
        ]
    )
    
    email = models.EmailField(
        max_length=100,  # 길이 늘림
        unique=True, 
        verbose_name='이메일',
        validators=[EmailValidator(message='올바른 이메일 형식이 아닙니다.')],
        db_index=True  # 유니크 제약과 검색용
    )
    
    birth = models.DateField(
        verbose_name='생년월일',
        help_text='YYYY-MM-DD 형식'
    )
    
    # 추가 필드들
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성 상태',
        db_index=True
    )
    
    last_login = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='마지막 로그인'
    )
    
    class Meta:
        db_table = 'member'
        verbose_name = '회원'
        verbose_name_plural = '회원들'
        indexes = [
            models.Index(fields=['accountType', 'joinDate']),  # 복합 인덱스
            models.Index(fields=['name']),  # 이름 검색용
            models.Index(fields=['-joinDate']),  # 최신 가입자순
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(birth__lte=date.today()),
                name='valid_birth_date'
            )
        ]
    
    def clean(self):
        """모델 레벨 유효성 검사"""
        super().clean()
        
        # 생년월일 검사
        if self.birth and self.birth > date.today():
            raise ValidationError({'birth': '생년월일은 오늘 날짜보다 이전이어야 합니다.'})
        
        # 나이 제한 (만 14세 이상)
        if self.birth:
            age = (date.today() - self.birth).days // 365
            if age < 14:
                raise ValidationError({'birth': '만 14세 이상만 가입할 수 있습니다.'})
    
    def save(self, *args, **kwargs):
        self.full_clean()  # 유효성 검사 실행
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.accountID})"
    
    @property
    def age(self):
        """나이 계산"""
        if self.birth:
            return (date.today() - self.birth).days // 365
        return None

class Interests(models.Model):
    """관심사 모델 - 검색 최적화"""
    interestID = models.AutoField(primary_key=True, verbose_name='관심사ID')
    interestName = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='관심사명',
        db_index=True,  # 검색 최적화
        validators=[
            RegexValidator(
                regex=r'^[가-힣a-zA-Z0-9\s/]+$',
                message='관심사명에는 한글, 영문, 숫자, 공백, /만 사용할 수 있습니다.'
            )
        ]
    )
    
    # 추가 필드들
    description = models.TextField(
        blank=True,
        verbose_name='설명'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성 상태',
        db_index=True
    )
    
    created_date = models.DateField(
        auto_now_add=True,
        verbose_name='생성일'
    )
    
    class Meta:
        db_table = 'interests'
        verbose_name = '관심사'
        verbose_name_plural = '관심사들'
        ordering = ['interestName']
        indexes = [
            models.Index(fields=['interestName']),  # 이름 검색용
            models.Index(fields=['is_active', 'interestName']),  # 활성 관심사
        ]
    
    def __str__(self):
        return self.interestName

class Class(models.Model):
    """클래스 모델 - 성능 최적화"""
    classID = models.AutoField(primary_key=True, verbose_name='클래스ID')
    className = models.CharField(
        max_length=150,  # 길이 증가
        verbose_name='클래스명',
        db_index=True,  # 검색용 인덱스
        validators=[
            MinLengthValidator(2, message='클래스명은 2자 이상이어야 합니다.')
        ]
    )
    
    classStartDate = models.DateField(
        verbose_name='시작일',
        db_index=True,  # 날짜 검색용
        help_text='YYYY-MM-DD 형식'
    )
    
    classEndDate = models.DateField(
        verbose_name='종료일',
        db_index=True,  # 날짜 검색용
        help_text='YYYY-MM-DD 형식'
    )
    
    interestID = models.ForeignKey(
        Interests, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='관련관심사',
        related_name='classes',
        db_index=True  # 조인 최적화
    )
    
    # 추가 필드들
    description = models.TextField(
        blank=True,
        verbose_name='클래스 설명'
    )
    
    max_members = models.PositiveIntegerField(
        default=20,
        verbose_name='최대 인원',
        help_text='최대 참여 가능 인원'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성 상태',
        db_index=True
    )
    
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성일시'
    )
    
    class Meta:
        db_table = 'class'
        verbose_name = '클래스'
        verbose_name_plural = '클래스들'
        ordering = ['-classID']
        indexes = [
            models.Index(fields=['interestID', 'classStartDate']),  # 관심사별 시작일
            models.Index(fields=['is_active', '-classID']),  # 활성 클래스
            models.Index(fields=['classStartDate', 'classEndDate']),  # 날짜 범위
            models.Index(fields=['-created_date']),  # 최신순
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(classEndDate__gt=models.F('classStartDate')),
                name='valid_class_dates'
            ),
            models.CheckConstraint(
                check=models.Q(max_members__gt=0),
                name='positive_max_members'
            )
        ]
    
    def clean(self):
        """모델 레벨 유효성 검사"""
        super().clean()
        
        if self.classStartDate and self.classEndDate:
            if self.classStartDate >= self.classEndDate:
                raise ValidationError({
                    'classEndDate': '종료일은 시작일보다 이후여야 합니다.'
                })
        
        # 과거 날짜 체크 (생성 시에만)
        if not self.pk and self.classStartDate and self.classStartDate < date.today():
            raise ValidationError({
                'classStartDate': '시작일은 오늘 날짜 이후여야 합니다.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.className
    
    @property
    def member_count(self):
        """참여 회원 수 - annotate/F 없이 항상 단순 count 쿼리만 사용 (MySQL ONLY_FULL_GROUP_BY 안전)"""
        return self.sugang_set.count()
    
    @property
    def is_full(self):
        """정원 초과 여부 - annotate/F 없이 항상 단순 count 쿼리만 사용 (MySQL ONLY_FULL_GROUP_BY 안전)"""
        return self.member_count >= self.max_members
    
    @property
    def is_ongoing(self):
        """진행중 여부"""
        today = date.today()
        return self.classStartDate <= today <= self.classEndDate

class MemberInterests(models.Model):
    """회원 관심사 모델"""
    member = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE, 
        verbose_name='회원',
        related_name='member_interests'
    )
    interests = models.ForeignKey(
        Interests, 
        on_delete=models.CASCADE, 
        verbose_name='관심사',
        related_name='member_interests'
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='등록일시'
    )
    
    class Meta:
        db_table = 'memberInterests'
        unique_together = ('member', 'interests')
        verbose_name = '회원관심사'
        verbose_name_plural = '회원관심사들'
        indexes = [
            models.Index(fields=['member', 'interests']),
            models.Index(fields=['interests']),  # 관심사별 회원 조회
        ]
    
    def __str__(self):
        return f"{self.member.name} - {self.interests.interestName}"

class Sugang(models.Model):
    """수강신청 모델 - 트랜잭션 최적화"""
    sugangID = models.AutoField(primary_key=True, verbose_name='수강ID')
    class_classID = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        verbose_name='클래스',
        related_name='sugang_set'
    )
    member_accountID = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE, 
        verbose_name='회원',
        related_name='sugang_set'
    )
    registration_date = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='신청일시',
        db_index=True
    )
    
    # 추가 필드
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '대기중'),
            ('approved', '승인됨'),
            ('cancelled', '취소됨'),
        ],
        default='approved',
        verbose_name='신청상태',
        db_index=True
    )
    
    class Meta:
        db_table = 'sugang'
        # unique_together = ('class_classID', 'member_accountID')
        verbose_name = '수강신청'
        verbose_name_plural = '수강신청들'
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['class_classID', 'status']),  # 클래스별 상태
            models.Index(fields=['member_accountID', '-registration_date']),  # 회원별 신청이력
            models.Index(fields=['-registration_date']),  # 최신 신청순
        ]
    
    def clean(self):
        """수강신청 유효성 검사 - 모든 체크를 views.py로 이관 (ONLY_FULL_GROUP_BY 디버깅용)"""
        super().clean()
        # 모든 유효성 검사 로직을 views.py에서 수행하도록 이관함.
        # 이 clean 메서드는 현재 ONLY_FULL_GROUP_BY 오류를 유발할 수 있는 어떤 쿼리도 발생시키지 않음.
        pass # <-- 이 메서드 내의 모든 로직을 제거하고 'pass'만 남깁니다.
    
    # def save(self, *args, **kwargs): # <-- 이 save 메서드 전체는 이미 주석 처리됨.
    #     self.full_clean()
    #     super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.member_accountID.name} - {self.class_classID.className}"

class Attendance(models.Model):
    """출석 모델 - 집계 최적화"""
    ATTENDANCE_STATUS_CHOICES = [
        ('present', '출석'),
        ('absent', '결석'),
        ('late', '지각'),
    ]
    
    attendanceID = models.AutoField(primary_key=True, verbose_name='출석ID')
    attendDate = models.DateField(
        verbose_name='출석일',
        db_index=True  # 날짜별 조회 최적화
    )
    attendanceStatus = models.CharField(
        max_length=20, 
        choices=ATTENDANCE_STATUS_CHOICES, 
        default='present',
        verbose_name='출석상태',
        db_index=True  # 상태별 집계용
    )
    sugang_sugangID = models.ForeignKey(
        Sugang, 
        on_delete=models.CASCADE, 
        verbose_name='수강신청',
        related_name='attendance_set'
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='기록일시'
    )
    
    class Meta:
        db_table = 'attendance'
        unique_together = ('sugang_sugangID', 'attendDate')
        verbose_name = '출석'
        verbose_name_plural = '출석들'
        ordering = ['-attendDate']
        indexes = [
            models.Index(fields=['attendDate', 'attendanceStatus']),  # 날짜별 상태
            models.Index(fields=['sugang_sugangID', 'attendDate']),  # 수강생별 출석이력
            models.Index(fields=['-attendDate']),  # 최신 출석순
        ]
    
    def __str__(self):
        return f"{self.sugang_sugangID.member_accountID.name} - {self.attendDate} - {self.get_attendanceStatus_display()}"

class Post(models.Model):
    """게시글 모델 - 검색 최적화"""
    CATEGORY_CHOICES = [
        ('notice', '공지'),
        ('review', '후기'),
        ('general', '일반'),
    ]
    
    postID = models.AutoField(primary_key=True, verbose_name='게시글ID')
    title = models.CharField(
        max_length=200, 
        verbose_name='제목',
        db_index=True,  # 제목 검색용
        validators=[
            MinLengthValidator(2, message='제목은 2자 이상이어야 합니다.')
        ]
    )
    content = models.TextField(
        verbose_name='내용',
        validators=[
            MinLengthValidator(10, message='내용은 10자 이상이어야 합니다.')
        ]
    )
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        default='general',
        verbose_name='카테고리',
        db_index=True  # 카테고리별 필터링
    )
    class_classID = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        verbose_name='클래스',
        related_name='posts'
    )
    author = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE, 
        verbose_name='작성자',
        related_name='posts'
    )
    writeDate = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='작성일',
        db_index=True  # 작성일순 정렬용
    )
    updateDate = models.DateTimeField(
        auto_now=True, 
        verbose_name='수정일'
    )
    
    # 추가 필드
    views = models.PositiveIntegerField(
        default=0,
        verbose_name='조회수',
        db_index=True
    )
    
    is_pinned = models.BooleanField(
        default=False,
        verbose_name='상단 고정',
        db_index=True
    )
    
    class Meta:
        db_table = 'post'
        verbose_name = '게시글'
        verbose_name_plural = '게시글들'
        ordering = ['-is_pinned', '-writeDate']  # 고정글 우선, 최신순
        indexes = [
            models.Index(fields=['class_classID', 'category', '-writeDate']),  # 클래스별 카테고리
            models.Index(fields=['author', '-writeDate']),  # 작성자별
            models.Index(fields=['-writeDate']),  # 최신순
            models.Index(fields=['category']),  # 카테고리별
            models.Index(fields=['-is_pinned', '-writeDate']),  # 고정글 정렬
        ]
    
    def clean(self):
        """게시글 유효성 검사"""
        super().clean()
        
        if len(self.title.strip()) < 2:
            raise ValidationError({'title': '제목은 2자 이상이어야 합니다.'})
        
        if len(self.content.strip()) < 10:
            raise ValidationError({'content': '내용은 10자 이상이어야 합니다.'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.author.name}"
    
    @property
    def is_recent(self):
        """최근 게시글 여부 (3일 이내)"""
        return (timezone.now() - self.writeDate).days <= 3