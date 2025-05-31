 
# meeting_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.클래스검색및신청, name='home'),
    path('login/', views.로그인, name='login'),
    path('logout/', views.로그아웃, name='logout'),
    path('register/', views.회원가입, name='register'),
    path('classes/', views.클래스검색및신청, name='classes'),
    path('classes/<int:class_id>/apply/', views.클래스신청, name='class_apply'),
    path('classes/<int:class_id>/attendance/', views.출석체크, name='attendance'),
    path('classes/<int:class_id>/posts/create/', views.게시글작성, name='post_create'),
    path('classes/<int:class_id>/posts/', views.게시글목록, name='post_list'),
    path('posts/<int:post_id>/', views.게시글상세, name='post_detail'),
    path('mypage/', views.마이페이지, name='mypage'),
    path('interests/<int:interest_id>/', views.관심사별_모임, name='interest_classes'),
]