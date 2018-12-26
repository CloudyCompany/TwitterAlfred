from main.models import *
from bs4 import BeautifulSoup
from urllib.request import urlopen


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


def update_user(backend, user, response, *args, **kwargs):
    system_user = SystemUser.objects.filter(id=response["id"])[0]

    if system_user.following_count != int(response["friends_count"]) or len(system_user.following_users) != int(response["friends_count"]):
        page = urlopen("https://twitter.com/"+response["screen_name"]+"/following")
        tree = BeautifulSoup(page.read().decode('utf-8'), 'html.parser')

        followers = tree.findAll('div', {"class":"following"})
        for follower in followers:
            follow_id = follower["data-user-id"]
            User.objects.get_or_create(id=follow_id)

        print("System user updated")