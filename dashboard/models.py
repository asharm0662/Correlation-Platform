from __future__ import unicode_literals
from django.db import models


class DataSource(models.Model):
    name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=50)
    human_name = models.CharField(max_length=100)


class DatedData(models.Model):
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    date = models.DateField()
    value = models.FloatField()


class SentimentData(models.Model):
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    value = models.FloatField()

