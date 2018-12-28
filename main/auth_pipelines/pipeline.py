from main.models import *
import tweepy
import time


consumer_key = "2G8XPMR1fsWlUih1vSs0PPGP0"
consumer_secret = "HqsjqDywEICnxgvi9uY1KEGD1n9rXVhyv6ytldzbatJoe64uHF"
access_token = "748223177210331142-8fnl2OAldHDHiDttw4QFbqFppAYhzYw"
access_token_secret = "P3rleM8izkVLsOGIYG8DElTSZAAwFLxOt7cle9aNKYzPz"


def create_user(backend, user, response, *args, **kwargs):
    
    sys_user = SystemUser(id=response["id"], following_count=response["friends_count"])
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

    if system_user.following_count != int(response["friends_count"]) or len(system_user.following_users.all()) != int(response["friends_count"]):

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth)
        friends = []
        ids = []
        for ids in handle_errors(tweepy.Cursor(api.friends_ids, screen_name=response["screen_name"]).pages()):
            for id in ids:
                print(id)
                friends.append(User.objects.get_or_create(id=id)[0])
        system_user.following_users.set(friends)
        system_user.save()
        print("System user updated")