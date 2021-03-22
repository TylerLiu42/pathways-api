from requests_futures.sessions import FuturesSession
from youtubesearchpython.__future__ import VideosSearch
from flask import request, jsonify
from bs4 import BeautifulSoup as bs
import asyncio 
import requests

def get_resources():
    # payload = request.get_json()
    tags = request.args.get('tags')
    # tags = payload.get('tags')
    response = {}
    session = FuturesSession()
    futures_medium = []
    youtube_results = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    youtube_results = loop.run_until_complete(scrape_youtube(tags))
    for tag in tags:
        futures_medium.append((session.get("https://medium.com/search?q=" + tag), tag))
    for future, tag in futures_medium:
        medium_results = scrape_medium(future.result().content)
        response[tag] = {"medium": medium_results, "youtube": youtube_results[tag]}
    return jsonify(resources=response, message="Success"), 200
        
async def scrape_youtube(search_strings):
    results = {}
    for search_string in search_strings:
        videosSearch = VideosSearch(search_string, limit = 5)
        videosResult = await videosSearch.next()
        scraped_data = []
        for result in videosResult["result"]:
            scraped_data.append({"title": result["title"], "url": result["link"]})
        results[search_string] = scraped_data
    return results
    
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