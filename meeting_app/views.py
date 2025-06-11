# meeting_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction, connection
from django.core.exceptions import ValidationError
from .models import *
from .forms import *
import json
import logging
import traceback

# 로거 설정
logger = logging.getLogger(__name__)

def 로그인(request):
    """로그인 화면"""
    if request.method == 'POST':
        account_id = request.POST.get('accountID', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not account_id or not password:
            messages.error(request, '아이디와 비밀번호를 모두 입력해주세요.')
            return render(request, 'login.html')
        
        try:
            with transaction.atomic():
                member = Member.objects.select_related().get(
                    accountID=account_id, 
                    password=password
                )
                request.session['member_id'] = member.accountID
                request.session['member_name'] = member.name
                request.session['member_type'] = member.accountType
                
                messages.success(request, f'{member.name}님 환영합니다!')
                
                # 다음 페이지로 리다이렉트 (GET 파라미터 확인)
                next_url = request.GET.get('next', 'meeting_app:classes')
                return redirect(next_url)
                
        except Member.DoesNotExist:
            messages.error(request, '아이디 또는 비밀번호가 잘못되었습니다.')
        except Exception as e:
            logger.error(f"Login error: {e}")
            messages.error(request, '로그인 처리 중 오류가 발생했습니다.')
    
    return render(request, 'login.html')

def 로그아웃(request):
    """로그아웃"""
    try:
        # 세션 정리
        session_keys = ['member_id', 'member_name', 'member_type']
        for key in session_keys:
            if key in request.session:
                del request.session[key]
        
        request.session.flush()  # 전체 세션 삭제
        messages.success(request, '로그아웃되었습니다.')
    except Exception as e:
        logger.error(f"Logout error: {e}")
        messages.error(request, '로그아웃 처리 중 오류가 발생했습니다.')
    
    return redirect('meeting_app:login')

def 회원가입(request):
    """회원 가입 화면"""
    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)
        
        try:
            with transaction.atomic():
                if form.is_valid():
                    # 아이디 중복 확인
                    if Member.objects.filter(accountID=form.cleaned_data['accountID']).exists():
                        messages.error(request, '이미 사용 중인 아이디입니다.')
                        return render(request, 'register.html', {'form': form})
                    
                    # 이메일 중복 확인
                    if Member.objects.filter(email=form.cleaned_data['email']).exists():
                        messages.error(request, '이미 사용 중인 이메일입니다.')
                        return render(request, 'register.html', {'form': form})
                    
                    # 회원 생성
                    member = form.save()
                    messages.success(request, '회원가입이 완료되었습니다. 로그인해주세요.')
                    return redirect('meeting_app:login')
                else:
                    # 폼 에러 메시지 표시
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f'{field}: {error}')
                            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            messages.error(request, '회원가입 처리 중 오류가 발생했습니다.')
    else:
        form = MemberRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def 클래스검색및신청(request):
    """클래스(소모임) 검색 및 신청 화면 - MySQL 최적화 버전"""
    try:
        # 검색 폼
        form = ClassSearchForm(request.GET)
        
        # 기본 쿼리셋 - 최적화된 쿼리 (MySQL 인덱스 활용)
        classes = Class.objects.select_related('interestID').prefetch_related(
            Prefetch(
                'sugang_set',
                queryset=Sugang.objects.select_related('member_accountID')
            )
        ).annotate(
            sugang_count=Count('sugang_set', distinct=True)
        )
        
        # 카테고리별 필터링
        category = request.GET.get('category', 'all')
        
        # 카테고리 매핑 (관심사명 기반) - MySQL에서 효율적인 검색을 위해 개선
        category_filters = {
            'sports': Q(interestID__interestName__in=[
                '테니스', '배드민턴', '축구', '농구', '야구', '배구', '수영', '요가', 
                '필라테스', '헬스', '크로스핏', '러닝', '마라톤', '등산', '트레킹', 
                '클라이밍', '골프', '볼링'
            ]),
            'study': Q(interestID__interestName__in=[
                '영어', '중국어', '일본어', 'Java', 'Python', '토익', '토플', 
                '독서', '프로그래밍', '투자', '주식', '경제', '스터디', '공부'
            ]),
            'hobby': Q(interestID__interestName__in=[
                '요리', '베이킹', '커피', '와인', '여행', '게임', '카페', 
                '맛집', '쇼핑', '패션'
            ]),
            'culture': Q(interestID__interestName__in=[
                '영화', '연극', '뮤지컬', '콘서트', '음악', '미술', '사진', 
                '전시회', '갤러리'
            ]),
            'lifestyle': Q(interestID__interestName__in=[
                '반려동물', '원예', '인테리어', '명상', '힐링', '아로마', '자원봉사'
            ])
        }
        
        if category != 'all' and category in category_filters:
            classes = classes.filter(category_filters[category])
        
        # 검색 기능
        if form.is_valid():
            keyword = form.cleaned_data.get('keyword')
            interest = form.cleaned_data.get('interest')
            
            if keyword:
                # MySQL FULLTEXT 검색 대신 LIKE 검색 사용 (호환성 개선)
                keyword_filter = (
                    Q(className__icontains=keyword) |
                    Q(interestID__interestName__icontains=keyword)
                )
                classes = classes.filter(keyword_filter).distinct()
            
            if interest:
                classes = classes.filter(interestID=interest)
        
        # annotate 이후 values로 필요한 필드만 명시 (MySQL ONLY_FULL_GROUP_BY 에러 방지)
        classes = classes.values(
            'classID', 'className', 'max_members', 'sugang_count', 'classStartDate', 'classEndDate', 'interestID', 'description', 'is_active', 'created_date'
        )
        
        # 정렬 (MySQL 인덱스 최적화 고려)
        sort_by = request.GET.get('sort', 'recent')
        if sort_by == 'popular':
            classes = classes.order_by('-sugang_count', '-classID')
        elif sort_by == 'name':
            classes = classes.order_by('className')
        else:  # recent
            classes = classes.order_by('-classID')
        
        # 페이지네이션 (MySQL에서 LIMIT/OFFSET 최적화)
        paginator = Paginator(classes, 12)
        page_number = request.GET.get('page', 1)
        try:
            page_obj = paginator.get_page(page_number)
        except Exception:
            page_obj = paginator.get_page(1)
        
        # 인기 관심사 (상위 10개) - 서브쿼리 최적화
        popular_interests = Interests.objects.annotate(
            class_count=Count('classes', distinct=True)
        ).filter(class_count__gt=0).order_by('-class_count')[:10]
        
        # 통계 데이터 - 캐시 가능하도록 개선
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM class")
                total_classes = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM member")
                total_members = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM interests")
                total_interests = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(DISTINCT member_accountID_id) FROM sugang")
                total_participants = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Statistics query error: {e}")
            total_classes = Class.objects.count()
            total_members = Member.objects.count()
            total_interests = Interests.objects.count()
            total_participants = Sugang.objects.values('member_accountID').distinct().count()
        # 진행중 모임(예시)
        active_classes = Class.objects.filter(classEndDate__gte=timezone.now().date()).count()
        stats = {
            'total_classes': total_classes,
            'total_members': total_members,
            'total_interests': total_interests,
            'total_participants': total_participants,
            'active_classes': active_classes,
        }
        # 최근 게시글(예시)
        recent_posts = Post.objects.order_by('-writeDate')[:5]
        context = {
            'form': form,
            'classes': page_obj,
            'current_category': category,
            'current_sort': sort_by,
            'stats': stats,
            'popular_interests': popular_interests,
            'recent_posts': recent_posts,
        }
        return render(request, 'class_search.html', context)
    except Exception as e:
        logger.error(f"Error in 클래스검색및신청: {e}")
        messages.error(request, '페이지를 불러오는 중 오류가 발생했습니다.')
        context = {
            'form': ClassSearchForm(),
            'classes': Paginator([], 1).get_page(1),
            'current_category': 'all',
            'current_sort': 'recent',
            'stats': {
                'total_classes': 0,
                'total_members': 0,
                'total_interests': 0,
                'total_participants': 0,
                'active_classes': 0,
            },
            'popular_interests': [],
            'recent_posts': [],
        }
        return render(request, 'class_search.html', context)

