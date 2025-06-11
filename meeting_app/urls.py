# meeting_app/urls.py
from django.urls import path
from django.views.generic import RedirectView
from . import views

# 앱 이름 설정 (네임스페이스)
app_name = 'meeting_app'

urlpatterns = [
    # 홈페이지 및 기본 라우팅
    path('', views.클래스검색및신청, name='home'),
    path('home/', RedirectView.as_view(pattern_name='meeting_app:classes', permanent=True)),
    
    # 인증 관련
    path('login/', views.로그인, name='login'),
    path('logout/', views.로그아웃, name='logout'),
    path('register/', views.회원가입, name='register'),
    
    # 클래스(모임) 관련
    path('classes/', views.클래스검색및신청, name='classes'),
    path('classes/<int:class_id>/apply/', views.클래스신청, name='class_apply'),
    path('classes/<int:class_id>/attendance/', views.출석체크, name='attendance'),
    path('classes/<int:class_id>/favorite/', views.즐겨찾기_토글, name='class_favorite'),
    
    # 게시글 관련
    path('classes/<int:class_id>/posts/', views.게시글목록, name='post_list'),
    path('classes/<int:class_id>/posts/create/', views.게시글작성, name='post_create'),
    path('posts/<int:post_id>/', views.게시글상세, name='post_detail'),
    
    # 사용자 페이지
    path('mypage/', views.마이페이지, name='mypage'),
    
    # 관심사별 모임
    path('interests/<int:interest_id>/', views.관심사별_모임, name='interest_classes'),
    
    # API 엔드포인트
    path('api/health/', views.상태체크, name='health_check'),
    
    # 리다이렉트 (이전 URL 호환성)
    path('meeting/', RedirectView.as_view(pattern_name='meeting_app:classes', permanent=True)),
    path('board/', RedirectView.as_view(pattern_name='meeting_app:classes', permanent=True)),
]

# 에러 핸들러 (옵션)
handler404 = 'meeting_app.views.오류페이지'
handler500 = 'meeting_app.views.오류페이지'