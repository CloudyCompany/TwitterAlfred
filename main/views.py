from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
import tweepy
import time
from django.http import JsonResponse
from main.forms import *

consumer_key = "2G8XPMR1fsWlUih1vSs0PPGP0"
consumer_secret = "HqsjqDywEICnxgvi9uY1KEGD1n9rXVhyv6ytldzbatJoe64uHF"
access_token = "748223177210331142-8fnl2OAldHDHiDttw4QFbqFppAYhzYw"
access_token_secret = "P3rleM8izkVLsOGIYG8DElTSZAAwFLxOt7cle9aNKYzPz"
tweets = []
time_limit = 5
current_time = 0
tag = "pink"

# Create your views here.
@login_required
def home(request):
    return render(request, 'home.html')

class StreamListener(tweepy.StreamListener):
    global tweets
    global current_time

    def on_status(self, status):
        # print(str(time.time() - current_time))
        if (time.time() - current_time) < time_limit:
            tweets.append(status.text)
            # print(status.text)
            return True
        else:
            return False


def get_twitter_stream(request):
    global tweets
    global time_limit
    global current_time
    global tag
    # if len(tweets) > 30:
    #     tweets = []

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    time_limit = 5
    current_time = time.time()

    streamListener = StreamListener()

    stream = tweepy.Stream(auth=api.auth, listener=streamListener)
    stream.filter(track=[str(tag)])

    return JsonResponse({'data':tweets})


def twitter_stream(request):
    global tweets
    global tag

    get_twitter_stream("")

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = FilterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            print("holiiii")
            tag = form['tag'].value()
            tweets = []
            get_twitter_stream("")
            
            return render(request, "main/tweets.html", {"tweets":tweets, "url": "http://127.0.0.1:8000/getStream/", "form":form})            
    else:
        form = FilterForm()

    return render(request, "main/tweets.html", {"tweets":tweets, "url": "http://127.0.0.1:8000/getStream/", "form":form})
