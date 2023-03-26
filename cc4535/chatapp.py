import sys
import requests
from bs4 import BeautifulSoup
import openai
import json
######################### USAGE FROM PROJECT 1
import time
import pprint
from googleapiclient.discovery import build
import string
import nltk
sys.path.append('lib/')
#import lib.nltk as nltk
#nltk.data.append('lib/nltk_data/')
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt')
######################### USAGE FROM PROJECT 1

######################### PROJECT 2
from spacy_help_functions import get_entities as g_ent
from spacy_help_functions import extract_relations as e_rel
from spacy_help_functions import create_entity_pairs as cep
#import requests

"""
example input:
python3 project2.py -spanbert googleapikey12345 googleengineidabcdefg openaisecretkeya1b2c3d4 r t "bill gates burger" k
"""

GOOGLE_APIKEY = "abc123"
GOOGLE_ENGINEID = "xyz456"
OPENAI_SECRETKEY = "idk789"

r= int()
relations = ["SCHOOLS_ATTENDED", "WORK_FOR", "LIVE_IN", "TOP_MEMBER_EMPLOYEES"]
entities_of_interest = ["ORGANIZATION", "PERSON", "LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"]
t = int()
q = ""
k = int()

######################### PROJECT 2 

#first, initialize X as the empty set. X is the set of extracted tuples
def initialization(q):
    #initialize x as empty set
    X = set()

    def get_results(client_key=GOOGLE_APIKEY, engine_key=GOOGLE_ENGINEID, query=q):
        global doc_collection
        service = build(
            "customsearch", "v1", developerKey=client_key
        )

        res = (
            service.cse()
            .list(
                q=query,
                cx=engine_key,
            )
            .execute()
        )

        clean_json = [dict() for x in range(10)]

        for i in range(len(res['items'])): 
            #clean_json[i]['Title'] = res['items'][i].get('title',"")
            clean_json[i]['URL'] = res['items'][i].get('link',"")
            clean_json[i]['Summary'] = res['items'][i].get('snippet',"")
        doc_collection = clean_json
        return clean_json
    
    dict_URL = get_results()
















def BERT_main():
    pass

def GPT_main():
    pass

if __name__ == "__main__":
    """
    mode = sys.argv[1]
    apikey = sys.argv[2]
    googleid = sys.argv[3]
    aikey = sys.argv[4]
    r = sys.argv[5]
    t = sys.argv[6]
    q = sys.argv[7]
    k = sys.argv[8]
    """
    mode = sys.argv[1]
    r = sys.argv[2]
    t = sys.argv[3]
    q = sys.argv[4]
    k = sys.argv[5]
    if mode == '-spanbert':
        BERT_main(r, t, q, k)
        """
        -spanbert
        r = relation extraction
        t = extraction confidence threshold
        q = query
        k = desired number of tuples
        python3 project2.py -spanbert googleapikey12345 googleengineidabcdefg openaisecretkeya1b2c3d4 r t "bill gates burger" k
        python chatapp.py "-whatever" r t "q" k
        """
    elif mode == 'chatgpt3':
        GPT_main(r, t, q, k)
    else:
        print("please restart and pick a valid mode.")
        sys.exit()