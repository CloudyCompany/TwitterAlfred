from django.shortcuts import render
from django.db.models import Sum
import tweepy
import time
from django.http import JsonResponse
from main.forms import *
from main.models import *
import numpy as np
from requests_oauthlib import OAuth1Session, OAuth1
import json
from bs4 import BeautifulSoup
import urllib.request
import mechanize
import http.cookiejar

consumer_key = "2G8XPMR1fsWlUih1vSs0PPGP0"
consumer_secret = "HqsjqDywEICnxgvi9uY1KEGD1n9rXVhyv6ytldzbatJoe64uHF"
access_token = "748223177210331142-8fnl2OAldHDHiDttw4QFbqFppAYhzYw"
access_token_secret = "P3rleM8izkVLsOGIYG8DElTSZAAwFLxOt7cle9aNKYzPz"
tweets = []
places = []
pagination = 10
time_limit = 5
current_time = 0
tag = "trump"
last_tag = "trump"
last_id = 0


# @login_required
def home(request):
    return render(request, 'home.html')


class StreamListener(tweepy.StreamListener):
    global tweets
    global current_time
    global places

    def on_status(self, status):
        global last_id
        global last_tag
        if (time.time() - current_time) < time_limit and status.id != last_id and last_tag == tag:
            last_id = status.id
            tweet = {}
            tweet['text'] = status.text
            tweet['user_photo'] = status.user.profile_image_url
            tweet['date'] = status.created_at
            tweet['username'] = status.user.screen_name
            tweet['name'] = status.user.name
            tweets.insert(0, tweet)

            if status.place is not None:
                center = np.array(status.place.bounding_box.coordinates).mean(axis=1)[0].tolist()
                places.append(center)

            if len(tweets) > pagination:
                tweets.pop()
        
            return True
        else:
            last_tag = tag
            return False

    def on_error(self, status_code):
        if status_code != 200:
            return False


def get_twitter_stream(request=None):
    global tweets
    global time_limit
    global current_time
    global tag
    global places

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    time_limit = 5
    current_time = time.time()

    streamListener = StreamListener()
    stream = tweepy.Stream(auth=api.auth, listener=streamListener)
    stream.filter(track=[str(tag)])

    return JsonResponse({'data': tweets, 'places':places})


def twitter_stream(request):
    global tweets
    global tag
    global last_tag
    global pagination
    global places

    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():

            if tag != form['tag'].value():
                last_tag = tag
                tag = form['tag'].value()
                places = []

            pagination = int(form["pagination"].value())
            tweets = []
            get_twitter_stream()
            
            return render(request, "main/tweets.html", {"tweets":tweets, "url": "http://127.0.0.1:8000/getStream/", "form": form})
    else:
        form = FilterForm()
        get_twitter_stream()

    return render(request, "main/tweets.html", {"tweets": tweets, "url": "http://127.0.0.1:8000/getStream/", "form": form})


def sim_pearson(p1, p2, friends_p1, friends_p2):

    print(friends_p1)
    print(friends_p2)
    # Get the list of mutually rated items
    si={}
    for item in friends_p1:
        if UserLike.objects.filter(system_user=p2, user=item.user).exists():
                si[item.user] = 1
        # Find the number of elements
    n=len(si)
    print("N: "+str(n))
    if n == 0:
        for item in p1.following_users.all():
            if p2.following_users.filter(id=item.id).exists():
                si[item]=1
        if len(si)==0: return 0
        return (len(si)/p1.following_count)+1/p2.following_count

    sum1 = 0
    sum2 = 0
    sum1Sq = 0
    sum2Sq = 0
    pSum = 0

    for friend in si.keys():

        p1_likes = UserLike.objects.filter(system_user=p1, user=friend)
        p2_likes = UserLike.objects.filter(system_user=p2, user=friend)
        print(p1_likes)
        print(p2_likes)
        if len(p1_likes) > 0:
            p1_likes = p1_likes[0].like_count
        else:
            p1_likes = 0

        if len(p2_likes) > 0:
            p2_likes = p2_likes[0].like_count
        else:
            p2_likes = 0

        sum1 += p1_likes
        sum2 += p2_likes

        sum1Sq += pow(p1_likes, 2)
        sum2Sq += pow(p2_likes, 2)

        pSum += p1_likes*p2_likes

    num = pSum-(sum1*sum2/n)
    den = np.sqrt((sum1Sq-pow(sum1,2)/n)*(sum2Sq-pow(sum2,2)/n))
    if num == 0: return 0.5
    if den == 0: return 0.5

    return num/den


def retrieve_user_data(user):
    twitter = OAuth1Session('2G8XPMR1fsWlUih1vSs0PPGP0',
                            client_secret='HqsjqDywEICnxgvi9uY1KEGD1n9rXVhyv6ytldzbatJoe64uHF',
                            resource_owner_key='748223177210331142-8fnl2OAldHDHiDttw4QFbqFppAYhzYw',
                            resource_owner_secret='P3rleM8izkVLsOGIYG8DElTSZAAwFLxOt7cle9aNKYzPz')
    user_data = twitter.get("https://api.twitter.com/1.1/users/show.json?user_id="+str(user)).text
    # print(user_data.text)
    user.data = json.loads(user_data)


