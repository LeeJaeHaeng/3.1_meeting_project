# meeting_app/context_processors.py
from django.db.models import Count, Q
from .models import Interests, Class, Member, Sugang

def sidebar_data(request):
    """모든 템플릿에서 사용할 사이드바 데이터"""
    
    try:
        print("=== DEBUG: context_processors sidebar_data 시작 ===")
        
        # 카테고리별 관심사 필터링 키워드
        sports_keywords = ['테니스', '배드민턴', '축구', '농구', '야구', '배구', '수영', '요가', '필라테스', 
                          '헬스', '크로스핏', '러닝', '마라톤', '등산', '트레킹', '클라이밍', '골프', '볼링']
        
        study_keywords = ['영어', '중국어', '일본어', 'Java', 'Python', '토익', '토플', '독서', 
                         '프로그래밍', '투자', '주식', '경제', '스터디', '공부']
        
        hobby_keywords = ['요리', '베이킹', '커피', '와인', '여행', '게임', '카페', '맛집', '쇼핑', '패션']
        
        # Q 객체를 사용한 필터링 함수
        def create_interest_filter(keywords):
            filter_q = Q()
            for keyword in keywords:
                filter_q |= Q(interestName__icontains=keyword)
            return filter_q
        
        # 전체 통계 먼저 계산
        total_interests = Interests.objects.count()
        total_classes = Class.objects.count()
        
        print(f"DEBUG: 전체 통계 - 관심사: {total_interests}, 클래스: {total_classes}")
        
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
        
        print(f"DEBUG: 카테고리별 관심사 수 - 스포츠: {sports_interests.count()}, 스터디: {study_interests.count()}, 취미: {hobby_interests.count()}")
        
        result = {
            'sidebar_sports_interests': sports_interests,
            'sidebar_study_interests': study_interests,
            'sidebar_hobby_interests': hobby_interests,
            'sidebar_culture_interests': [],  # 일단 빈 배열
            'sidebar_lifestyle_interests': [],  # 일단 빈 배열
            'sidebar_total_interests': total_interests,
            'sidebar_total_classes': total_classes,
        }
        
        print(f"DEBUG: context_processors 결과 반환")
        return result
        
    except Exception as e:
        print(f"DEBUG: Sidebar data error: {e}")
        import traceback
        traceback.print_exc()
        
        # 오류 발생 시 기본값 반환
        return {
            'sidebar_sports_interests': [],
            'sidebar_study_interests': [],
            'sidebar_hobby_interests': [],
            'sidebar_culture_interests': [],
            'sidebar_lifestyle_interests': [],
            'sidebar_total_interests': 0,
            'sidebar_total_classes': 0,
        }