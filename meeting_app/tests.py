 
# meeting_app/tests.py
from django.test import TestCase
from django.urls import reverse
from .models import *
from datetime import date

class MemberModelTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(
            accountID='testuser',
            password='testpass123',
            name='테스트유저',
            phoneNum='010-1234-5678',
            email='test@example.com',
            birth=date(1990, 1, 1)
        )
    
    def test_member_creation(self):
        self.assertEqual(self.member.accountID, 'testuser')
        self.assertEqual(self.member.name, '테스트유저')
        self.assertEqual(str(self.member), '테스트유저 (testuser)')

class ClassModelTest(TestCase):
    def setUp(self):
        self.interest = Interests.objects.create(interestName='테니스')
        self.class_obj = Class.objects.create(
            className='테니스 초보자 모임',
            classStartDate=date.today(),
            classEndDate=date(2025, 12, 31),
            interestID=self.interest
        )
    
    def test_class_creation(self):
        self.assertEqual(self.class_obj.className, '테니스 초보자 모임')
        self.assertEqual(self.class_obj.interestID, self.interest)

class ViewsTest(TestCase):
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)