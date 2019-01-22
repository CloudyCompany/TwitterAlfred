from django.shortcuts import render
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
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
from operator import itemgetter
import math
import re

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
                print(tag)
                print(last_tag)

            pagination = int(form["pagination"].value())
            tweets = []
            get_twitter_stream()
            
            return render(request, "main/tweets.html", {"tweets":tweets, "url": "http://127.0.0.1:8000/getStream/", "form": form})
    else:
        form = FilterForm()
        get_twitter_stream()

    return render(request, "main/tweets.html", {"tweets": tweets, "url": "http://127.0.0.1:8000/getStream/", "form": form})


def sim_pearson(p1, p2, friends_p1, friends_p2):

    if len(friends_p1) == 0 or len(friends_p2) == 0 or p2.following_count == 0: return 0

    # Get the list of mutually rated items
    si={}
    for item in friends_p1:
        if UserLike.objects.filter(system_user=p2, user=item.user).exists():
                si[item.user] = 1
        # Find the number of elements
    n=len(si)
    if n == 0:
        for item in p1.following_users.all():
            if p2.following_users.filter(id=item.id).exists():
                si[item]=1
        if len(si)==0: return 0
        if p1.following_count==0: return 0
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
                if not likes.\
                        exists():
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
    # [retrieve_user_data(value) for item, value in rankings]
    rankings = [el[1] for el in rankings]
    #rankings.reverse()
    return rankings

@login_required
def recommend(request):
    user_id = request.user.social_auth.get(provider='twitter').uid
    system_user = SystemUser.objects.filter(id=user_id)[0]

    if request.method == 'POST':
        recommendations = getRecommendations(system_user)
        system_user.recommendations.set(recommendations)
        system_user.save()
    else:
        if system_user.recommendations.count() == 0:
            recommendations = getRecommendations(system_user)
            system_user.recommendations.set(recommendations)
            system_user.save()
        else:
            recommendations = system_user.recommendations.all()

    print(recommendations)
    return render(request, "main/recommendations.html", {"recommendations": recommendations[:5]})


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
    user = User.objects.filter(username=request.GET.get('screen_name'))[0]

    # Scrapping to retrieve twitter profile
    url = urllib.request.urlopen(url)

    soup = BeautifulSoup(url, 'html.parser')

    url.close()
    profile = soup.find(id='doc')
    profile_picture = profile.find('img',class_="avatar", src=True)['src']
    profile_card = profile.find('div',class_="ProfileHeaderCard")
    profile_app_container = profile.findAll('div',class_="AppContainer")[1]
    last_tweet = soup.findAll("p", class_="TweetTextSize TweetTextSize--normal js-tweet-text tweet-text")[0].text.split("pic.twitter")[0]
    tweet = soup.findAll("div", class_="tweet")[0].text
    try:
        tweet_count = profile_app_container.find('a', {'data-nav':'tweets'}).findAll("span")[2]["data-count"]
    except:
        tweet_count = 0

    try:
        following = profile_app_container.find('a', {'data-nav':'following'}).findAll("span")[2]["data-count"]
    except:
        following = 0

    try:
        followers = profile_app_container.find('a', {'data-nav':'followers'}).findAll("span")[2]["data-count"]
    except:
        followers = 0
        
    bio = profile_card.find('p', class_="ProfileHeaderCard-bio u-dir").getText()
    location = profile_card.find('span', class_="ProfileHeaderCard-locationText u-dir").text

    # Setting of data
    data["profile_picture"] = str(profile_picture)
    data["profile_card"] = str(profile_card)
    data["profile_app_container"] = str(profile_app_container)
    data["tweet_count"] = str(tweet_count)
    data["bio"] = re.sub('\s+', ' ', str(bio)).strip()
    data["location"] = re.sub('\s+', ' ', str(location)).strip()
    data["username"] = request.GET.get('screen_name')
    data["name"] = user.name
    data["following"] = str(following)
    data["followers"] = str(followers)
    data["last_tweet"] = str(last_tweet)
    data["tweet"] = str(tweet)
    return JsonResponse({'data': data})

@login_required
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


def get_likes_graph(user_id):
    system_user = SystemUser.objects.filter(id=user_id)[0]

    user_likes = UserLike.objects.filter(system_user__id = user_id).order_by('-like_count')[:5]
    likes_graph = []

    for u in user_likes:
        likes_graph.append([u.user.username, u.like_count])

    return likes_graph

def get_follows_graph(user_id):
    system_user = SystemUser.objects.filter(id=user_id)[0]
    system_users = SystemUser.objects.all()
    follows_graph = []

    for s in system_users:
        if s == system_user: continue
        common_items = system_user.following_users.filter(id__in=s.following_users.values_list('id', flat=True))
        follows_graph.append([s.username, len(common_items)])

    return follows_graph

def get_sim_graph(user_id):
    system_user = SystemUser.objects.filter(id=user_id)[0]
    users = User.objects.all()
    sim_graph = []

    for u in users:
        sim = sim_pearson(system_user, u, UserLike.objects.filter(system_user=system_user), UserLike.objects.filter(user=u))
        if sim == 0: continue
        sim_graph.append([u.username, math.ceil(sim)])

    return sorted(sim_graph, key=itemgetter(1), reverse=True)[:5]

@login_required
def get_stats(request):
    user_id = request.user.social_auth.get(provider='twitter').uid
    likes_graph = get_likes_graph(user_id)
    follows_graph = get_follows_graph(user_id)
    sim_graph = get_sim_graph(user_id)

    return render(request, "main/stats.html", {'likes_graph': likes_graph, 'follows_graph': follows_graph, 'sim_graph': sim_graph})