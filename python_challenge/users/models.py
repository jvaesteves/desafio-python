import json
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    last_modified = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, default=None)
    token = models.CharField(max_length=512, null=False, blank=False)

    def toJSONdict(self):
        phones = [
            {'ddd': phone.ddd, 'number': phone.number}
            for phone in Phone.objects.filter(user__id=self.id)
        ]

        return {
            'id': str(self.id),
            'name': self.first_name,
            'email': self.email,
            'phones': phones or None,
            'created': str(self.date_joined),
            'modified': str(self.last_modified),
            'last_login': str(self.last_login) if self.last_login else None,
            'token': self.token
        }

    def check_password(self, password):
        worked = super(User, self).check_password(password)
        if worked:
            self.last_login = timezone.now()
            self.save()

        return worked


class Phone(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ddd = models.CharField(max_length=2, blank=False, null=False)
    number = models.CharField(max_length=9, blank=False, null=False)
