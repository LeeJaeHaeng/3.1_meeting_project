# meeting_app/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import date, timedelta
import random
import logging
from meeting_app.models import *

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'MySQL 데이터베이스용 샘플 데이터를 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--members',
            type=int,
            default=30,
            help='생성할 회원 수 (기본값: 30)'
        )
        parser.add_argument(
            '--classes',
            type=int,
            default=50,
            help='생성할 클래스 수 (기본값: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='기존 데이터 삭제 후 생성'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('MySQL 샘플 데이터 생성을 시작합니다...')
        )

        try:
            with transaction.atomic():
                if options['clear']:
                    self.clear_existing_data()
                
                # 1. 관심사 데이터 생성
                self.create_interests()
                
                # 2. 샘플 회원 생성
                self.create_members(options['members'])
                
                # 3. 샘플 클래스 생성
                self.create_classes(options['classes'])
                
                # 4. 수강신청 데이터 생성
                self.create_sugang()
                
                # 5. 회원관심사 데이터 생성
                self.create_member_interests()
                
                # 6. 게시글 데이터 생성
                self.create_posts()
                
                # 7. 출석 데이터 생성
                self.create_attendance()

            self.display_summary()
            self.stdout.write(
                self.style.SUCCESS('✅ MySQL 샘플 데이터 생성이 완료되었습니다!')
            )
            
        except Exception as e:
            logger.error(f"Sample data creation error: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'❌ 오류 발생: {str(e)}')
            )

    def clear_existing_data(self):
        """기존 데이터 삭제 (외래키 순서 고려)"""
        self.stdout.write('🗑️  기존 데이터 삭제 중...')
        
        # 외래키 의존성 순서대로 삭제
        Attendance.objects.all().delete()
        Post.objects.all().delete()
        Sugang.objects.all().delete()
        MemberInterests.objects.all().delete()
        Class.objects.all().delete()
        Member.objects.all().delete()
        Interests.objects.all().delete()
        
        self.stdout.write('✅ 기존 데이터 삭제 완료')

    def create_interests(self):
        """관심사 생성"""
        self.stdout.write('📝 관심사 데이터 생성 중...')
        
        interests_data = [
            # 운동/스포츠 (15개)
            '테니스', '배드민턴', '축구', '농구', '야구', '배구', '수영', '요가', 
            '필라테스', '헬스', '크로스핏', '러닝', '마라톤', '등산', '트레킹',
            
            # 스터디 (12개)
            '영어회화', '중국어', '일본어', 'Java', 'Python', 'JavaScript',
            '토익', '토플', '독서', '투자', '주식', '경제',
            
            # 취미/여가 (10개)
            '요리', '베이킹', '커피', '와인', '여행', '게임', 
            '카페투어', '맛집탐방', '쇼핑', '패션',
            
            # 문화/예술 (8개)
            '영화감상', '연극관람', '뮤지컬', '콘서트', '음악', 
            '미술', '사진촬영', '전시회',
            
            # 라이프스타일 (5개)
            '반려동물', '원예', '인테리어', '명상', '힐링'
        ]
        
        created_count = 0
        for interest_name in interests_data:
            interest, created = Interests.objects.get_or_create(
                interestName=interest_name
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ➕ 관심사 생성: {interest_name}')
        
        self.stdout.write(f'✅ 총 {created_count}개의 관심사가 생성되었습니다.')

    def create_members(self, count):
        """회원 생성"""
        self.stdout.write(f'👥 {count}명의 회원 데이터 생성 중...')
        
        first_names = [
            '김민수', '이영희', '박철수', '최지현', '정다영', '강민재', '윤서연',
            '임태현', '한예진', '조성민', '신미경', '오준혁', '배수지', '노현우',
            '송가영', '홍정우', '권나연', '서동혁', '이수빈', '장민호', '유지훈',
            '김하은', '이준서', '박시우', '최서윤', '정예준', '강하율', '윤도윤',
            '임서현', '한지민'
        ]
        
        last_names = ['김', '이', '박', '최', '정', '강', '윤', '임', '한', '조', 
                     '신', '오', '배', '노', '송', '홍', '권', '서', '유', '문']
        
        domains = ['gmail.com', 'naver.com', 'daum.net', 'kakao.com', 'hanmail.net']
        account_types = ['student', 'instructor', 'admin']
        weights = [0.8, 0.15, 0.05]  # 학생 80%, 강사 15%, 관리자 5%
        
        created_count = 0
        for i in range(count):
            # 고유한 계정ID 생성
            base_id = f'user{i+1:03d}'
            account_id = base_id
            counter = 1
            while Member.objects.filter(accountID=account_id).exists():
                account_id = f'{base_id}_{counter}'
                counter += 1
            
            # 랜덤 이름 생성
            if i < len(first_names):
                name = first_names[i]
            else:
                name = f"{random.choice(last_names)}{random.choice(['민수', '영희', '철수', '지현', '다영', '준호', '서연', '태현', '예진', '성민'])}"
            
            # 고유한 이메일 생성
            email_base = account_id
            email = f'{email_base}@{random.choice(domains)}'
            counter = 1
            while Member.objects.filter(email=email).exists():
                email = f'{email_base}_{counter}@{random.choice(domains)}'
                counter += 1
            
            # 전화번호 생성
            phone = f'010-{random.randint(1000,9999)}-{random.randint(1000,9999)}'
            
            # 생년월일 생성 (1980-2005년)
            birth_year = random.randint(1980, 2005)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)
            birth_date = date(birth_year, birth_month, birth_day)
            
            # 계정 타입 선택 (가중치 적용)
            account_type = random.choices(account_types, weights=weights)[0]
            
            try:
                member = Member.objects.create(
                    accountID=account_id,
                    password='password123',  # 실제 운영시에는 해시화 필요
                    accountType=account_type,
                    name=name,
                    phoneNum=phone,
                    email=email,
                    birth=birth_date
                )
                
                created_count += 1
                self.stdout.write(f'  ➕ 회원 생성: {account_id} ({name}, {account_type})')
                
            except Exception as e:
                self.stdout.write(f'  ❌ 회원 생성 실패 {account_id}: {str(e)}')
        
        self.stdout.write(f'✅ 총 {created_count}명의 회원이 생성되었습니다.')

    def create_classes(self, count):
        """클래스 생성"""
        self.stdout.write(f'🏫 {count}개의 클래스 데이터 생성 중...')
        
        class_templates = [
            '초보자를 위한 {}', '주말 {} 모임', '{}를 함께해요', '재미있는 {}',
            '아침 {} 클럽', '저녁 {} 동호회', '{} 정기모임', '{} 스터디',
            '강남 {} 동호회', '홍대 {} 모임', '신촌 {} 클럽', '이태원 {}',
            '강북 {} 그룹', '{}로 시작하는 하루', '즐거운 {} 시간',
            '{}와 함께하는 여가', '프리미엄 {}', '베이직 {}', '어드밴스드 {}'
        ]
        
        locations = ['강남', '홍대', '신촌', '이태원', '강북', '서초', '잠실', '건대', '명동']
        
        interests = list(Interests.objects.all())
        if not interests:
            self.stdout.write('❌ 관심사가 없습니다. 먼저 관심사를 생성하세요.')
            return
        
        created_count = 0
        for i in range(count):
            interest = random.choice(interests)
            template = random.choice(class_templates)
            
            # 클래스명 생성
            if '{}' in template:
                class_name = template.format(interest.interestName)
            else:
                class_name = f"{template} {interest.interestName}"
            
            # 지역 추가 (30% 확률)
            if random.random() < 0.3:
                location = random.choice(locations)
                class_name = f"{location} {class_name}"
            
            # 중복 클래스명 방지
            counter = 1
            original_name = class_name
            while Class.objects.filter(className=class_name).exists():
                class_name = f"{original_name} {counter}"
                counter += 1
            
            # 날짜 설정 (현재부터 미래 6개월 내)
            start_days = random.randint(1, 60)  # 1-60일 후 시작
            duration_days = random.randint(30, 180)  # 30-180일간 진행
            
            start_date = date.today() + timedelta(days=start_days)
            end_date = start_date + timedelta(days=duration_days)
            
            try:
                class_obj = Class.objects.create(
                    className=class_name,
                    classStartDate=start_date,
                    classEndDate=end_date,
                    interestID=interest
                )
                
                created_count += 1
                self.stdout.write(f'  ➕ 클래스 생성: {class_name}')
                
            except Exception as e:
                self.stdout.write(f'  ❌ 클래스 생성 실패 {class_name}: {str(e)}')
        
        self.stdout.write(f'✅ 총 {created_count}개의 클래스가 생성되었습니다.')

    def create_sugang(self):
        """수강신청 생성"""
        self.stdout.write('📋 수강신청 데이터 생성 중...')
        
        members = list(Member.objects.all())
        classes = list(Class.objects.all())
        
        if not members or not classes:
            self.stdout.write('❌ 회원 또는 클래스가 없습니다.')
            return
        
        created_count = 0
        for member in members:
            # 각 회원이 1-5개의 랜덤 클래스에 신청
            num_classes = random.randint(1, min(5, len(classes)))
            member_classes = random.sample(classes, num_classes)
            
            for class_obj in member_classes:
                try:
                    # 신청일을 클래스 시작일 이전으로 설정
                    days_before = random.randint(1, 30)
                    reg_date = class_obj.classStartDate - timedelta(days=days_before)
                    
                    # 시간 추가
                    reg_datetime = timezone.make_aware(
                        timezone.datetime.combine(
                            reg_date, 
                            timezone.datetime.min.time().replace(
                                hour=random.randint(9, 21),
                                minute=random.randint(0, 59)
                            )
                        )
                    )
                    
                    sugang = Sugang.objects.create(
                        member_accountID=member,
                        class_classID=class_obj,
                        registration_date=reg_datetime
                    )
                    created_count += 1
                    
                except Exception:
                    pass  # 중복 등은 무시
        
        self.stdout.write(f'✅ 총 {created_count}개의 수강신청이 생성되었습니다.')

    def create_member_interests(self):
        """회원관심사 생성"""
        self.stdout.write('💝 회원관심사 데이터 생성 중...')
        
        members = list(Member.objects.all())
        interests = list(Interests.objects.all())
        
        if not members or not interests:
            self.stdout.write('❌ 회원 또는 관심사가 없습니다.')
            return
        
        created_count = 0
        for member in members:
            # 각 회원이 1-4개의 관심사를 가짐
            num_interests = random.randint(1, min(4, len(interests)))
            member_interests = random.sample(interests, num_interests)
            
            for interest in member_interests:
                try:
                    MemberInterests.objects.create(
                        member=member,
                        interests=interest
                    )
                    created_count += 1
                except Exception:
                    pass  # 중복 무시
        
        self.stdout.write(f'✅ 총 {created_count}개의 회원관심사가 생성되었습니다.')

    def create_posts(self):
        """게시글 생성"""
        self.stdout.write('📝 게시글 데이터 생성 중...')
        
        post_titles = [
            '안녕하세요! 처음 참여합니다', '오늘 모임 후기입니다', '다음 모임 일정 공지',
            '모임 장소 변경 안내', '신입 회원 환영합니다!', '질문있습니다!',
            '감사 인사드립니다', '모임 규칙 안내', '추천하고 싶은 팁',
            '모임 참여 소감', '다음 주 계획', '준비물 안내',
            '모임 사진 공유', '좋은 정보 공유', '함께 해요!',
            '궁금한 점이 있어요', '도움이 필요합니다', '경험담 공유',
            '추천 도서/자료', '모임 개선 제안'
        ]
        
        post_contents = [
            '안녕하세요! 이번에 처음 참여하게 되었습니다. 잘 부탁드려요. 앞으로 함께 좋은 시간 보내면 좋겠습니다. 많은 조언 부탁드립니다.',
            '오늘 모임 정말 즐거웠어요! 다들 친절하게 대해주셔서 감사합니다. 다음 모임도 기대됩니다. 오늘 배운 것들을 잘 활용해보겠습니다.',
            '다음 주 모임은 토요일 오후 2시에 진행됩니다. 장소는 기존과 동일하니 참고해주세요. 준비물이 있다면 미리 안내드리겠습니다.',
            '갑작스럽게 장소가 변경되었습니다. 새로운 장소는 단체 채팅방에 공유드렸으니 확인해주세요. 시간은 동일합니다.',
            '새로 가입하신 분들 환영합니다! 궁금한 점이 있으시면 언제든 문의해주세요. 함께 즐거운 모임 만들어가요.',
            '초보자인데 질문이 있습니다. 어떻게 시작하면 좋을까요? 조언 부탁드립니다. 경험 있으신 분들의 노하우도 듣고 싶어요.',
            '오늘 도움 주신 분들께 감사드립니다. 덕분에 즐거운 시간이었어요. 다음에도 잘 부탁드립니다.',
            '모임 참여 시 지켜야 할 기본 규칙들을 안내드립니다. 모두 함께 지켜주시면 더 좋은 모임이 될 것 같아요.',
            '오늘 배운 유용한 팁을 공유합니다. 다들 한번씩 시도해보시면 좋을 것 같아요. 제가 해본 경험상 정말 도움이 됩니다.',
            '이번 모임을 통해 많은 것을 배웠습니다. 특히 오늘 다룬 내용은 정말 유익했어요. 다음에도 이런 유익한 시간이 있으면 좋겠습니다.'
        ]
        
        categories = ['notice', 'review', 'general']
        category_weights = [0.15, 0.25, 0.6]  # 공지 15%, 후기 25%, 일반 60%
        
        # 활성 클래스만 선택 (게시글이 있을만한 클래스)
        active_classes = list(Class.objects.filter(
            classStartDate__lte=timezone.now().date() + timedelta(days=30)
        ))
        
        if not active_classes:
            self.stdout.write('❌ 활성 클래스가 없습니다.')
            return
        
        # 수강생이 있는 클래스만 선택
        classes_with_members = []
        for cls in active_classes:
            if cls.sugang_set.exists():
                classes_with_members.append(cls)
        
        if not classes_with_members:
            self.stdout.write('❌ 수강생이 있는 클래스가 없습니다.')
            return
        
        created_count = 0
        for class_obj in classes_with_members[:20]:  # 상위 20개 클래스에만 게시글 생성
            # 해당 클래스의 수강생들
            class_members = list(Member.objects.filter(
                sugang_set__class_classID=class_obj
            ))
            
            if not class_members:
                continue
            
            # 각 클래스마다 3-8개의 게시글 생성
            num_posts = random.randint(3, 8)
            
            for _ in range(num_posts):
                title = random.choice(post_titles)
                content = random.choice(post_contents)
                category = random.choices(categories, weights=category_weights)[0]
                author = random.choice(class_members)
                
                # 게시글 작성일을 클래스 기간 내로 설정
                start_date = max(class_obj.classStartDate, timezone.now().date() - timedelta(days=30))
                end_date = min(class_obj.classEndDate, timezone.now().date())
                
                if start_date <= end_date:
                    days_range = (end_date - start_date).days
                    if days_range > 0:
                        random_days = random.randint(0, days_range)
                        post_date = start_date + timedelta(days=random_days)
                        
                        post_datetime = timezone.make_aware(
                            timezone.datetime.combine(
                                post_date,
                                timezone.datetime.min.time().replace(
                                    hour=random.randint(9, 22),
                                    minute=random.randint(0, 59)
                                )
                            )
                        )
                    else:
                        post_datetime = timezone.now()
                else:
                    post_datetime = timezone.now()
                
                try:
                    post = Post.objects.create(
                        title=title,
                        content=content,
                        category=category,
                        class_classID=class_obj,
                        author=author,
                        writeDate=post_datetime,
                        view_count=random.randint(0, 50)
                    )
                    created_count += 1
                except Exception:
                    pass  # 오류 무시
        
        self.stdout.write(f'✅ 총 {created_count}개의 게시글이 생성되었습니다.')

    def create_attendance(self):
        """출석 데이터 생성"""
        self.stdout.write('📅 출석 데이터 생성 중...')
        
        sugang_list = list(Sugang.objects.select_related(
            'class_classID', 'member_accountID'
        ))
        
        if not sugang_list:
            self.stdout.write('❌ 수강신청 데이터가 없습니다.')
            return
        
        attendance_statuses = ['present', 'absent', 'late']
        status_weights = [0.8, 0.1, 0.1]  # 출석 80%, 결석 10%, 지각 10%
        
        created_count = 0
        for sugang in sugang_list:
            class_obj = sugang.class_classID
            
            # 클래스가 시작된 경우만 출석 데이터 생성
            if class_obj.classStartDate > timezone.now().date():
                continue
            
            # 클래스 기간 내의 주별 출석 생성 (주 1회 가정)
            current_date = class_obj.classStartDate
            end_date = min(class_obj.classEndDate, timezone.now().date())
            
            while current_date <= end_date:
                # 주 1회 출석 (토요일마다)
                days_until_saturday = (5 - current_date.weekday()) % 7
                attendance_date = current_date + timedelta(days=days_until_saturday)
                
                if attendance_date <= end_date:
                    # 80% 확률로 출석 기록 생성 (모든 모임에 참석하지 않을 수 있음)
                    if random.random() < 0.8:
                        status = random.choices(attendance_statuses, weights=status_weights)[0]
                        
                        try:
                            Attendance.objects.create(
                                sugang_sugangID=sugang,
                                attendDate=attendance_date,
                                attendanceStatus=status
                            )
                            created_count += 1
                        except Exception:
                            pass  # 중복 등 오류 무시
                
                # 다음 주로 이동
                current_date = attendance_date + timedelta(days=7)
        
        self.stdout.write(f'✅ 총 {created_count}개의 출석 기록이 생성되었습니다.')

    def display_summary(self):
        """최종 통계 출력"""
        self.stdout.write('\n📊 최종 데이터베이스 현황')
        self.stdout.write('=' * 40)
        
        stats = [
            ('관심사', Interests.objects.count()),
            ('회원', Member.objects.count()),
            ('클래스', Class.objects.count()),
            ('수강신청', Sugang.objects.count()),
            ('회원관심사', MemberInterests.objects.count()),
            ('게시글', Post.objects.count()),
            ('출석기록', Attendance.objects.count()),
        ]
        
        for name, count in stats:
            self.stdout.write(f'{name}: {count:,}개')
        
        # 추가 통계
        active_classes = Class.objects.filter(
            classStartDate__lte=timezone.now().date(),
            classEndDate__gte=timezone.now().date()
        ).count()
        
        recent_posts = Post.objects.filter(
            writeDate__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        self.stdout.write(f'\n📈 추가 통계')
        self.stdout.write(f'현재 진행 중인 클래스: {active_classes}개')
        self.stdout.write(f'최근 7일간 게시글: {recent_posts}개')
        
        self.stdout.write('=' * 40)