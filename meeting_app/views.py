# meeting_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.db import transaction
from .models import *
from .forms import *
import json
import hashlib
from datetime import date, timedelta

def 클래스검색및신청(request):
    """메인 페이지 - 클래스 검색 및 신청"""
    try:
        # 검색 폼 처리
        form = ClassSearchForm(request.GET or None)
        
        # 기본 쿼리셋 (최적화된 쿼리)
        classes = Class.objects.select_related('interestID', 'instructor').prefetch_related(
            'sugang_set__member_accountID'
        ).annotate(
            member_count=Count('sugang_set', distinct=True)
        )
        
        # 카테고리별 필터링
        category = request.GET.get('category', 'all')
        
        if category != 'all':
            category_mapping = {
                'sports': ['테니스', '배드민턴', '축구', '농구', '야구', '배구', '수영', '요가', '필라테스', '헬스', '등산'],
                'study': ['영어', '중국어', '일본어', 'Java', 'Python', '토익', '토플', '독서', '프로그래밍', '투자', '경제'],
                'hobby': ['요리', '베이킹', '커피', '와인', '여행', '게임', '쇼핑', '패션'],
                'culture': ['영화', '연극', '뮤지컬', '콘서트', '음악', '미술', '사진', '전시회'],
                'lifestyle': ['반려동물', '원예', '인테리어', '명상', '힐링', '아로마']
            }
            
            if category in category_mapping:
                keywords = category_mapping[category]
                interest_filter = Q()
                for keyword in keywords:
                    interest_filter |= Q(interestID__interestName__icontains=keyword)
                classes = classes.filter(interest_filter)
        
        # 검색 기능
        if form.is_valid():
            keyword = form.cleaned_data.get('keyword')
            interest = form.cleaned_data.get('interest')
            
            if keyword:
                classes = classes.filter(
                    Q(className__icontains=keyword) |
                    Q(classDescription__icontains=keyword) |
                    Q(interestID__interestName__icontains=keyword)
                ).distinct()
            
            if interest:
                classes = classes.filter(interestID=interest)
        
        # 정렬
        sort_by = request.GET.get('sort', 'recent')
        if sort_by == 'popular':
            classes = classes.order_by('-member_count', '-created_at')
        elif sort_by == 'name':
            classes = classes.order_by('className')
        elif sort_by == 'date':
            classes = classes.order_by('classStartDate')
        else:  # recent
            classes = classes.order_by('-created_at')
        
        # 페이지네이션
        paginator = Paginator(classes, 12)
        page_number = request.GET.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # 통계 데이터
        stats = {
            'total_classes': Class.objects.count(),
            'total_members': Member.objects.count(),
            'total_interests': Interests.objects.count(),
            'total_participants': Sugang.objects.values('member_accountID').distinct().count(),
            'active_classes': Class.objects.filter(
                classStartDate__lte=timezone.now().date(),
                classEndDate__gte=timezone.now().date()
            ).count()
        }
        
        # 인기 관심사 (클래스가 있는 것만)
        popular_interests = Interests.objects.annotate(
            class_count=Count('classes', distinct=True)
        ).filter(class_count__gt=0).order_by('-class_count')[:8]
        
        # 최근 게시글
        recent_posts = Post.objects.select_related('author', 'class_classID').order_by('-writeDate')[:5]
        
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
        print(f"Error in 클래스검색및신청: {e}")
        messages.error(request, '페이지를 불러오는 중 오류가 발생했습니다.')
        
        # 기본 빈 컨텍스트로 렌더링
        context = {
            'form': ClassSearchForm(),
            'classes': [],
            'current_category': 'all',
            'current_sort': 'recent',
            'stats': {'total_classes': 0, 'total_members': 0, 'total_interests': 0, 'total_participants': 0, 'active_classes': 0},
            'popular_interests': [],
            'recent_posts': [],
        }
        return render(request, 'class_search.html', context)

