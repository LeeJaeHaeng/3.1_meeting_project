# meeting_app/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random
from meeting_app.models import *

class Command(BaseCommand):
    help = '샘플 데이터를 생성합니다'

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

    def handle(self, *args, **options):
        self.stdout.write('샘플 데이터 생성을 시작합니다...')

        try:
            # 기존 데이터 삭제
            self.stdout.write('기존 데이터 삭제 중...')
            Attendance.objects.all().delete()
            Post.objects.all().delete()
            Sugang.objects.all().delete()
            MemberInterests.objects.all().delete()
            Class.objects.all().delete()
            Member.objects.all().delete()
            Interests.objects.all().delete()
            
            # 1. 관심사 데이터 생성
            self.create_interests()
            
            # 2. 샘플 회원 생성
            self.create_members(options['members'])
            
            # 3. 샘플 클래스 생성
            self.create_classes(options['classes'])
            
            # 4. 수강신청 데이터 생성
            self.create_sugang()
            
            # 5. 게시글 데이터 생성
            self.create_posts()

            self.stdout.write(
                self.style.SUCCESS('샘플 데이터 생성이 완료되었습니다!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'오류 발생: {str(e)}')
            )

    def create_interests(self):
        """관심사 생성"""
        self.stdout.write('관심사 데이터 생성 중...')
        
        interests_data = [
            # 운동/스포츠
            '테니스', '배드민턴', '축구', '농구', '수영', '요가', '헬스', '러닝',
            
            # 스터디
            '영어회화', '중국어', 'Java', 'Python', '토익', '독서',
            
            # 취미/여가
            '요리', '베이킹', '여행', '게임', '커피',
            
            # 문화/예술
            '영화감상', '연극관람', '음악', '사진촬영',
            
            # 라이프스타일
            '반려동물', '원예', '명상'
        ]
        
        created_count = 0
        for interest_name in interests_data:
            interest = Interests.objects.create(interestName=interest_name)
            created_count += 1
            self.stdout.write(f'관심사 생성: {interest_name}')
        
        self.stdout.write(f'총 {created_count}개의 관심사가 생성되었습니다.')

    def create_members(self, count):
        """회원 생성"""
        self.stdout.write(f'{count}명의 회원 데이터 생성 중...')
        
        first_names = [
            '김민수', '이영희', '박철수', '최지현', '정다영',
            '강민재', '윤서연', '임태현', '한예진', '조성민',
            '신미경', '오준혁', '배수지', '노현우', '송가영',
            '홍정우', '권나연', '서동혁', '이수빈', '장민호'
        ]
        
        domains = ['gmail.com', 'naver.com', 'daum.net', 'kakao.com']
        account_types = ['student', 'instructor', 'admin']
        
        created_count = 0
        for i in range(count):
            account_id = f'user{i+1:03d}'
            name = random.choice(first_names)
            email = f'{account_id}@{random.choice(domains)}'
            phone = f'010-{random.randint(1000,9999)}-{random.randint(1000,9999)}'
            
            birth_year = random.randint(1980, 2000)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)
            birth_date = date(birth_year, birth_month, birth_day)
            
            try:
                member = Member.objects.create(
                    accountID=account_id,
                    password='password123',
                    accountType=random.choice(account_types),
                    name=name,
                    phoneNum=phone,
                    email=email,
                    birth=birth_date
                )
                
                # 각 회원에게 1-3개의 랜덤 관심사 할당
                interests = Interests.objects.order_by('?')[:random.randint(1, 3)]
                for interest in interests:
                    MemberInterests.objects.create(
                        member=member,
                        interests=interest
                    )
                
                created_count += 1
                self.stdout.write(f'회원 생성: {account_id} ({name})')
                
            except Exception as e:
                self.stdout.write(f'회원 생성 실패 {account_id}: {str(e)}')
        
        self.stdout.write(f'총 {created_count}명의 회원이 생성되었습니다.')

    def create_classes(self, count):
        """클래스 생성"""
        self.stdout.write(f'{count}개의 클래스 데이터 생성 중...')
        
        class_templates = [
            '초보자를 위한 {}', '주말 {} 모임', '{}를 함께해요',
            '아침 {} 클럽', '저녁 {} 동호회', '{} 정기모임',
            '강남 {} 동호회', '홍대 {} 모임', '{} 스터디'
        ]
        
        interests = list(Interests.objects.all())
        if not interests:
            self.stdout.write('관심사가 없습니다.')
            return
        
        created_count = 0
        for i in range(count):
            interest = random.choice(interests)
            template = random.choice(class_templates)
            class_name = template.format(interest.interestName)
            
            # 중복 클래스명 방지
            counter = 1
            original_name = class_name
            while Class.objects.filter(className=class_name).exists():
                class_name = f"{original_name} {counter}"
                counter += 1
            
            start_date = date.today() + timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(days=random.randint(30, 90))
            
            try:
                class_obj = Class.objects.create(
                    className=class_name,
                    classStartDate=start_date,
                    classEndDate=end_date,
                    interestID=interest
                )
                
                created_count += 1
                self.stdout.write(f'클래스 생성: {class_name}')
                
            except Exception as e:
                self.stdout.write(f'클래스 생성 실패 {class_name}: {str(e)}')
        
        self.stdout.write(f'총 {created_count}개의 클래스가 생성되었습니다.')

    def create_sugang(self):
        """수강신청 생성"""
        self.stdout.write('수강신청 데이터 생성 중...')
        
        members = list(Member.objects.all())
        classes = list(Class.objects.all())
        
        if not members or not classes:
            self.stdout.write('회원 또는 클래스가 없습니다.')
            return
        
        created_count = 0
        for member in members:
            # 각 회원이 2-5개의 랜덤 클래스에 신청
            num_classes = random.randint(2, min(5, len(classes)))
            member_classes = random.sample(classes, num_classes)
            
            for class_obj in member_classes:
                try:
                    Sugang.objects.create(
                        member_accountID=member,
                        class_classID=class_obj
                    )
                    created_count += 1
                except Exception:
                    pass  # 중복 등은 무시
        
        self.stdout.write(f'총 {created_count}개의 수강신청이 생성되었습니다.')

    def create_posts(self):
        """게시글 생성"""
        self.stdout.write('게시글 데이터 생성 중...')
        
        post_titles = [
            '안녕하세요! 처음 참여합니다',
            '오늘 모임 후기입니다',
            '다음 모임 일정 공지',
            '모임 장소 변경 안내',
            '신입 회원 환영합니다!',
            '질문있습니다!',
            '감사 인사드립니다',
            '모임 규칙 안내'
        ]
        
        post_contents = [
            '안녕하세요! 이번에 처음 참여하게 되었습니다. 잘 부탁드려요. 앞으로 함께 좋은 시간 보내면 좋겠습니다.',
            '오늘 모임 정말 즐거웠어요! 다들 친절하게 대해주셔서 감사합니다. 다음 모임도 기대됩니다.',
            '다음 주 모임은 토요일 오후 2시에 진행됩니다. 장소는 기존과 동일하니 참고해주세요.',
            '갑작스럽게 장소가 변경되었습니다. 새로운 장소는 카톡방에 공유드렸으니 확인해주세요.',
            '새로 가입하신 분들 환영합니다! 궁금한 점이 있으시면 언제든 문의해주세요.',
            '초보자인데 질문이 있습니다. 어떻게 시작하면 좋을까요? 조언 부탁드립니다.',
            '오늘 도움 주신 분들께 감사드립니다. 덕분에 즐거운 시간이었어요.',
            '모임 참여 시 지켜야 할 기본 규칙들을 안내드립니다. 모두 함께 지켜주세요.'
        ]
        
        categories = ['notice', 'review', 'general']
        classes = list(Class.objects.all())
        members = list(Member.objects.all())
        
        if not classes or not members:
            self.stdout.write('클래스 또는 회원이 없습니다.')
            return
        
        created_count = 0
        for class_obj in classes[:20]:  # 상위 20개 클래스에만 게시글 생성
            # 각 클래스마다 3-8개의 게시글 생성
            num_posts = random.randint(3, 8)
            
            for _ in range(num_posts):
                title = random.choice(post_titles)
                content = random.choice(post_contents)
                category = random.choices(categories, weights=[0.2, 0.3, 0.5])[0]  # 일반글 비중 높임
                author = random.choice(members)
                
                try:
                    Post.objects.create(
                        title=title,
                        content=content,
                        category=category,
                        class_classID=class_obj,
                        author=author
                    )
                    created_count += 1
                except Exception:
                    pass  # 중복 등의 오류는 무시
        
        self.stdout.write(f'총 {created_count}개의 게시글이 생성되었습니다.')
        
        # 최종 통계 출력
        self.stdout.write('\n=== 최종 데이터 현황 ===')
        self.stdout.write(f'관심사: {Interests.objects.count()}개')
        self.stdout.write(f'회원: {Member.objects.count()}명')
        self.stdout.write(f'클래스: {Class.objects.count()}개')
        self.stdout.write(f'수강신청: {Sugang.objects.count()}개')
        self.stdout.write(f'게시글: {Post.objects.count()}개')