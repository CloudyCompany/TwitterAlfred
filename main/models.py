from django.db import models


# Create your models here.
class User(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    followers_count = models.IntegerField()

    def __str__(self):
        return str(self.id)


class SystemUser(User):
    following_count = models.IntegerField()
    favourites_count = models.IntegerField()
    following_users = models.ManyToManyField(User, related_name='following_users')
    recommendations = models.ManyToManyField(User, related_name="recommendations")


class UserLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="like_user")
    system_user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, related_name="like_system_user")
    like_count = models.IntegerField()
