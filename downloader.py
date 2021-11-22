#!/usr/bin/env python
import signal
import sys
import os
import io
import json
import time
import math
import requests
import urllib.request
from dotenv import load_dotenv

load_dotenv()

CREATOR = None
SAVE_PATH = None
COOKIE = os.environ.get("COOKIE")
LIMIT = 12

url = "https://pocketstars.com/graphql"
headers = {
    "accept": "*/*",
    "accept-language": "en-DE,en;q=0.9,ja-JP;q=0.8,ja;q=0.7,en-GB;q=0.6,en-US;q=0.5,de;q=0.4",
    "content-type": "application/json",
    "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"96\", \"Google Chrome\";v=\"96\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-app-version": "e3c9624",
    "referer": "no-referrer",
    "cookie": COOKIE
}

def signal_handler(sig, frame):
    print("Exiting...")
    sys.exit(0)

def fetch_profile():
    data = {
        "operationName": "getProfile",
        "query": "query getProfile($username: String!) {\n  user(username: $username) {\n    id\n    displayName\n    username\n    subscription {\n      state\n      expiresAt\n      __typename\n    }\n    numLikes\n    numPosts\n    listIds\n    banner\n    avatar\n    numImages\n    numVideos\n    lastSeen\n    bio\n    subscriptionPrice\n    role\n    featured\n    subscriptionBundles {\n      id\n      duration\n      discountPercentage\n      price\n      maxUsage\n      expiresAt\n      message\n      used\n      __typename\n    }\n    gender\n    postsAreHidden\n    canBeMessaged\n    blocked\n    doesHardKinks\n    __typename\n  }\n}\n",
        "variables": {
            "username": CREATOR
        }
    }
    response = requests.post(url, data=json.dumps(data), headers=headers)
    user = json.loads(response.text)['data']['user']

    return user

def fetch_profile_images(offset):
    image_urls = [] 
    data = {
        "operationName": "getProfileImages",
        "query": "query getProfileImages($username: String!, $limit: Int, $offset: Int) {\n  images(username: $username, limit: $limit, offset: $offset) {\n    url\n    tileUrl\n    post {\n      kind\n      id\n      price\n      username\n      __typename\n    }\n    __typename\n  }\n}\n",
        "variables": {
            "limit": LIMIT,
            "offset": offset,
            "username": CREATOR
        }
    }
    response = requests.post(url, data=json.dumps(data), headers=headers)
    images = json.loads(response.text)['data']['images']

    if(images):
        for img in images:
            image_urls.append(img['url'])
    else:
        print(f"ERROR: Couldn't fetch images {offset} - {offset + LIMIT}.")

    return image_urls

def fetch_profile_videos(offset):
    video_urls = [] 
    data = {
        "operationName": "getProfileVideos",
        "query": "query getProfileVideos($username: String!, $limit: Int, $offset: Int) {\n  videos(username: $username, limit: $limit, offset: $offset) {\n    url\n    thumbnailUrl\n    tileUrl\n    post {\n      kind\n      id\n      price\n      username\n      __typename\n    }\n    __typename\n  }\n}\n",
        "variables": {
            "limit": LIMIT,
            "offset": offset,
            "username": CREATOR
        }
    }
    response = requests.post(url, data=json.dumps(data), headers=headers)
    videos = json.loads(response.text)['data']['videos']

    if(videos):
        for vid in videos:
            video_urls.append(vid['url'])
    else:
        print(f"ERROR: Couldn't fetch videos {offset} - {offset + LIMIT}.")

    return video_urls

def get_image_count():
    user = fetch_profile()
    image_count = 0
    if(user):
        image_count = user['numImages']
        print(f"{CREATOR} has {image_count} images.")
    else:
        print(f"ERROR: Couldn't fetch data for user {CREATOR}.")

    return image_count

def get_video_count():
    user = fetch_profile()
    video_count = 0
    if(user):
        video_count = user['numVideos']
        print(f"{CREATOR} has {video_count} videos.")
    else:
        print(f"ERROR: Couldn't fetch data for user {CREATOR}.")

    return video_count

def startProgress(title):
    global progress_x
    sys.stdout.write(title + ": [" + "-"*40 + "]" + chr(8)*41)
    sys.stdout.flush()
    progress_x = 0

def progress(x):
    global progress_x
    x = int(x * 40 // 100)
    sys.stdout.write("#" * (x - progress_x))
    sys.stdout.flush()
    progress_x = x

def endProgress():
    sys.stdout.write("#" * (40 - progress_x) + "]\n")
    sys.stdout.flush()

def save_file(url, offset, counter, path_suffix):
    if "placeholder" in url:
        return

    path = SAVE_PATH + f"{path_suffix}/"
    if not os.path.exists(path):
        os.makedirs(path)

    file_name = url.rsplit('/', 1)[1].rsplit('?', 1)[0]
    if not os.path.isfile(path + file_name):
        f = open(path + file_name, 'wb')
    
        with urllib.request.urlopen(url) as resp:
            length = resp.getheader('content-length')
            block_size = 1000000
    
            if length:
                length = int(length)
                block_size = max(4096, length // 20)
    
            buffer_all = io.BytesIO()
            size = 0
            startProgress(f"Downloading file {counter + offset}")
            while True:
                buffer_now = resp.read(block_size)
                if not buffer_now:
                    break
                buffer_all.write(buffer_now)
                size += len(buffer_now)
                if length:
                    percent = int((size / length) * 100)
                    progress(percent)
    
            f.write(buffer_all.getvalue())
            endProgress()
            f.close()
    else:
        print(f"File {counter + offset} already downloaded.")

def download_images():
    image_count = get_image_count()
    iterations = math.ceil(image_count / LIMIT)
    errors = 0

    for x in range(iterations):
        offset = x * LIMIT
        print(f"INFO: Downloading images {offset + 1} - {offset + LIMIT}")

        image_urls = fetch_profile_images(offset)
        image_counter = 0
        if(image_urls):
            for url in image_urls:
                image_counter += 1
                save_file(url, offset, image_counter, "images")
        else:
            errors += 1

    if errors != 0:
        print(f"There has been {errors} errors while downloading, please repeat.")

def download_videos():
    video_count = get_video_count()
    iterations = math.ceil(video_count / LIMIT)
    errors = 0

    for x in range(iterations):
        offset = x * LIMIT
        print(f"INFO: Downloading videos {offset + 1} - {offset + LIMIT}")

        video_urls = fetch_profile_videos(offset)
        video_counter = 0
        if(video_urls):
            for url in video_urls:
                video_counter += 1
                save_file(url, offset, video_counter, "videos")
        else:
            errors += 1

    if errors != 0:
        print(f"There has been {errors} errors while downloading, please repeat.")

def init():
    print(f"PocketStars Downloader\n")
    global CREATOR 
    CREATOR = input("Username of creator: ")
    global SAVE_PATH
    SAVE_PATH = f"./{CREATOR}/"

def main():
    init()

    selection = input("Select Content: Images (1), Videos (2): ")
    if selection == "1":
        download_images()
    if selection == "2":
        download_videos()

signal.signal(signal.SIGINT, signal_handler)
main()