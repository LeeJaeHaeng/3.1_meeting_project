# 소모임 관리 시스템 (Meeting Project)

## 프로젝트 소개
이 프로젝트는 소모임(클래스)을 관리하고 운영할 수 있는 웹 기반 시스템입니다. Django 프레임워크를 사용하여 개발되었으며, MySQL 데이터베이스를 활용합니다.

## 주요 기능
- 회원 관리
  - 회원가입 및 로그인
  - 마이페이지를 통한 개인 정보 관리
  - 관심사 설정 및 관리

- 클래스(소모임) 관리
  - 클래스 검색 및 필터링
  - 클래스 신청 및 관리
  - 정원 관리 및 출석 체크
  - 게시판 기능

- 커뮤니티 기능
  - 클래스별 게시판
  - 출석 관리
  - 활동 통계

## 기술 스택
- Backend: Django
- Database: MySQL
- Frontend: HTML, CSS, JavaScript
- 기타: Bootstrap

## 설치 및 실행 방법
1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 데이터베이스 설정
- MySQL 데이터베이스 생성
- settings.py에서 데이터베이스 설정 수정

4. 마이그레이션 실행
```bash
python manage.py makemigrations
python manage.py migrate
```

5. 서버 실행
```bash
python manage.py runserver
```

## 프로젝트 구조
```
meeting_project/
├── meeting_app/          # 메인 애플리케이션
│   ├── models.py        # 데이터베이스 모델
│   ├── views.py         # 뷰 로직
│   ├── forms.py         # 폼 정의
│   └── templates/       # HTML 템플릿
├── static/              # 정적 파일
├── media/               # 업로드된 파일
└── manage.py           # Django 관리 스크립트
```

## 주요 모델
- Member: 회원 정보
- Class: 클래스(소모임) 정보
- Sugang: 수강 신청 정보
- Post: 게시글
- Attendance: 출석 정보
- Interests: 관심사 정보

## 개발자
- 이재행 (Lee Jae Haeng)

## 라이선스
이 프로젝트는 MIT 라이선스를 따릅니다. 