@require_POST
@csrf_exempt
def 클래스신청(request, class_id):
    """클래스 신청 처리 - ONLY_FULL_GROUP_BY 문제 최종 해결 시도 (원시 SQL 사용)"""
    if 'member_id' not in request.session:
        return JsonResponse({
            'success': False, 
            'message': '로그인이 필요합니다.',
            'redirect': '/login/'
        })
    
    try:
        with transaction.atomic():
            member = get_object_or_404(Member, accountID=request.session['member_id'])
            
            # 클래스 정보를 필요한 필드만 명시적으로 가져옴 (ONLY_FULL_GROUP_BY 방지)
            try:
                # classStartDate도 추가하여 views.py에서 체크
                클래스_data = Class.objects.values('classID', 'max_members', 'classEndDate', 'classStartDate').get(classID=class_id)
                클래스_id = 클래스_data['classID']
                max_members_limit = 클래스_data['max_members']
                class_end_date = 클래스_data['classEndDate']
                class_start_date = 클래스_data['classStartDate']
            except Class.DoesNotExist:
                return JsonResponse({'success': False, 'message': '존재하지 않는 클래스입니다.'})
            
            # --- 중복 신청 확인 (원시 SQL 사용) ---
            with connection.cursor() as cursor:
                check_sql = """
                    SELECT EXISTS(
                        SELECT 1 FROM sugang
                        WHERE member_accountID_id = %s AND class_classID_id = %s
                    )
                """
                cursor.execute(check_sql, [member.accountID, 클래스_id])
                already_applied = cursor.fetchone()[0]

            if already_applied:
                return JsonResponse({
                    'success': False, 
                    'message': '이미 신청한 클래스입니다.'
                })
            # --- 중복 신청 확인 끝 ---

            # 클래스 기간 확인: 종료일과 시작일 모두 views.py에서 명시적으로 체크
            if class_end_date < timezone.now().date():
                return JsonResponse({
                    'success': False, 
                    'message': '종료된 클래스입니다.'
                })
            
            # 시작일이 오늘이거나 이미 지난 클래스인지 확인
            if class_start_date <= timezone.now().date(): 
                return JsonResponse({
                    'success': False,
                    'message': '이미 시작되었거나 종료된 클래스에는 신청할 수 없습니다.'
                })

            # 정원 초과 체크 (Foreign Key ID 직접 사용)
            current_sugang_count = Sugang.objects.filter(class_classID_id=클래스_id).count()
            if current_sugang_count >= max_members_limit:
                return JsonResponse({
                    'success': False,
                    'message': '정원이 초과되었습니다.'
                })
            
            # --- 수강 신청 (원시 SQL INSERT 사용) ---
            with connection.cursor() as cursor:
                # 현재 세션의 sql_mode를 확인하여 로그로 출력합니다.
                cursor.execute("SELECT @@SESSION.sql_mode")
                current_sql_mode = cursor.fetchone()[0]
                logger.info(f"Current MySQL session sql_mode before INSERT: {current_sql_mode}")

                sql = """
                    INSERT INTO sugang (member_accountID_id, class_classID_id, registration_date, status)
                    VALUES (%s, %s, NOW(), %s)
                """
                cursor.execute(sql, [member.accountID, 클래스_id, 'approved'])
                
                # 삽입된 레코드의 sugangID를 가져옴
                cursor.execute("SELECT LAST_INSERT_ID()")
                sugang_id = cursor.fetchone()[0]

            return JsonResponse({
                'success': True, 
                'message': '클래스 신청이 완료되었습니다.',
                'sugang_id': sugang_id 
            })
    
    except Exception as e:
        logger.error(f"Error in 클래스신청: {e}")
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'message': '오류가 발생했습니다. 다시 시도해주세요.'
        })

