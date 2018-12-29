from main.models import *
import tweepy
import time


consumer_key = "2G8XPMR1fsWlUih1vSs0PPGP0"
consumer_secret = "HqsjqDywEICnxgvi9uY1KEGD1n9rXVhyv6ytldzbatJoe64uHF"
access_token = "748223177210331142-8fnl2OAldHDHiDttw4QFbqFppAYhzYw"
access_token_secret = "P3rleM8izkVLsOGIYG8DElTSZAAwFLxOt7cle9aNKYzPz"


def create_user(backend, user, response, *args, **kwargs):
    if len(SystemUser.objects.filter(id=response["id"])) == 0:
        sys_user = SystemUser(id=response["id"], followers_count=response["followers_count"], favourites_count=0,
                              following_count=0)
        sys_user.save()

    print("System user saved")


def save_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'twitter':
        profile_photo = response.get('profile_image_url')
        user.profile_photo = profile_photo
        user.save()
        user.social_auth.get(provider='twitter').set_extra_data({"profile_photo": profile_photo})


def handle_errors(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.TweepError:
            time.sleep(20 * 60)


def update_user(backend, user, response, *args, **kwargs):
    system_user = SystemUser.objects.filter(id=response["id"])[0]
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    if system_user.following_count != int(response["friends_count"]):

        friends = []
        for ids in handle_errors(tweepy.Cursor(api.friends_ids, screen_name=response["screen_name"]).pages()):
            for id in ids:
                try:
                    friends.append(User.objects.get(id=id))
                except User.DoesNotExist:
                    user = User(id=id, followers_count=0)
                    user.save()
                    friends.append(user)
        system_user.following_count = response["friends_count"]
        system_user.following_users.set(friends)
        system_user.save()

    if response["favourites_count"] != system_user.favourites_count:
        UserLike.objects.filter(system_user=system_user).delete()
        for favorite in handle_errors(tweepy.Cursor(api.favorites, screen_name=response["screen_name"]).items(100)):
                users = User.objects.filter(id=favorite.user.id)
                if len(users) == 0:
                    liked_user = User(id=favorite.user.id, followers_count=0)
                    liked_user.save()
                else:
                    liked_user = users[0]

                likes = UserLike.objects.filter(user=liked_user, system_user=system_user)
                if len(likes)>0:
                    likes[0].like_count += 1
                    likes[0].save()
                else:
                    like = UserLike(user=liked_user, system_user=system_user, like_count=1)
                    like.save()

        system_user.favourites_count = response["favourites_count"]
        system_user.save()

    print("System user updated")