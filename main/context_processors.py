from django.contrib.auth.models import User

def user_online(request):
    user = request.user
    user_online = (hasattr(user, 'social_auth') and user.social_auth.count() >= 1)
    screen_name = ""
    profile_photo = ""

    if user_online:
        social = user.social_auth.get(provider='twitter') 
        extra_data = social.extra_data
        screen_name = extra_data["access_token"]["screen_name"]
        profile_photo = extra_data["profile_photo"]

    return {'user_online': user_online, 'screen_name': screen_name, 'profile_photo' : profile_photo}