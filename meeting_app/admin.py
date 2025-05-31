 
# meeting_app/admin.py
from django.contrib import admin
from .models import *

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['accountID', 'name', 'email', 'accountType', 'joinDate']
    list_filter = ['accountType', 'joinDate']
    search_fields = ['accountID', 'name', 'email']
    readonly_fields = ['joinDate']

@admin.register(Interests)
class InterestsAdmin(admin.ModelAdmin):
    list_display = ['interestID', 'interestName']
    search_fields = ['interestName']

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['classID', 'className', 'interestID', 'classStartDate', 'classEndDate']
    list_filter = ['classStartDate', 'classEndDate', 'interestID']
    search_fields = ['className']
    date_hierarchy = 'classStartDate'

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['postID', 'title', 'category', 'author', 'class_classID', 'writeDate']
    list_filter = ['category', 'writeDate', 'class_classID']
    search_fields = ['title', 'content']
    date_hierarchy = 'writeDate'

@admin.register(Sugang)
class SugangAdmin(admin.ModelAdmin):
    list_display = ['sugangID', 'member_accountID', 'class_classID', 'registration_date']
    list_filter = ['registration_date', 'class_classID']
    search_fields = ['member_accountID__name', 'class_classID__className']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['attendanceID', 'sugang_sugangID', 'attendDate', 'attendanceStatus']
    list_filter = ['attendanceStatus', 'attendDate']
    date_hierarchy = 'attendDate'

@admin.register(MemberInterests)
class MemberInterestsAdmin(admin.ModelAdmin):
    list_display = ['member', 'interests']
    list_filter = ['interests']