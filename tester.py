import requests
from bs4 import BeautifulSoup
import csv
import sys
import time
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import spacy
from spacy_help_functiosn import get_entities, create_entity_pairs
from spanbert import SpanBERT
import openai

API_KEY = AIzaSyDnmpdnGICKIyboO8Kkt5ejzpAU4gfsN18
ENGINE_KEY = db5d168d3993a85fe
SEC_KEY = ""
REL = ""
THR = ""
QUERY = "bill gates microsoft"
TUPS = ""

def get_results(akey=API_KEY, query=QUERY, ekey=ENGINE_KEY):
    service = build(
        "customsearch", "v1", developerKey=api_key
    )

    res = (
        service.cse()
        .list(
            q=query,
            cx=engine_key,
        )
        .execute()
    )

    top10_urls = []

    for i in range(len(res['items'])):
        top10_urls.append(res['items'][i].get('link',""))

    # for use in query optimization in separate function
    return top10_urls

def extract_plaintext(url):
    print("WEEEBBBBBBB: ", url)
    r = requests.get(url)
    print("\n request test: \n", r)

if __name__ == "__main__":
    top = get_results()
    for i in top:
        extract_plaintext(i)