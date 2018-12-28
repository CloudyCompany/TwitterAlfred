from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
import tweepy
import time
from django.http import JsonResponse
from main.forms import *
import numpy

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


@login_required
def home(request):
    return render(request, 'home.html')


class StreamListener(tweepy.StreamListener):
    global tweets
    global current_time
    global places

    def on_status(self, status):
        global last_id
        global photos
        print(status)
        if (time.time() - current_time) < time_limit and status.id != last_id:
            print(status.user.geo_enabled)
            print(status.coordinates)
            print(status.place)
            last_id = status.id
            tweet = {}
            tweet['text'] = status.text
            tweet['user_photo'] = status.user.profile_image_url
            tweet['date'] = status.created_at
            tweet['username'] = status.user.screen_name
            tweet['name'] = status.user.name
            tweets.insert(0, tweet)

            if status.place is not None:
                center = numpy.array(status.place.bounding_box.coordinates).mean(axis=1)[0].tolist()
                print(center)
                places.append(center)

            if len(tweets) > pagination:
                tweets.pop()
        
            return True
        else:
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

    return render(request, "main/tweets.html", {"tweets": tweets, "url": "http://127.0.0.1:8000/getStream/", "form":form})
