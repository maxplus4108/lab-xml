from django.db import models

class ExampleModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    email = models.EmailField()
    what_sells = models.CharField(max_length=100, default='')

    def __str__(self):
        return self.name
