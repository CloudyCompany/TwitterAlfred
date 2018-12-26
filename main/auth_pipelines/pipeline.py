from main.models import *

def create_user(backend, user, response, *args, **kwargs):
    
    sys_user = SystemUser(id=response["id"], following_count=response["friends_count"])
    sys_user.save()

    print("System user saved")

def save_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'twitter':
        profile_photo = response.get('profile_image_url')
        user.profile_photo = profile_photo
        user.save()
        user.social_auth.get(provider='twitter').set_extra_data({"profile_photo":profile_photo})