import json
import uuid

from django.conf import settings
from django.test import TestCase

from .models import Phone, User


class UsersTestCase(TestCase):
    id

    def setUp(self):
        user = User.objects.create_user(
            first_name='Alberto Roberto',
            username='alberto@roberto.com',
            email='alberto@roberto.com',
            password='hunter2',
            token='TESTTOKEN'
        )

        self.id = str(user.id)

        Phone.objects.create(
            user=user,
            ddd='21',
            number='26134141'
        )

    def test_model_dict(self):
        user = User.objects.get(username='alberto@roberto.com')
        model_dict = user.toJSONdict()

        self.assertEqual(model_dict.get('id'), str(user.id))
        self.assertEqual(model_dict.get('name'), user.first_name)
        self.assertEqual(model_dict.get('email'), user.email)
        self.assertEqual(model_dict.get('created'), str(user.date_joined))
        self.assertEqual(model_dict.get('modified'), str(user.last_modified))
        self.assertEqual(model_dict.get('token'), user.token)

        self.assertIsNone(model_dict.get('last_login'), None)
        self.assertIsNone(user.last_login)

        self.assertTrue(user.check_password('hunter2'))
        user.last_login = None
        user.save()

        phones = Phone.objects.filter(user=user)
        dict_phone = model_dict.get('phones')

        self.assertEqual(len(dict_phone), len(phones))
        self.assertEqual(dict_phone[0].get('ddd'), phones[0].ddd)
        self.assertEqual(dict_phone[0].get('number'), phones[0].number)

    def test_invalid_register_keys(self):
        payload = json.dumps({
            'name': 'João da Silva',
            'email': 'joao@silva.org',
            'test': 'scanning'
        })
        res = self.client.post('/users/register/', payload, 'application/json')

        self.assertContains(res, 'Required key: password', status_code=400)
        self.assertContains(res, 'Required key: phones', status_code=400)
        self.assertContains(res, 'Invalid key: test', status_code=400)

    def test_invalid_phone_keys(self):
        payload = json.dumps({
            'name': 'João da Silva',
            'email': 'joao@silva.org',
            'password': 'hunter2',
            'phones': [{
                    'test': 'scanning',
                    'ddd': '21'
            }]
        })
        res = self.client.post('/users/register/', payload, 'application/json')

        self.assertContains(res, 'Required key: number', status_code=400)
        self.assertContains(res, 'Invalid key: test', status_code=400)

    def test_invalid_register_email(self):
        payload = json.dumps({
            'name': 'João da Silva',
            'email': 'alberto@roberto.com',
            'password': 'hunter2',
            'phones': [{
                    'ddd': '21',
                    'number': '987654321'
            }]
        })
        res = self.client.post('/users/register/', payload, 'application/json')

        self.assertContains(res, 'E-mail já existente', status_code=400)

    def test_valid_register_request(self):
        payload = json.dumps({
            "name": "João da Silva",
            "email": "joao@silva.org",
            "password": "hunter2",
            "phones": [
                {
                    "number": "987654321",
                    "ddd": "21"
                }
            ]
        })
        res = self.client.post('/users/register/', payload, 'application/json')
        self.assertEqual(res.status_code, 201)

        user = User.objects.get(username='joao@silva.org')
        user = json.dumps(user.toJSONdict())
        res = json.dumps(res.json())

        self.assertEqual(user, res)

    def test_invalid_login_keys(self):
        payload = json.dumps({
            'email': 'alberto@roberto.com',
            'token': 'TESTTOKEN'
        })

        res = self.client.post('/users/login/', payload, 'application/json')

        self.assertContains(res, 'Required key: password', status_code=400)
        self.assertContains(res, 'Invalid key: token', status_code=400)

    def test_nonexistent_email(self):
        payload = json.dumps({
            'email': 'roberto@alberto.com',
            'password': 'hunter2'
        })

        r = self.client.post('/users/login/', payload, 'application/json')

        self.assertContains(r, 'Usuário e/ou senha inválidos', status_code=400)

    def test_wrong_password(self):
        payload = json.dumps({
            'email': 'alberto@roberto.com',
            'password': 'hunter1'
        })

        r = self.client.post('/users/login/', payload, 'application/json')

        self.assertContains(r, 'Usuário e/ou senha inválidos', status_code=401)

    def test_valid_login_request(self):
        payload = json.dumps({
            'email': 'alberto@roberto.com',
            'password': 'hunter2'
        })
        res = self.client.post('/users/login/', payload, 'application/json')
        self.assertEqual(res.status_code, 200)

        user = User.objects.get(username='alberto@roberto.com')
        user = json.dumps(user.toJSONdict())
        res = json.dumps(res.json())

        self.assertEqual(user, res)

    def test_profile_request_without_token(self):
        res = self.client.get('/users/profile/%s' % self.id)
        self.assertContains(res, 'Não autorizado', status_code=401)

    def test_profile_request_invalid_token(self):
        res = self.client.get(
            '/users/profile/%s' % self.id,
            HTTP_X_API_KEY='INVALIDTOKEN'
        )

        self.assertContains(res, 'Não autorizado', status_code=401)

    def test_profile_request_invalid_id(self):
        res = self.client.get(
            '/users/profile/%s' % str(uuid.uuid1()),
            HTTP_X_API_KEY='TESTTOKEN'
        )

        self.assertContains(res, 'Não autorizado', status_code=401)

    def test_profile_request_invalid_session(self):
        user = User.objects.get(id=self.id)
        user.last_login = None
        user.save()

        res = self.client.get(
            '/users/profile/%s' % self.id,
            HTTP_X_API_KEY='TESTTOKEN'
        )

        self.assertContains(res, 'Sessão inválida', status_code=401)

    def test_profile_request_invalid_session(self):
        user = User.objects.get(id=self.id)
        user.last_login = None
        user.save()

        res = self.client.get(
            '/users/profile/%s' % self.id,
            HTTP_X_API_KEY='TESTTOKEN'
        )

        self.assertContains(res, 'Sessão inválida', status_code=401)

    def test_valid_profile_request(self):
        payload = json.dumps({
            'email': 'alberto@roberto.com',
            'password': 'hunter2'
        })
        res = self.client.post('/users/login/', payload, 'application/json')
        self.assertEqual(res.status_code, 200)

        res = self.client.get(
            '/users/profile/%s' % self.id,
            HTTP_X_API_KEY=res.json().get('token')
        )
        self.assertEqual(res.status_code, 200)

        user = User.objects.get(username='alberto@roberto.com')
        user = json.dumps(user.toJSONdict())
        res = json.dumps(res.json())

        self.assertEqual(user, res)