def 로그인(request):
    """로그인 처리"""
    if request.method == 'POST':
        account_id = request.POST.get('accountID', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not account_id or not password:
            messages.error(request, '아이디와 비밀번호를 모두 입력해주세요.')
            return render(request, 'login.html')
        
        try:
            # 비밀번호 해싱 후 비교
            hashed_password = f"hashed_{hashlib.md5(password.encode()).hexdigest()}"
            member = Member.objects.get(accountID=account_id, password=hashed_password)
            
            # 세션 설정
            request.session['member_id'] = member.accountID
            request.session['member_name'] = member.name
            request.session['account_type'] = member.accountType
            
            messages.success(request, f'{member.name}님 환영합니다!')
            
            # 다음 페이지로 리다이렉트
            next_url = request.GET.get('next', 'classes')
            return redirect(next_url)
            
        except Member.DoesNotExist:
            messages.error(request, '아이디 또는 비밀번호가 잘못되었습니다.')
        except Exception as e:
            print(f"Login error: {e}")
            messages.error(request, '로그인 중 오류가 발생했습니다.')
    
    return render(request, 'login.html')

def 로그아웃(request):
    """로그아웃 처리"""
    try:
        # 세션 데이터 삭제
        if 'member_id' in request.session:
            del request.session['member_id']
        if 'member_name' in request.session:
            del request.session['member_name']
        if 'account_type' in request.session:
            del request.session['account_type']
        
        request.session.flush()  # 모든 세션 데이터 삭제
        messages.success(request, '로그아웃되었습니다.')
    except Exception as e:
        print(f"Logout error: {e}")
        messages.info(request, '로그아웃되었습니다.')
    
    return redirect('login')

def 회원가입(request):
    """회원가입 처리"""
    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 이메일 중복 확인
                    email = form.cleaned_data['email']
                    if Member.objects.filter(email=email).exists():
                        messages.error(request, '이미 사용 중인 이메일입니다.')
                        return render(request, 'register.html', {'form': form})
                    
                    # 회원 생성
                    member = form.save()
                    messages.success(request, f'{member.name}님, 회원가입이 완료되었습니다!')
                    return redirect('login')
                    
            except Exception as e:
                print(f"Registration error: {e}")
                messages.error(request, '회원가입 중 오류가 발생했습니다. 다시 시도해주세요.')
        else:
            # 폼 유효성 검사 오류
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = MemberRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def 마이페이지(request):
    """마이페이지"""
    if 'member_id' not in request.session:
        messages.warning(request, '로그인이 필요합니다.')
        return redirect('login')
    
    try:
        member = get_object_or_404(Member, accountID=request.session['member_id'])
        
        # 사용자 관련 데이터 조회 (최적화된 쿼리)
        신청클래스들 = Sugang.objects.filter(
            member_accountID=member,
            is_active=True
        ).select_related('class_classID', 'class_classID__interestID').order_by('-registration_date')
        
        작성게시글들 = Post.objects.filter(
            author=member
        ).select_related('class_classID').order_by('-writeDate')[:10]
        
        관심사들 = MemberInterests.objects.filter(
            member=member
        ).select_related('interests').order_by('-created_at')
        
        # 출석 통계
        출석이력 = Attendance.objects.filter(
            sugang_sugangID__member_accountID=member
        ).select_related(
            'sugang_sugangID__class_classID'
        ).order_by('-attendDate')[:20]
        
        # 출석률 계산
        총출석 = 출석이력.filter(attendanceStatus='present').count()
        총수업 = 출석이력.count()
        출석률 = round((총출석 / 총수업 * 100), 1) if 총수업 > 0 else 0
        
        # 활동 통계
        활동통계 = {
            '참여모임': 신청클래스들.count(),
            '작성게시글': 작성게시글들.count(),
            '관심사': 관심사들.count(),
            '출석률': 출석률,
        }
        
        context = {
            'member': member,
            '신청클래스들': 신청클래스들,
            '작성게시글들': 작성게시글들,
            '관심사들': 관심사들,
            '출석이력': 출석이력,
            '활동통계': 활동통계,
        }
        
        return render(request, 'mypage.html', context)
        
    except Exception as e:
        print(f"Error in 마이페이지: {e}")
        messages.error(request, '마이페이지를 불러오는 중 오류가 발생했습니다.')
        return redirect('classes')

@require_POST
@csrf_exempt
def 클래스신청(request, class_id):
    """클래스 신청 처리 (AJAX)"""
    if 'member_id' not in request.session:
        return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})
    
    try:
        with transaction.atomic():
            member = get_object_or_404(Member, accountID=request.session['member_id'])
            클래스 = get_object_or_404(Class, classID=class_id)
            
            # 정원 확인
            if 클래스.is_full:
                return JsonResponse({'success': False, 'message': '정원이 마감된 클래스입니다.'})
            
            # 이미 신청했는지 확인
            if Sugang.objects.filter(member_accountID=member, class_classID=클래스, is_active=True).exists():
                return JsonResponse({'success': False, 'message': '이미 신청한 클래스입니다.'})
            
            # 수강 신청
            sugang = Sugang.objects.create(
                member_accountID=member, 
                class_classID=클래스,
                is_active=True
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'"{클래스.className}" 클래스 신청이 완료되었습니다.',
                'new_member_count': 클래스.member_count + 1
            })
    
    except Exception as e:
        print(f"Error in 클래스신청: {e}")
        return JsonResponse({'success': False, 'message': f'신청 중 오류가 발생했습니다: {str(e)}'})

