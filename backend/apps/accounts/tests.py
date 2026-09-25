from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(phone_number='09123456789', password='password123')

    def test_signup(self):
        response = self.client.post(reverse('signUp'), {
            'phone_number': '09987654321',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 302) # Redirect to dashboard
        self.assertTrue(User.objects.filter(phone_number='09987654321').exists())

    def test_login(self):
        response = self.client.post(reverse('login'), {
            'phone_number': '09123456789',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302) # Redirect to dashboard
    
    def test_dashboard_access_denied_anonymous(self):
        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 302) # Redirect to login
