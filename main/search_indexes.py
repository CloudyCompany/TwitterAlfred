from haystack import indexes
from main.models import User, SystemUser


class UserIndex(indexes.SearchIndex, indexes.Indexable):
    id = indexes.IntegerField()
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return User

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(id=self.id)


class SystemUserIndex(indexes.SearchIndex, indexes.Indexable):
    id = indexes.IntegerField()
    text = indexes.CharField(document=True, use_template=True)
    following_users = indexes.ModelSearchIndex(User)

    def get_model(self):
        return SystemUser

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(id=self.id)