from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
import tweepy
import time
from django.http import JsonResponse
from main.forms import *
from main.models import *
import numpy as np
import requests
from requests_oauthlib import OAuth1Session
import json

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
        if (time.time() - current_time) < time_limit and status.id != last_id:
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
    global pagination
    global places

    if request.method == 'POST':
        form = FilterForm(request.POST)
        if form.is_valid():

            if tag != form['tag'].value():
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


def sim_pearson(friends_p1, friends_p2):

    # Get the list of mutually rated items
    si={}
    for item in friends_p1:
        if item in friends_p2:
            si[item] = 1
        # Find the number of elements
    n=len(si)
    # if they are no ratings in common, return 0
    if n==0: return 0

    return (len(friends_p1)/n)+1/len(friends_p2)


def retrieve_user_data(user):
    twitter = OAuth1Session('2G8XPMR1fsWlUih1vSs0PPGP0',
                            client_secret='HqsjqDywEICnxgvi9uY1KEGD1n9rXVhyv6ytldzbatJoe64uHF',
                            resource_owner_key='748223177210331142-8fnl2OAldHDHiDttw4QFbqFppAYhzYw',
                            resource_owner_secret='P3rleM8izkVLsOGIYG8DElTSZAAwFLxOt7cle9aNKYzPz')
    user_data = twitter.get("https://api.twitter.com/1.1/users/show.json?user_id="+str(user)).text
    # print(user_data.text)
    user.data = json.loads(user_data)

def getRecommendations(user,similarity=sim_pearson):
    totals={}
    simSums={}
    follows = SystemUser.objects.filter(id=user)[0].following_users.all()
    for other in SystemUser.objects.all():
        # don't compare me to myself
        if str(other) == str(user): continue
        other_follows = SystemUser.objects.filter(id=other.id)[0].following_users.all()
        # print(other_follows)
        sim=similarity(follows, other_follows)
        # ignore scores of zero or lower
        if sim<=0: continue
        for item in other_follows:
            # only score movies I haven't seen yet
            if str(item) == str(user): continue 
            if item not in follows:
                # Similarity * Score
                if item.followers_count != 0:
                    totals.setdefault(item, 0)

                    totals[item] += item.followers_count*sim
                    # Sum of similarities
                    simSums.setdefault(item, 0)
                    simSums[item] += sim
    # Create the normalized list
    rankings=[(float(total/simSums[item]), item) for item, total in totals.items()]
    # Return the sorted list
    rankings = sorted(rankings, key= lambda x: x[0], reverse=True)[:10]
    # Get user profile and annotate it
    [retrieve_user_data(value) for item, value in rankings]
    #rankings.reverse()
    return rankings


def recommend(request):
    user_id = request.user.social_auth.get(provider='twitter').uid
    recommendations = getRecommendations(user_id)

    return render(request, "main/recommendations.html", {"recommendations": recommendations})

