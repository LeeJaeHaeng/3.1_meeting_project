 
# meeting_app/models.py
from django.db import models
from django.core.validators import MinLengthValidator, EmailValidator

class Member(models.Model):
    ACCOUNT_TYPE_CHOICES = [
        ('student', '학생'),
        ('instructor', '강사'),
        ('admin', '관리자'),
    ]
    
    accountID = models.CharField(
        max_length=50, 
        primary_key=True, 
        verbose_name='계정ID',
        validators=[MinLengthValidator(4)]
    )
    password = models.CharField(max_length=100, verbose_name='비밀번호')
    accountType = models.CharField(
        max_length=20, 
        choices=ACCOUNT_TYPE_CHOICES, 
        default='student',
        verbose_name='계정타입'
    )
    joinDate = models.DateField(auto_now_add=True, verbose_name='가입일')
    name = models.CharField(max_length=45, verbose_name='이름')
    phoneNum = models.CharField(max_length=45, verbose_name='전화번호')
    email = models.EmailField(
        max_length=45, 
        unique=True, 
        verbose_name='이메일',
        validators=[EmailValidator()]
    )
    birth = models.DateField(verbose_name='생년월일')
    
    class Meta:
        db_table = 'member'
        verbose_name = '회원'
        verbose_name_plural = '회원들'
    
    def __str__(self):
        return f"{self.name} ({self.accountID})"

class Interests(models.Model):
    interestID = models.AutoField(primary_key=True, verbose_name='관심사ID')
    interestName = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name='관심사명'
    )
    
    class Meta:
        db_table = 'interests'
        verbose_name = '관심사'
        verbose_name_plural = '관심사들'
        ordering = ['interestName']
    
    def __str__(self):
        return self.interestName

class Class(models.Model):
    classID = models.AutoField(primary_key=True, verbose_name='클래스ID')
    className = models.CharField(max_length=100, verbose_name='클래스명')
    classStartDate = models.DateField(verbose_name='시작일')
    classEndDate = models.DateField(verbose_name='종료일')
    interestID = models.ForeignKey(
        Interests, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='관련관심사',
        related_name='classes'
    )
    
    class Meta:
        db_table = 'class'
        verbose_name = '클래스'
        verbose_name_plural = '클래스들'
        ordering = ['-classID']
    
    def __str__(self):
        return self.className
    
    @property
    def member_count(self):
        """참여 회원 수"""
        return self.sugang_set.count()

class MemberInterests(models.Model):
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
    
    class Meta:
        db_table = 'memberInterests'
        unique_together = ('member', 'interests')
        verbose_name = '회원관심사'
        verbose_name_plural = '회원관심사들'
    
    def __str__(self):
        return f"{self.member.name} - {self.interests.interestName}"

class Sugang(models.Model):
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
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name='신청일시')
    
    class Meta:
        db_table = 'sugang'
        unique_together = ('class_classID', 'member_accountID')
        verbose_name = '수강신청'
        verbose_name_plural = '수강신청들'
        ordering = ['-registration_date']
    
    def __str__(self):
        return f"{self.member_accountID.name} - {self.class_classID.className}"

class Attendance(models.Model):
    ATTENDANCE_STATUS_CHOICES = [
        ('present', '출석'),
        ('absent', '결석'),
        ('late', '지각'),
    ]
    
    attendanceID = models.AutoField(primary_key=True, verbose_name='출석ID')
    attendDate = models.DateField(verbose_name='출석일')
    attendanceStatus = models.CharField(
        max_length=20, 
        choices=ATTENDANCE_STATUS_CHOICES, 
        default='present',
        verbose_name='출석상태'
    )
    sugang_sugangID = models.ForeignKey(
        Sugang, 
        on_delete=models.CASCADE, 
        verbose_name='수강신청',
        related_name='attendance_set'
    )
    
    class Meta:
        db_table = 'attendance'
        unique_together = ('sugang_sugangID', 'attendDate')
        verbose_name = '출석'
        verbose_name_plural = '출석들'
        ordering = ['-attendDate']
    
    def __str__(self):
        return f"{self.sugang_sugangID.member_accountID.name} - {self.attendDate} - {self.get_attendanceStatus_display()}"

class Post(models.Model):
    CATEGORY_CHOICES = [
        ('notice', '공지'),
        ('review', '후기'),
        ('general', '일반'),
    ]
    
    postID = models.AutoField(primary_key=True, verbose_name='게시글ID')
    title = models.CharField(max_length=200, verbose_name='제목')
    content = models.TextField(verbose_name='내용')
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        default='general',
        verbose_name='카테고리'
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
    writeDate = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updateDate = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        db_table = 'post'
        verbose_name = '게시글'
        verbose_name_plural = '게시글들'
        ordering = ['-writeDate']
    
    def __str__(self):
        return f"{self.title} - {self.author.name}"