def getRecommendations(user, similarity=sim_pearson):
    totals={}
    simSums={}
    user_likes = UserLike.objects.filter(system_user=user)
    print(user_likes)
    for other in User.objects.all():
        print(other)
        # don't compare me to myself
        if str(other) == str(user): continue
        other_likes = UserLike.objects.filter(system_user=other)
        print(other_likes)
        # print(other_follows)
        sim=similarity(user, other, user_likes, other_likes)
        print(sim)
        # ignore scores of zero or lower
        if sim<=0: continue
        for item in other.following_users.all():
            # only score movies I haven't seen yet
            if str(item) == str(user): continue

            if not user.following_users.filter(id=item.id).exists():
                # Similarity * Score
                totals.setdefault(item, 0)
                likes = other_likes.filter(user=item)
                if not likes.exists():
                    num_likes = 1
                else:
                    num_likes = likes[0].like_count
                #print(item.followers_count)
                totals[item] += sim+np.log(num_likes+1)+np.log(item.followers_count+1)/10
                # Sum of similarities
                simSums.setdefault(item, 0)
                simSums[item] += sim

    # Create the normalized list
    rankings=[(total/simSums[item], item) for item, total in totals.items()]
    # Return the sorted list
    rankings = sorted(rankings, key= lambda x: x[0], reverse=True)[:10]
    print(rankings)
    # Get user profile and annotate it
    [retrieve_user_data(value) for item, value in rankings]
    #rankings.reverse()
    return rankings


def recommend(request):
    user_id = request.user.social_auth.get(provider='twitter').uid
    system_user = SystemUser.objects.filter(id=user_id)[0]
    print(system_user)
    recommendations = getRecommendations(system_user)

    return render(request, "main/recommendations.html", {"recommendations": recommendations})


def get_user_followers_count(user):
    url = "https://twitter.com/" + user

    # Scrapping to retrieve twitter profile
    url = urllib.request.urlopen(url)

    soup = BeautifulSoup(url, 'html.parser')

    url.close()
    profile = soup.find(id='doc')
    profile_app_container = profile.findAll('div',class_="AppContainer")[1]

    try:
        following = profile_app_container.findAll('span', class_="ProfileNav-value")[2]["data-count"]
    except:
        following = 0

    return following


def get_profile_preview(request):
    data = {}
    url = "https://twitter.com/" + request.GET.get('screen_name')

    # Scrapping to retrieve twitter profile
    url = urllib.request.urlopen(url)

    soup = BeautifulSoup(url, 'html.parser')

    url.close()
    profile = soup.find(id='doc')
    profile_picture = profile.find('img',class_="avatar", src=True)['src']
    profile_card = profile.find('div',class_="ProfileHeaderCard")
    profile_app_container = profile.findAll('div',class_="AppContainer")[1]
    data["profile_picture"] = str(profile_picture)
    data["profile_card"] = str(profile_card)
    data["profile_app_container"] = str(profile_app_container)
    
    return JsonResponse({'data': data})


def updateDB(request):

    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            print("Actualisando :)")

            screen_name = form['screen_name'].value()
            depth = int(form['depth'].value())

            print("El user es " + screen_name)

            url = "https://twitter.com/" + screen_name + "/following/"

            cj = http.cookiejar.CookieJar()
            br = mechanize.Browser()
            br.set_cookiejar(cj)
            br.open(url)

            br.select_form(action="https://twitter.com/sessions")
            br.form['session[username_or_email]'] = 'cloudycompany'
            br.form['session[password]'] = 'corchuelocabron'
            br.submit()
            content = br.response().read()

            for i in range(depth):
                print("Iteración número " + str(i+1))
                print("-------------------------------")

                soup = BeautifulSoup(content, 'html.parser')
                following = soup.findAll('div', class_="Grid-cell u-size1of2 u-lg-size1of3 u-mb10")
                for f in following:
                    user_data = f.find("div", {"data-screen-name":True}, class_="ProfileCard js-actionable-user ")
                    username = user_data["data-screen-name"]
                    user_id = user_data["data-user-id"]
                    print(username)
                    print(user_id)

                    following_count = get_user_followers_count(username)
                    print(following_count)

                print("\n")
    else:
        form = AccountForm()
    return render(request, "main/updateDB.html", {"form":form})


def get_stats(request):
    user_id = request.user.social_auth.get(provider='twitter').uid
    system_user = SystemUser.objects.filter(id=user_id)[0]

    user_likes = UserLike.objects.filter(system_user__id = user_id).order_by('-like_count')[:5]
    likes_graph = []

    for u in user_likes:
        likes_graph.append([u.user.id, u.like_count])

    print(likes_graph)
    return render(request, "main/stats.html", {'values': likes_graph})