def 출석체크(request, class_id):
    """출석 체크 화면 - MySQL 최적화"""
    if 'member_id' not in request.session:
        messages.error(request, '로그인이 필요합니다.')
        return redirect('meeting_app:login')
    
    try:
        클래스 = get_object_or_404(Class, classID=class_id)
        
        # 수강생 목록 조회 (최적화된 쿼리)
        수강생들 = Sugang.objects.filter(
            class_classID=클래스
        ).select_related('member_accountID').order_by('member_accountID__name')
        
        if request.method == 'POST':
            date = request.POST.get('date')
            
            if not date:
                messages.error(request, '출석일을 선택해주세요.')
                return redirect('meeting_app:attendance', class_id=class_id)
            
            try:
                with transaction.atomic():
                    # 기존 출석 데이터 삭제 (중복 방지)
                    Attendance.objects.filter(
                        sugang_sugangID__class_classID=클래스,
                        attendDate=date
                    ).delete()
                    
                    # 새 출석 데이터 생성
                    attendance_records = []
                    for 수강생 in 수강생들:
                        status = request.POST.get(f'attendance_{수강생.sugangID}')
                        if status and status in ['present', 'late', 'absent']:
                            attendance_records.append(
                                Attendance(
                                    sugang_sugangID=수강생,
                                    attendDate=date,
                                    attendanceStatus=status
                                )
                            )
                    
                    # 벌크 생성으로 성능 최적화
                    if attendance_records:
                        Attendance.objects.bulk_create(attendance_records)
                        messages.success(request, f'{len(attendance_records)}명의 출석이 저장되었습니다.')
                    else:
                        messages.warning(request, '저장된 출석 정보가 없습니다.')
                
                return redirect('meeting_app:attendance', class_id=class_id)
                
            except Exception as e:
                logger.error(f"Attendance save error: {e}")
                messages.error(request, '출석 저장 중 오류가 발생했습니다.')
        
        return render(request, 'attendance.html', {
            'class': 클래스,
            '수강생들': 수강생들
        })
        
    except Exception as e:
        logger.error(f"Error in 출석체크: {e}")
        messages.error(request, '출석 체크 페이지를 불러오는 중 오류가 발생했습니다.')
        return redirect('meeting_app:classes')