def 게시글목록(request, class_id):
    """게시글 목록"""
    try:
        클래스 = get_object_or_404(Class, classID=class_id)
        
        # 카테고리 필터
        category = request.GET.get('category', 'all')
        게시글들 = Post.objects.filter(class_classID=클래스).select_related('author')
        
        if category != 'all':
            게시글들 = 게시글들.filter(category=category)
        
        # 검색
        search = request.GET.get('search', '').strip()
        if search:
            게시글들 = 게시글들.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        
        게시글들 = 게시글들.order_by('-is_pinned', '-writeDate')
        
        # 페이지네이션
        paginator = Paginator(게시글들, 15)
        page_number = request.GET.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # 카테고리별 게시글 수
        category_counts = {
            'all': Post.objects.filter(class_classID=클래스).count(),
            'notice': Post.objects.filter(class_classID=클래스, category='notice').count(),
            'general': Post.objects.filter(class_classID=클래스, category='general').count(),
            'review': Post.objects.filter(class_classID=클래스, category='review').count(),
            'question': Post.objects.filter(class_classID=클래스, category='question').count(),
        }
        
        # 사용자가 이 클래스에 참여 중인지 확인
        is_member = False
        if 'member_id' in request.session:
            is_member = Sugang.objects.filter(
                member_accountID__accountID=request.session['member_id'],
                class_classID=클래스,
                is_active=True
            ).exists()
        
        context = {
            'class': 클래스,
            '게시글들': page_obj,
            'current_category': category,
            'search': search,
            'category_counts': category_counts,
            'is_member': is_member,
        }
        
        return render(request, 'post_list.html', context)
        
    except Exception as e:
        print(f"Error in 게시글목록: {e}")
        messages.error(request, '게시글 목록을 불러오는 중 오류가 발생했습니다.')
        return redirect('classes')

def 게시글상세(request, post_id):
    """게시글 상세보기"""
    try:
        게시글 = get_object_or_404(Post, postID=post_id)
        
        # 조회수 증가
        게시글.increment_views()
        
        # 사용자가 이 클래스에 참여 중인지 확인
        is_member = False
        is_author = False
        if 'member_id' in request.session:
            is_member = Sugang.objects.filter(
                member_accountID__accountID=request.session['member_id'],
                class_classID=게시글.class_classID,
                is_active=True
            ).exists()
            is_author = 게시글.author.accountID == request.session['member_id']
        
        # 이전/다음 게시글
        prev_post = Post.objects.filter(
            class_classID=게시글.class_classID,
            writeDate__lt=게시글.writeDate
        ).order_by('-writeDate').first()
        
        next_post = Post.objects.filter(
            class_classID=게시글.class_classID,
            writeDate__gt=게시글.writeDate
        ).order_by('writeDate').first()
        
        context = {
            '게시글': 게시글,
            'is_member': is_member,
            'is_author': is_author,
            'prev_post': prev_post,
            'next_post': next_post,
        }
        
        return render(request, 'post_detail.html', context)
        
    except Exception as e:
        print(f"Error in 게시글상세: {e}")
        messages.error(request, '게시글을 불러오는 중 오류가 발생했습니다.')
        return redirect('classes')

