# meeting_app/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import * # 모든 모델 임포트

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['accountID', 'name', 'email', 'accountType', 'joinDate', 'member_classes_count', 'is_active']
    list_filter = ['accountType', 'joinDate', 'is_active']
    search_fields = ['accountID', 'name', 'email', 'phoneNum']
    readonly_fields = ['joinDate']
    list_per_page = 25
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('accountID', 'name', 'email', 'phoneNum', 'birth')
        }),
        ('계정 정보', {
            'fields': ('password', 'accountType', 'is_active', 'last_login', 'joinDate')
        }),
    )
    
    def member_classes_count(self, obj):
        """참여 클래스 수"""
        # Sugang 모델에 is_active 필드가 없으므로, obj.sugang_set.count()만 사용합니다.
        # 만약 Sugang 모델에 '승인됨' 상태만 세고 싶다면 .filter(status='approved')를 사용합니다.
        count = obj.sugang_set.count() 
        return format_html(
            '<span style="color: #007cba;">{} 개</span>',
            count
        )
    member_classes_count.short_description = '참여 클래스'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('sugang_set')

@admin.register(Interests)
class InterestsAdmin(admin.ModelAdmin):
    list_display = ['interestID', 'interestName', 'class_count', 'is_active', 'created_date'] # 'created_at' -> 'created_date', 'is_active' 추가
    list_filter = ['is_active', 'created_date'] # 'created_at' -> 'created_date'
    search_fields = ['interestName', 'description']
    readonly_fields = ['created_date'] # 'created_at' -> 'created_date'
    list_per_page = 30
    
    def class_count(self, obj):
        """관련 클래스 수"""
        count = obj.classes.count()
        if count > 0:
            url = reverse('admin:meeting_app_class_changelist') + f'?interestID__interestID__exact={obj.interestID}' 
            return format_html(
                '<a href="{}" style="color: #007cba;">{} 개</a>',
                url, count
            )
        return '0 개'
    class_count.short_description = '클래스 수'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('classes')

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    # 'instructor' 필드는 Class 모델에 직접적인 필드가 없으므로 삭제했습니다.
    # classDescription -> description, maxMembers -> max_members, created_at -> created_date
    list_display = ['classID', 'className', 'interestID', 'member_count', 
                   'classStartDate', 'classEndDate', 'status', 'is_active', 'created_date'] # 'created_at' -> 'created_date', 'is_active' 추가
    # 'instructor__accountType'는 Class 모델에 instructor 필드가 없으므로 제거
    list_filter = ['classStartDate', 'classEndDate', 'interestID', 'is_active'] # 'instructor__accountType' 제거, 'is_active' 추가
    search_fields = ['className', 'description'] # 'classDescription' -> 'description', 'instructor__name' 제거
    date_hierarchy = 'classStartDate'
    readonly_fields = ['created_date'] # 'created_at' -> 'created_date'
    list_per_page = 20
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('className', 'description', 'interestID') # 'classDescription' -> 'description', 'instructor' 제거
        }),
        ('일정 및 정원', {
            'fields': ('classStartDate', 'classEndDate', 'max_members', 'is_active') # 'maxMembers' -> 'max_members', 'is_active' 추가
        }),
        ('시스템 정보', {
            'fields': ('created_date',), # 'created_at' -> 'created_date'
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        """참여 회원 수"""
        count = obj.member_count # obj.member_count @property를 사용
        if count > 0:
            url = reverse('admin:meeting_app_sugang_changelist') + f'?class_classID__classID__exact={obj.classID}' 
            return format_html(
                '<a href="{}" style="color: #007cba;">{}/{}</a>',
                url, count, obj.max_members 
            )
        return f'0/{obj.max_members}' 
    member_count.short_description = '참여인원'
    
    def status(self, obj):
        """클래스 상태"""
        today = timezone.now().date()
        if obj.classEndDate < today:
            return format_html('<span style="color: #dc3545;">종료</span>')
        elif obj.classStartDate > today:
            return format_html('<span style="color: #ffc107;">예정</span>')
        else:
            return format_html('<span style="color: #28a745;">진행중</span>')
    status.short_description = '상태'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'interestID' 
        ).prefetch_related('sugang_set')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['postID', 'title', 'category', 'author', 'class_classID', 
                   'views', 'is_pinned', 'writeDate'] # 'view_count' -> 'views'
    list_filter = ['category', 'writeDate', 'is_pinned', 'class_classID']
    search_fields = ['title', 'content', 'author__name']
    date_hierarchy = 'writeDate'
    readonly_fields = ['writeDate', 'updateDate', 'views'] # 'view_count' -> 'views'
    list_per_page = 25
    
    fieldsets = (
        ('게시글 정보', {
            'fields': ('title', 'content', 'category', 'is_pinned')
        }),
        ('작성자 및 클래스', {
            'fields': ('author', 'class_classID')
        }),
        ('시스템 정보', {
            'fields': ('writeDate', 'updateDate', 'views'), # 'view_count' -> 'views'
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'author', 'class_classID'
        )

@admin.register(Sugang)
class SugangAdmin(admin.ModelAdmin):
    list_display = ['sugangID', 'member_name', 'class_name', 'registration_date', 'status'] # 'is_active' 제거, 'status' 추가
    list_filter = ['registration_date', 'status', 'class_classID'] # 'is_active' 제거, 'status' 추가
    search_fields = ['member_accountID__name', 'class_classID__className']
    date_hierarchy = 'registration_date'
    readonly_fields = ['registration_date']
    list_per_page = 30
    
    def member_name(self, obj):
        """회원 이름"""
        url = reverse('admin:meeting_app_member_change', args=[obj.member_accountID.accountID])
        return format_html(
            '<a href="{}">{}</a>',
            url, obj.member_accountID.name
        )
    member_name.short_description = '회원명'
    
    def class_name(self, obj):
        """클래스 이름"""
        url = reverse('admin:meeting_app_class_change', args=[obj.class_classID.classID])
        return format_html(
            '<a href="{}">{}</a>',
            url, obj.class_classID.className
        )
    class_name.short_description = '클래스명'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'member_accountID', 'class_classID'
        )

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['attendanceID', 'member_name', 'class_name', 'attendDate', 
                   'attendanceStatus', 'created_date'] # 'created_at' -> 'created_date'
    list_filter = ['attendanceStatus', 'attendDate', 'created_date'] # 'created_at' -> 'created_date'
    search_fields = ['sugang_sugangID__member_accountID__name', 
                    'sugang_sugangID__class_classID__className']
    date_hierarchy = 'attendDate'
    readonly_fields = ['created_date'] # 'created_at' -> 'created_date'
    list_per_page = 50
    
    def member_name(self, obj):
        """회원 이름"""
        return obj.sugang_sugangID.member_accountID.name
    member_name.short_description = '회원명'
    
    def class_name(self, obj):
        """클래스 이름"""
        return obj.sugang_sugangID.class_classID.className
    class_name.short_description = '클래스명'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sugang_sugangID__member_accountID',
            'sugang_sugangID__class_classID'
        )

@admin.register(MemberInterests)
class MemberInterestsAdmin(admin.ModelAdmin):
    list_display = ['id', 'member_name', 'interest_name', 'created_date'] # 'created_at' -> 'created_date'
    list_filter = ['interests', 'created_date'] # 'created_at' -> 'created_date'
    search_fields = ['member__name', 'interests__interestName']
    readonly_fields = ['created_date'] # 'created_at' -> 'created_date'
    list_per_page = 40
    
    def member_name(self, obj):
        """회원 이름"""
        url = reverse('admin:meeting_app_member_change', args=[obj.member.accountID])
        return format_html(
            '<a href="{}">{}</a>',
            url, obj.member.name
        )
    member_name.short_description = '회원명'
    
    def interest_name(self, obj):
        """관심사 이름"""
        url = reverse('admin:meeting_app_interests_change', args=[obj.interests.interestID])
        return format_html(
            '<a href="{}">{}</a>',
            url, obj.interests.interestName
        )
    interest_name.short_description = '관심사'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'member', 'interests'
        )

# 관리자 사이트 커스터마이징
admin.site.site_header = "소모임 관리 시스템"
admin.site.site_title = "소모임 Admin"
admin.site.index_title = "소모임 관리 대시보드"