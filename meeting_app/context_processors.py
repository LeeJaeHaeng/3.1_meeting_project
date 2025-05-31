 
# meeting_app/context_processors.py
from django.db.models import Count, Q
from .models import Interests, Class

def sidebar_data(request):
    """모든 템플릿에서 사용할 사이드바 데이터"""
    
    try:
        # 카테고리별 관심사 필터링 (키워드 기반)
        sports_keywords = ['테니스', '배드민턴', '축구', '농구', '야구', '배구', '수영', '요가', '필라테스', 
                          '헬스', '크로스핏', '러닝', '마라톤', '등산', '트레킹', '클라이밍', '골프', '볼링']
        
        study_keywords = ['영어', '중국어', '일본어', 'Java', 'Python', '토익', '토플', '독서', 
                         '프로그래밍', '투자', '주식', '경제', '스터디', '공부']
        
        hobby_keywords = ['요리', '베이킹', '커피', '와인', '여행', '게임', '카페', '맛집', '쇼핑', '패션']
        
        culture_keywords = ['영화', '연극', '뮤지컬', '콘서트', '음악', '미술', '사진', '전시회', '갤러리']
        
        lifestyle_keywords = ['반려동물', '원예', '인테리어', '명상', '힐링', '아로마', '자원봉사']
        
        # Q 객체를 사용한 필터링 함수
        def create_interest_filter(keywords):
            filter_q = Q()
            for keyword in keywords:
                filter_q |= Q(interestName__icontains=keyword)
            return filter_q
        
        # 카테고리별 관심사 조회 (클래스 수가 있는 것만)
        sports_interests = Interests.objects.filter(
            create_interest_filter(sports_keywords)
        ).annotate(
            class_count=Count('classes', distinct=True)
        ).filter(
            class_count__gt=0
        ).order_by('-class_count')[:5]
        
        study_interests = Interests.objects.filter(
            create_interest_filter(study_keywords)
        ).annotate(
            class_count=Count('classes', distinct=True)
        ).filter(
            class_count__gt=0
        ).order_by('-class_count')[:5]
        
        hobby_interests = Interests.objects.filter(
            create_interest_filter(hobby_keywords)
        ).annotate(
            class_count=Count('classes', distinct=True)
        ).filter(
            class_count__gt=0
        ).order_by('-class_count')[:5]
        
        culture_interests = Interests.objects.filter(
            create_interest_filter(culture_keywords)
        ).annotate(
            class_count=Count('classes', distinct=True)
        ).filter(
            class_count__gt=0
        ).order_by('-class_count')[:5]
        
        lifestyle_interests = Interests.objects.filter(
            create_interest_filter(lifestyle_keywords)
        ).annotate(
            class_count=Count('classes', distinct=True)
        ).filter(
            class_count__gt=0
        ).order_by('-class_count')[:5]
        
        # 전체 통계
        total_interests = Interests.objects.count()
        total_classes = Class.objects.count()
        
        return {
            'sidebar_sports_interests': sports_interests,
            'sidebar_study_interests': study_interests,
            'sidebar_hobby_interests': hobby_interests,
            'sidebar_culture_interests': culture_interests,
            'sidebar_lifestyle_interests': lifestyle_interests,
            'sidebar_total_interests': total_interests,
            'sidebar_total_classes': total_classes,
        }
        
    except Exception as e:
        # 오류 발생 시 빈 데이터 반환
        print(f"Sidebar data error: {e}")
        return {
            'sidebar_sports_interests': [],
            'sidebar_study_interests': [],
            'sidebar_hobby_interests': [],
            'sidebar_culture_interests': [],
            'sidebar_lifestyle_interests': [],
            'sidebar_total_interests': 0,
            'sidebar_total_classes': 0,
        }