@require_http_methods(["GET", "POST"])
def 게시글작성(request, class_id):
    """게시글 작성"""
    if 'member_id' not in request.session:
        messages.error(request, '로그인이 필요합니다.')
        return redirect('login')
    
    try:
        클래스 = get_object_or_404(Class, classID=class_id)
        member = get_object_or_404(Member, accountID=request.session['member_id'])
        
        # 클래스 참여 여부 확인
        if not Sugang.objects.filter(
            member_accountID=member, 
            class_classID=클래스, 
            is_active=True
        ).exists():
            messages.error(request, '이 클래스에 참여한 회원만 게시글을 작성할 수 있습니다.')
            return redirect('post_list', class_id=class_id)
        
        if request.method == 'POST':
            form = PostForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        post = form.save(commit=False)
                        post.class_classID = 클래스
                        post.author = member
                        post.save()
                        
                        messages.success(request, '게시글이 작성되었습니다.')
                        return redirect('post_detail', post_id=post.postID)
                        
                except Exception as e:
                    print(f"Post creation error: {e}")
                    messages.error(request, '게시글 작성 중 오류가 발생했습니다.')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
        else:
            form = PostForm()
        
        context = {
            'form': form,
            'class': 클래스,
        }
        
        return render(request, 'post_create.html', context)
        
    except Exception as e:
        print(f"Error in 게시글작성: {e}")
        messages.error(request, '게시글 작성 페이지를 불러오는 중 오류가 발생했습니다.')
        return redirect('post_list', class_id=class_id)

def 출석체크(request, class_id):
    """출석 체크"""
    if 'member_id' not in request.session:
        messages.error(request, '로그인이 필요합니다.')
        return redirect('login')
    
    try:
        클래스 = get_object_or_404(Class, classID=class_id)
        member = get_object_or_404(Member, accountID=request.session['member_id'])
        
        # 강사 또는 관리자만 접근 가능
        if member.accountType not in ['instructor', 'admin'] and 클래스.instructor != member:
            messages.error(request, '출석 체크 권한이 없습니다.')
            return redirect('post_list', class_id=class_id)
        
        # 수강생 목록
        수강생들 = Sugang.objects.filter(
            class_classID=클래스, 
            is_active=True
        ).select_related('member_accountID').order_by('member_accountID__name')
        
        if request.method == 'POST':
            attend_date = request.POST.get('attend_date')
            if not attend_date:
                messages.error(request, '출석일을 선택해주세요.')
                return redirect('attendance', class_id=class_id)
            
            try:
                with transaction.atomic():
                    # 기존 출석 기록 삭제
                    Attendance.objects.filter(
                        sugang_sugangID__class_classID=클래스,
                        attendDate=attend_date
                    ).delete()
                    
                    # 새로운 출석 기록 생성
                    for 수강생 in 수강생들:
                        status = request.POST.get(f'attendance_{수강생.sugangID}')
                        if status:
                            Attendance.objects.create(
                                sugang_sugangID=수강생,
                                attendDate=attend_date,
                                attendanceStatus=status
                            )
                    
                    messages.success(request, f'{attend_date} 출석이 저장되었습니다.')
                    
            except Exception as e:
                print(f"Attendance save error: {e}")
                messages.error(request, '출석 저장 중 오류가 발생했습니다.')
        
        # 최근 출석 기록
        recent_attendance = Attendance.objects.filter(
            sugang_sugangID__class_classID=클래스
        ).select_related('sugang_sugangID__member_accountID').order_by('-attendDate')[:50]
        
        context = {
            'class': 클래스,
            '수강생들': 수강생들,
            'recent_attendance': recent_attendance,
            'today': timezone.now().date(),
        }
        
        return render(request, 'attendance.html', context)
        
    except Exception as e:
        print(f"Error in 출석체크: {e}")
        messages.error(request, '출석 체크 페이지를 불러오는 중 오류가 발생했습니다.')
        return redirect('classes')

def 관심사별_모임(request, interest_id):
    """관심사별 모임 목록"""
    try:
        interest = get_object_or_404(Interests, interestID=interest_id)
        
        classes = Class.objects.filter(
            interestID=interest
        ).select_related('instructor').annotate(
            member_count=Count('sugang_set', distinct=True)
        ).order_by('-member_count', '-created_at')
        
        # 페이지네이션
        paginator = Paginator(classes, 12)
        page_number = request.GET.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        context = {
            'interest': interest,
            'classes': page_obj,
            'total_classes': classes.count(),
        }
        
        return render(request, 'interest_classes.html', context)
        
    except Exception as e:
        print(f"Error in 관심사별_모임: {e}")
        messages.error(request, '관심사별 모임을 불러오는 중 오류가 발생했습니다.')
        return redirect('classes')

# 홈페이지 리다이렉트
def 홈페이지(request):
    """홈페이지 - 클래스 검색으로 리다이렉트"""
    return redirect('classes')

# 404 에러 처리
def 오류페이지(request, exception=None):
    """404 에러 페이지"""
    return render(request, 'error.html', {
        'error_message': '요청하신 페이지를 찾을 수 없습니다.'
    }, status=404)