def 게시글작성(request, class_id):
    """게시글 작성 화면 - 유효성 검사 강화"""
    if 'member_id' not in request.session:
        messages.error(request, '로그인이 필요합니다.')
        return redirect('meeting_app:login')
    
    try:
        클래스 = get_object_or_404(Class, classID=class_id)
        member = get_object_or_404(Member, accountID=request.session['member_id'])
        
        # 수강 여부 확인 (선택사항)
        is_enrolled = Sugang.objects.filter(
            member_accountID=member,
            class_classID=클래스
        ).exists()
        
        if request.method == 'POST':
            form = PostForm(request.POST)
            
            try:
                with transaction.atomic():
                    if form.is_valid():
                        post = form.save(commit=False)
                        post.class_classID = 클래스
                        post.author = member
                        post.save()
                        
                        messages.success(request, '게시글이 작성되었습니다.')
                        return redirect('meeting_app:post_list', class_id=class_id)
                    else:
                        # 폼 에러를 개별적으로 표시
                        for field, errors in form.errors.items():
                            for error in errors:
                                messages.error(request, f'{form[field].label}: {error}')
                                
            except Exception as e:
                logger.error(f"Post creation error: {e}")
                messages.error(request, '게시글 작성 중 오류가 발생했습니다.')
        else:
            form = PostForm()
        
        return render(request, 'post_create.html', {
            'form': form,
            'class': 클래스,
            'is_enrolled': is_enrolled
        })
        
    except Exception as e:
        logger.error(f"Error in 게시글작성: {e}")
        messages.error(request, '게시글 작성 페이지를 불러오는 중 오류가 발생했습니다.')
        return redirect('meeting_app:classes')

def 마이페이지(request):
    """마이페이지 화면 - 쿼리 최적화"""
    if 'member_id' not in request.session:
        messages.warning(request, '로그인이 필요합니다.')
        return redirect('meeting_app:login')
    
    try:
        member = get_object_or_404(Member, accountID=request.session['member_id'])
        
        # 관련 데이터 조회 (최적화된 쿼리)
        신청클래스들 = Sugang.objects.filter(
            member_accountID=member
        ).select_related('class_classID', 'class_classID__interestID').order_by('-registration_date')
        
        작성게시글들 = Post.objects.filter(
            author=member
        ).select_related('class_classID').order_by('-writeDate')[:10]
        
        관심사들 = MemberInterests.objects.filter(
            member=member
        ).select_related('interests')
        
        출석이력 = Attendance.objects.filter(
            sugang_sugangID__member_accountID=member
        ).select_related(
            'sugang_sugangID__class_classID'
        ).order_by('-attendDate')[:20]
        
        # 활동통계 추가
        활동통계 = {
            '참여모임': 신청클래스들.count(),
            '작성게시글': 작성게시글들.count(),
            '관심사': 관심사들.count(),
            '출석률': int((출석이력.filter(attendanceStatus='present').count() / 출석이력.count()) * 100) if 출석이력.count() > 0 else 0
        }
        return render(request, 'mypage.html', {
            'member': member,
            '신청클래스들': 신청클래스들,
            '작성게시글들': 작성게시글들,
            '관심사들': 관심사들,
            '출석이력': 출석이력,
            '활동통계': 활동통계
        })
        
    except Exception as e:
        logger.error(f"Error in 마이페이지: {e}")
        messages.error(request, '마이페이지를 불러오는 중 오류가 발생했습니다.')
        return redirect('meeting_app:classes')

