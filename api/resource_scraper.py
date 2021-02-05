from requests_futures.sessions import FuturesSession
from flask import request, jsonify
from bs4 import BeautifulSoup as bs
import sys 
import requests

def get_resources():
    payload = request.get_json()
    tags = payload.get('tags')
    response = {}
    session = FuturesSession()
    futures_youtube = []
    futures_medium = []
    for tag in tags:
        #futures_youtube.append(requests.get('https://www.youtube.com/results?search_query=' + tag))
        futures_medium.append((session.get("https://medium.com/search?q=" + tag), tag))
    for future in futures_youtube:
        resources = []
        youtube_results = scrape_youtube(future.text)
    for future, tag in futures_medium:
        medium_results = scrape_medium(future.result().content)
        response[tag] = {"medium": medium_results}
    return jsonify(resources=response, message="Success"), 200
        
def scrape_youtube(content):
    #WIP
    soup = BeautifulSoup(content, 'html.parser')
    thumbnails = soup.findAll(attrs={'class':'yt-uix-tile-link'})
    for thumbnail in thumbnails:
        print(thumbnail, file=sys.stderr)
    
def scrape_medium(content):
    article_info = []
    titles = []
    links = []
    soup = bs(content, 'html.parser')
    article_titles_div = soup.findAll('div', "section-inner", limit=5)
    article_links_div = soup.findAll('div', "postArticle-content", limit=5)
    for div in article_links_div:
        for a in div.find_all('a'):
            links.append(a['data-action-value'])
    
    for title in article_titles_div:
        for h3 in title.find_all('h3'):
            titles.append(h3.text)
        
    for i in range(len(titles)):
        article_info.append({"title": titles[i], "url": links[i]})
        
    return article_info