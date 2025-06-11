# meeting_app/context_processors.py
from django.db.models import Count, Q
from .models import Interests, Class, Member, Post
from django.utils import timezone

def sidebar_data(request):
    """모든 템플릿에서 사용할 전역 컨텍스트 데이터"""
    
    try:
        # 카테고리별 키워드 정의
        categories = {
            'sports': ['테니스', '배드민턴', '축구', '농구', '야구', '수영', '요가', '헬스', '등산'],
            'study': ['영어', '중국어', '일본어', 'Java', 'Python', '토익', '프로그래밍', '경제'],
            'hobby': ['요리', '베이킹', '커피', '와인', '여행', '게임', '쇼핑'],
            'culture': ['영화', '연극', '뮤지컬', '음악', '미술', '사진'],
            'lifestyle': ['반려동물', '원예', '인테리어', '명상', '힐링']
        }
        
        # 각 카테고리별 관심사 조회
        sidebar_interests = {}
        for category, keywords in categories.items():
            # Q 객체로 OR 조건 생성
            filter_q = Q()
            for keyword in keywords:
                filter_q |= Q(interestName__icontains=keyword)
            
            interests = Interests.objects.filter(filter_q).annotate(
                class_count=Count('classes', distinct=True)
            ).filter(class_count__gt=0).order_by('-class_count')[:5]
            
            sidebar_interests[f'sidebar_{category}_interests'] = interests
        
        # 전체 통계
        stats = {
            'sidebar_total_interests': Interests.objects.count(),
            'sidebar_total_classes': Class.objects.count(),
            'sidebar_total_members': Member.objects.count(),
            'sidebar_active_classes': Class.objects.filter(
                classStartDate__lte=timezone.now().date(),
                classEndDate__gte=timezone.now().date()
            ).count()
        }
        
        # 최근 인기 게시글
        recent_posts = Post.objects.select_related(
            'author', 'class_classID'
        ).order_by('-views', '-writeDate')[:5]
        
        # 사용자 정보 (로그인된 경우)
        user_info = {}
        if 'member_id' in request.session:
            try:
                member = Member.objects.get(accountID=request.session['member_id'])
                user_info = {
                    'user_name': member.name,
                    'user_type': member.get_accountType_display(),
                    'user_id': member.accountID,
                }
            except Member.DoesNotExist:
                pass
        
        # 모든 데이터 병합
        context = {
            **sidebar_interests,
            **stats,
            'sidebar_recent_posts': recent_posts,
            **user_info,
        }
        
        return context
        
    except Exception as e:
        # 오류 발생 시 빈 데이터 반환
        print(f"Context processor error: {e}")
        return {
            'sidebar_sports_interests': [],
            'sidebar_study_interests': [],
            'sidebar_hobby_interests': [],
            'sidebar_culture_interests': [],
            'sidebar_lifestyle_interests': [],
            'sidebar_total_interests': 0,
            'sidebar_total_classes': 0,
            'sidebar_total_members': 0,
            'sidebar_active_classes': 0,
            'sidebar_recent_posts': [],
        }