def 게시글목록(request, class_id):
    """게시글 목록 보기 화면 - 페이지네이션 최적화"""
    try:
        클래스 = get_object_or_404(Class, classID=class_id)
        
        # 게시글 조회 (카테고리별 정렬: 공지 -> 후기 -> 일반)
        게시글들 = Post.objects.filter(
            class_classID=클래스
        ).select_related('author').order_by(
            # 공지사항을 맨 위로
            'category',
            '-writeDate'
        )
        
        # 페이지네이션
        paginator = Paginator(게시글들, 10)
        page_number = request.GET.get('page', 1)
        try:
            page_obj = paginator.get_page(page_number)
        except Exception:
            page_obj = paginator.get_page(1)
        
        return render(request, 'post_list.html', {
            'class': 클래스,
            '게시글들': page_obj
        })
        
    except Exception as e:
        logger.error(f"Error in 게시글목록: {e}")
        messages.error(request, '게시글 목록을 불러오는 중 오류가 발생했습니다.')
        return redirect('meeting_app:classes')

def 게시글상세(request, post_id):
    """게시글 상세 보기 - 조회수 증가 기능 추가 가능"""
    try:
        게시글 = get_object_or_404(
            Post.objects.select_related('author', 'class_classID'),
            postID=post_id
        )
        
        return render(request, 'post_detail.html', {
            '게시글': 게시글
        })
        
    except Exception as e:
        logger.error(f"Error in 게시글상세: {e}")
        messages.error(request, '게시글을 불러오는 중 오류가 발생했습니다.')
        return redirect('meeting_app:classes')

def 관심사별_모임(request, interest_id):
    """특정 관심사의 모임 목록 - 최적화된 쿼리"""
    try:
        interest = get_object_or_404(Interests, interestID=interest_id)
        
        classes = Class.objects.filter(
            interestID=interest
        ).annotate(
            sugang_count=Count('sugang_set', distinct=True)
        ).order_by('-sugang_count', '-classID')
        
        # 페이지네이션
        paginator = Paginator(classes, 12)
        page_number = request.GET.get('page', 1)
        try:
            page_obj = paginator.get_page(page_number)
        except Exception:
            page_obj = paginator.get_page(1)
        
        return render(request, 'interest_classes.html', {
            'interest': interest,
            'classes': page_obj
        })
        
    except Exception as e:
        logger.error(f"Error in 관심사별_모임: {e}")
        messages.error(request, '관심사별 모임을 불러오는 중 오류가 발생했습니다.')
        return redirect('meeting_app:classes')

# 추가 유틸리티 뷰
def 홈페이지(request):
    """홈페이지 - 클래스 검색으로 리다이렉트"""
    return redirect('meeting_app:classes')

def 오류페이지(request, exception=None):
    """오류 페이지"""
    context = {
        'error_message': '페이지를 찾을 수 없습니다.'
    }
    return render(request, 'error.html', context, status=404)

# API 엔드포인트 (AJAX 요청용)
@require_POST
@csrf_exempt 
def 즐겨찾기_토글(request, class_id):
    """즐겨찾기 토글 API (향후 구현)"""
    if 'member_id' not in request.session:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        # 즐겨찾기 기능 구현 예정
        return JsonResponse({
            'success': True, 
            'favorited': False,
            'message': '즐겨찾기 기능은 준비 중입니다.'
        })
    except Exception as e:
        logger.error(f"Favorite toggle error: {e}")
        return JsonResponse({'success': False, 'message': '오류가 발생했습니다.'})

# 상태 체크 뷰 (헬스체크용)
def 상태체크(request):
    """애플리케이션 상태 체크"""
    try:
        # 데이터베이스 연결 확인
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'error',
            'database': 'disconnected',
            'error': str(e)
        }, status=500)