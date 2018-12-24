from django.db import models

# Create your models here.
class User(models.Model):
    id = models.IntegerField(primary_key=True)

    def __str__(self):
        return str(self.id)

class SystemUser(User):
    following_count = models.IntegerField()
    recommendations = models.ManyToManyField(User, related_name="recommendations")
