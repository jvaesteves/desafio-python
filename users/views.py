from django.conf import settings
from django.db import IntegrityError
from django.db.models import ObjectDoesNotExist
from django.utils import timezone
from jwt import encode as jwt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Phone, User

REGISTER_KEYS = {'name', 'email', 'password', 'phones'}
LOGIN_KEYS = {'email', 'password'}
PHONE_KEYS = {'ddd', 'number'}


def test_json_keys(needed_keys, data):
    data_keys = set(data.keys())
    error = None

    nonexistent_keys = needed_keys.difference(data_keys)
    unknown_keys = data_keys.difference(needed_keys)

    if (len(nonexistent_keys) + len(unknown_keys)) > 0:
        error = '; '.join([
            '; '.join('Required key: %s' % key for key in nonexistent_keys),
            ';'.join('Invalid key: %s' % key for key in unknown_keys)
        ])

    if error:
        raise KeyError(error)


@api_view(['POST'])
def register(request, format=None):
    data = request.data

    # Test if it has all required fields
    try:
        test_json_keys(REGISTER_KEYS, data)

        for phone in data.get('phones'):
            test_json_keys(PHONE_KEYS, phone)
    except KeyError as e:
        error = {'error': str(e)}
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    # Test if this user already exists, if not, create
    try:
        user = User.objects.create_user(
            first_name=data.get('name'),
            username=data.get('email'),
            email=data.get('email'),
            password=data.get('password'),
            token=jwt(data, settings.TOKEN_SECRET, algorithm='HS512')
        )
    except IntegrityError as e:
        error = {'error': 'E-mail já existente'}
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    # Save each phone to the database
    for phone in data.get('phones'):
        try:
            Phone.objects.create(
                user=user,
                ddd=phone.get('ddd'),
                number=phone.get('number')
            )
        except IntegrityError as e:
            if user:
                user.delete()
            error = {'error': str(e)}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

    return Response(user.toJSONdict(), status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login(request):
    data = request.data

    # Test if it has all required fields
    try:
        test_json_keys(LOGIN_KEYS, data)
    except KeyError as e:
        error = {'error': str(e)}
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    # Check if user's e-mail exists
    try:
        user = User.objects.get(username=data.get('email'))
    except ObjectDoesNotExist as e:
        error = {'error': 'Usuário e/ou senha inválidos'}
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    # Checks the given password
    if not user.check_password(data.get('password')):
        error = {'error': 'Usuário e/ou senha inválidos'}
        return Response(error, status=status.HTTP_401_UNAUTHORIZED)

    return Response(user.toJSONdict(), status.HTTP_200_OK)


@api_view(['GET'])
def get_profile(request, id, format=None):
    token = request.META.get('HTTP_X_API_KEY')

    # Check if user sent his token
    if token is None:
        error = {'error': 'Não autorizado'}
        return Response(error, status.HTTP_401_UNAUTHORIZED)

    # Check if token is valid and corresponds to the given id
    try:
        user = User.objects.get(id=id, token=token)
    except ObjectDoesNotExist as e:
        error = {'error': 'Não autorizado'}
        return Response(error, status.HTTP_401_UNAUTHORIZED)

    # Check if user's last_login was less than 30 minutes ago
    if user.last_login is not None:
        delta = timezone.now() - user.last_login
        if delta.seconds >= 1800:
            error = {'error': 'Sessão inválida'}
            return Response(error, status.HTTP_401_UNAUTHORIZED)
    else:
        error = {'error': 'Sessão inválida'}
        return Response(error, status.HTTP_401_UNAUTHORIZED)

    return Response(user.toJSONdict(), status.HTTP_200_OK)
