from main.models import *
import tweepy
import time
from bs4 import BeautifulSoup
import urllib.request
import mechanize
import http.cookiejar


consumer_key = "2G8XPMR1fsWlUih1vSs0PPGP0"
consumer_secret = "HqsjqDywEICnxgvi9uY1KEGD1n9rXVhyv6ytldzbatJoe64uHF"
access_token = "748223177210331142-8fnl2OAldHDHiDttw4QFbqFppAYhzYw"
access_token_secret = "P3rleM8izkVLsOGIYG8DElTSZAAwFLxOt7cle9aNKYzPz"


def create_user(backend, user, response, *args, **kwargs):
    if not SystemUser.objects.filter(id=response["id"]).exists():
        sys_user = SystemUser(id=response["id"], username=response["screen_name"], photo_url=response["profile_image_url"], name=response["name"], followers_count=response["followers_count"], favourites_count=0,
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
    if system_user.following_count != int(response["friends_count"]):
        friends_list = save_friends(api, response["screen_name"])

        system_user.following_users.set(friends_list)

        if response["friends_count"] != system_user.following_count:
            system_user.following_count = response["friends_count"]
        system_user.save()

    print("friends")
    print(response["favourites_count"])
    print(system_user.favourites_count)
    if response["favourites_count"] != system_user.favourites_count:
        save_likes(system_user, response["screen_name"], response["favourites_count"], api, 1)

    system_user.save()

    print("System user updated")


def save_friends(api, screen_name, depth=0):
    friends_list = []
    print("users deleted")
    try:

        for friends in tweepy.Cursor(api.friends, screen_name=screen_name).pages():
            for idx in range(len(friends)):
                print(friends[idx].screen_name)
                # followers_count = api.get_user(friend.id).followers_count
                user = User(id=friends[idx].id_str, username=friends[idx].screen_name, name=friends[idx].name, photo_url=friends[idx].profile_image_url, followers_count=friends[idx].followers_count, following_count=friends[idx].friends_count, favourites_count=friends[idx].favourites_count)
                user.save()
                friends_list.append(user)
                save_likes(user, friends[idx].screen_name, friends[idx].favourites_count, api, 1)
                # if depth < 0:
                #     result_friends = save_friends(api, friends[idx].screen_name, depth=depth+1)
                #     user.following_users.set(result_friends)
                #     user.save()
    except tweepy.TweepError as e:
        if "Rate limit exceeded" in e.__str__() or "Twitter error response: status code = 429" in e.__str__():
            friends_list = scrapp_friends(screen_name, depth)
        else:
            print(e)
    return friends_list


def save_likes(system_user, screen_name, favourites_count, api, depth=0):
    try:
        UserLike.objects.filter(system_user=system_user).delete()
        for favorites in tweepy.Cursor(api.favorites, screen_name=screen_name).pages():

            for favorite in favorites:
                print(favorite.user.screen_name)
                users = User.objects.filter(id=favorite.user.id)
                if len(users) == 0:
                    liked_user = User(id=favorite.user.id, followers_count=favorite.user.followers_count,name=favorite.user.name, photo_url=favorite.user.profile_image_url ,username=favorite.user.screen_name, following_count=favorite.user.friends_count, favourites_count=favorite.user.favourites_count)
                    liked_user.save()
                else:
                    liked_user = users[0]

                likes = UserLike.objects.filter(user=liked_user, system_user=system_user)
                if len(likes) > 0:
                    likes[0].like_count += 1
                    likes[0].save()
                else:
                    like = UserLike(user=liked_user, system_user=system_user, like_count=1)
                    like.save()
                # if depth < 0:
                #     save_likes(liked_user, favorite.user.screen_name, favorite.user.favourites_count, api, depth=depth+1)
            system_user.favourites_count = favourites_count

    except tweepy.TweepError as e:
        if "Rate limit exceeded" in e.__str__() or "Twitter error response: status code = 429" in e.__str__():
            print("Scrapp likes")
            scrapp_likes(system_user, screen_name, depth)
            system_user.favourites_count = favourites_count
        else:
            print(e)


def get_user_followers_count(user):
    url = "https://twitter.com/" + user

    # Scrapping to retrieve twitter profile
    url = urllib.request.urlopen(url)

    soup = BeautifulSoup(url, 'html.parser')

    url.close()
    profile = soup.find(id='doc')
    profile_app_container = profile.findAll('div', class_="AppContainer")[1]

    try:
        following = profile_app_container.findAll('span', class_="ProfileNav-value")[2]["data-count"]
    except:
        following = 0

    return following


def scrapp_friends(screen_name, depth=0):

    print("Actualisando :)")

    print(screen_name)
    print("El user es " + screen_name)

    url = "https://twitter.com/" + screen_name + "/following/"

    cj = http.cookiejar.CookieJar()
    br = mechanize.Browser()
    br.set_cookiejar(cj)
    br.open(url)

    br.select_form(action="https://twitter.com/sessions")
    br.form['session[username_or_email]'] = 'cloudycompany'
    br.form['session[password]'] = 'cloudycompany123'
    br.submit()
    content = br.response().read()

    friend_list = []
    print("-------------------------------")

    soup = BeautifulSoup(content, 'html.parser')
    following = soup.findAll('div', class_="Grid-cell u-size1of2 u-lg-size1of3 u-mb10")
    following = soup.findAll('div', class_="Grid-cell u-size1of2 u-lg-size1of3 u-mb10")
    for f in following:
        try:
            user_data = f.find("div", {"data-screen-name":True}, class_="ProfileCard js-actionable-user ")
            username = user_data["data-screen-name"]
            name = user_data.find("div", class_="ProfileCard-content").a["data-original-title"]
            photo = user_data.find("a", class_="ProfileCard-avatarLink js-nav js-tooltip").a.img["src"]
            user_id = user_data["data-user-id"]
            print(username)
            print(user_id)

            followers_count = get_user_followers_count(username)
            print(followers_count)

            user = User.objects.filter(id=user_id)
            if len(user) == 0:
                friend = User(id=user_id, followers_count=followers_count, name=name, photo_url=photo, screen_name=user_data.a.b.string, following_count=0, favourites_count=0)
                friend.save()

                friend_list.append(friend)

                # if depth < 0:
                #     result_friends = scrapp_friends(username, depth=depth+1)
                #     friend.following_users.set(result_friends)
                #     friend.save()
                #     scrapp_likes(friend, username, 1)
                print("=======================================")

            print("\n")
        except:
            break

    return friend_list


def scrapp_likes(system_user, screen_name, depth=0):

    print("Actualisando :)")
    print("DEPTH is : "+ str(depth))

    print("El user es " + screen_name)

    url = "https://twitter.com/" + screen_name + "/likes/"

    cj = http.cookiejar.CookieJar()
    br = mechanize.Browser()
    br.set_cookiejar(cj)
    br.open(url)

    br.select_form(action="https://twitter.com/sessions")
    br.form['session[username_or_email]'] = 'cloudycompany'
    br.form['session[password]'] = 'cloudycompany123'
    br.submit()
    content = br.response().read()

    print("-------------------------------")

    soup = BeautifulSoup(content, 'html.parser')

    # likes = soup.find("li", {"class": "ProfileNav-item ProfileNav-item--favorites is-active"}).a.find("span", {"class": "ProfileNav-value"})["data-count"]
    # print("Likes: "+likes)

    following = soup.findAll('div', {"class": "content"})
    for f in following:
        try:
            user_data = f.find("div", {"class": "stream-item-header"})
            if user_data is None:
                print("End of likes page")
                break
            user_id = user_data.a["data-user-id"]
            username = user_data.a.find("span", {"class": "username u-dir u-textTruncate"}).b.string
            name = user_data.a.find("span", {"class": "FullNameGroup"}).strong.string
            photo = user_data.a.find("a", {"class": "account-group js-account-group js-action-profile js-user-profile-link js-nav"}).img["src"]
            print(username)
            print(user_id)

            following_count = get_user_followers_count(username)
            print(following_count)

            users = User.objects.filter(id=user_id)
            if len(users) == 0:
                liked_user = User(id=user_id, followers_count=following_count,name=name, photo_url=photo, username=user_data.a.b.string, following_count=0, favourites_count=0)
                liked_user.save()
            else:
                liked_user = users[0]

            likes = UserLike.objects.filter(user=liked_user, system_user=system_user)
            if len(likes) > 0:
                likes[0].like_count += 1
                likes[0].save()
            else:
                like = UserLike(user=liked_user, system_user=system_user, like_count=1)
                like.save()
            print("=================")

            print("\n")
        except:
            break

