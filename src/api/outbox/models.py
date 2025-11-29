from django.db import models

# Create your models here.


class Outbox(models.Model):
    sender = models.CharField(max_length = 255)
    receiver = models.CharField(max_length = 255)
    data = models.TextField()
