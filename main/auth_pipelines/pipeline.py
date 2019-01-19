from main.models import *
import tweepy
import time


consumer_key = "2G8XPMR1fsWlUih1vSs0PPGP0"
consumer_secret = "HqsjqDywEICnxgvi9uY1KEGD1n9rXVhyv6ytldzbatJoe64uHF"
access_token = "748223177210331142-8fnl2OAldHDHiDttw4QFbqFppAYhzYw"
access_token_secret = "P3rleM8izkVLsOGIYG8DElTSZAAwFLxOt7cle9aNKYzPz"


def create_user(backend, user, response, *args, **kwargs):
    if not SystemUser.objects.filter(id=response["id"]).exists():
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
        except tweepy.TweepError as e:
            if "Rate limit exceeded" in e.__str__():
                time.sleep(60 * 5)  # Sleep for 5 minutes
            else:
                print(e)
                break


def update_user(backend, user, response, *args, **kwargs):
    system_user = SystemUser.objects.filter(id=response["id"])[0]
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    try:
        if system_user.following_count != int(response["friends_count"]):
            friends_list = []
            print("users deleted")
            for friends in handle_errors(tweepy.Cursor(api.friends, screen_name=response["screen_name"]).pages()):
                for idx in range(len(friends)):
                    print(friends[idx])
                    #followers_count = api.get_user(friend.id).followers_count
                    user = User(id=friends[idx].id_str, followers_count=friends[idx].followers_count)
                    user.save()
                    friends_list.append(user)
            #  system_user.following_count = response["friends_count"]
            #system_user.following_users.all().delete()
            system_user.following_users.set(friends_list)

            if response["friends_count"] != system_user.following_count:
                system_user.following_count = response["friends_count"]
            system_user.save()
        print("friends")
        if response["favourites_count"] != system_user.favourites_count:
            UserLike.objects.filter(system_user=system_user).delete()
            for favorite in tweepy.Cursor(api.favorites, screen_name=response["screen_name"]).items(300):
                print(favorite.user)
                users = User.objects.filter(id=favorite.user.id)
                if len(users) == 0:
                    #followers_count = api.get_user(favorite.user.id).followers_count
                    liked_user = User(id=favorite.user.id, followers_count=favorite.user.followers_count)
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
    except tweepy.error.RateLimitError:
        print("Rate Limit error")
    finally:
        system_user.save()

    print("System user updated")