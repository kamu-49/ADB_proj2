import sys
import time
import pprint
from googleapiclient.discovery import build
#import pandas as pd
#from sklearn.feature_extraction.text import TfidfVectorizer

from nltk.tokenize import word_tokenize
import string
import sys
import nltk
sys.path.append('lib/')
#import lib.nltk as nltk
#nltk.data.append('lib/nltk_data/')
from nltk.tokenize import word_tokenize
nltk.download('stopwords')
nltk.download('punkt')


client_key = ""
engine_key = ""
query = ""
precision = 0.0
doc_collection = dict()
relevant_docs = []
relevant_quant = 0
irrelevant_quant = 0
stop_words = nltk.corpus.stopwords.words('english')

# prints parameters for api
def print_parameters(client_key, engine_key, query, precision):
    parameters = """Parameters:\nClient key  = {}\nEngine key  = {}\nQuery = {}\nPrecision = {}"""
    print(parameters.format(client_key, engine_key, query, precision))

# fetches results from api
#   called within user_interaction()?
#   parameters tentative until i play w/ api
def get_results(client_key, engine_key, query):
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
        clean_json[i]['Title'] = res['items'][i].get('title',"")
        clean_json[i]['URL'] = res['items'][i].get('link',"")
        clean_json[i]['Summary'] = res['items'][i].get('snippet',"")
        #clean_json[i]['URL'] = res['items'][i]['link']
        #clean_json[i]['Title'] = res['items'][i]['title']
        #clean_json[i]['Summary'] = res['items'][i]['snippet']
        #print(i, clean_json[i])
    #pprint.pprint(clean_json)
    # for use in query optimization in separate function
    doc_collection = clean_json
    return clean_json

# sets up user interaction, cycling through results
#   for loop x10, displaying a result and collecting a response at each iteration
#   keep track of 'yes' responses 
#   return precision obtained (no. 'yes' divided by 10)
#   note: adjust for termination cases ###
def user_interaction(client_key, engine_key, query):
    #
    global relevant_docs, relevant_quant, irrelevant_quant
    #
    result_template = """Result {}\n[\n URL: {}\n Title: {}\n Summary: {}\n]\n"""
    relevant_results = 0
    results_json = get_results(client_key, engine_key, query)

    #pprint.pprint(results_json)
    print('Google Search Results:\n======================')
    for i in range(len(results_json)):
        print(result_template.format(i + 1, results_json[i]['URL'], results_json[i]['Title'], results_json[i]['Summary']))

        relevant = relevant_prompt()
        if relevant == 'Y':
            relevant_results += 1
            relevant_quant += 1
            # relevant_docs.append(i)
        results_json[i]["Relevance"] = relevant #FIX DICTIONARIES
        #might want to put the new function here
        #cd = {}
        #cd = isInDoc(results_json, i, cd)
    irrelevant_quant = 10-relevant_quant
    #return precision
    #print("finished up here")
    return results_json, relevant_results/10.0

def relevant_prompt():
    while True:
        relevant = input('Relevant (Y/N)?')
        if relevant != 'Y' and relevant != 'N':
            print("Enter a valid response.")
            continue
        else:
            break
        
    return relevant

def feedback_summary(query, acheived_precision, desired_precision):
    summary_template = """======================\nFEEDBACK SUMMARY\nQuery {}\nPrecision {}"""
    print(summary_template.format(query, acheived_precision))
    if acheived_precision < desired_precision:
        print('Still below the desired precision of {}'.format(desired_precision))
    else:
        print('Desired precision reached, done')
    

# decides how to update the query (important part)
#   runs only if precision is not met in user interaction
#   runs after feedback summary

def inverted(json):
    bagofwords = []
    testbow = []
    bagy = ""
    bagn = ""
    testbaggy = ""

    for i in range(len(json)):
        if json[i]["Relevance"] == "Y":
            bagy += (json[i]['Title'] + " " + json[i]['Summary'])
        elif json[i]["Relevance"] == "N":
            bagn += (json[i]['Title'] + " " + json[i]['Summary'])
        testbaggy += (json[i]['Title'] + " " + json[i]['Summary']);

    toky = word_tokenize(bagy)
    tokn = word_tokenize(bagn)
    ttoks = word_tokenize(testbaggy)
    excluded = set(string.punctuation)
    excluded.add("...")
    excluded.add("'s")
    excluded.add('·')
    excluded.add('the')

    new_toky = ' '.join(d.lower() for d in toky if d not in stop_words and d not in excluded) 
    new_tokn = ' '.join(d.lower() for d in tokn if d not in stop_words and d not in excluded)
    new_ttoks = ' '.join(d.lower() for d in ttoks if d not in stop_words and d not in excluded)
    rel_list = word_tokenize(new_toky) #
    unrel_list = word_tokenize(new_tokn) #
    test_bow = word_tokenize(new_ttoks) #toks from IS2

    #print("RELATED LIST******************************************************: \n")#, rel_list)


    rd = {}
    nd = {}
    td = {}
    almighty_dict ={} 

    for rt in rel_list:
        rd[rt] = (rd.get(rt,0) + 1)
    for nrt in unrel_list:
        nd[nrt] = (nd.get(nrt,0) + 1)
    for tt in test_bow:
        td[tt] = (td.get(tt,0) + 1)

    return rd, nd, td

#before this function a dictionary is filled with no
def isInDoc(json, it_ter, cd): #this is more used for the log but idc
    #bagofwords = []

    cd = {}
#    bagofwords.append(json[i]['Title'] + " " + json[i]['Summary'])
#    bagofwords = bagofwords.split(' ')
#    excluded = set(string.punctuation)
#    new_toks = [','.join(d.lower() for d in bagofwords if d not in stop_words and d not in excluded)]
    new_toks = tok_func(json, it_ter, False)
    for i in new_toks:
        cd[i][it_ter] = 1
    return cd

def counter(json, it = None, isIt=True): #maybe use sections for log but idc
    new_toks = tok_func(json, it, isIt)
    county = []
    for i in new_toks:
        if i not in county:
            county.append(i)
    return len(county), county
    
def rocchio(json, query, ALPHA=1, BETA=0.75, GAMMA=0.15):
    d1fl = float(BETA/relevant_quant) if relevant_quant else 0.0
    d2fl = float(GAMMA/irrelevant_quant) if irrelevant_quant else 0.0
    lenlist, wordlist = counter(json)
    q0, q1, d1sum, d2sum = [0]*lenlist, [0]*lenlist, [0]*lenlist, [0]*lenlist 
    d1, d2, trash = inverted(json)
    spot = [-1] * lenlist

    q = word_tokenize(query)
    qq = [x.lower() for x in q]

    for i in range(len(qq)):
        for x in range(lenlist):
            if qq[i] == wordlist[x]:
                q1[x] += 1
                #spot.append(x)
                spot[x] = i


    for i in range(lenlist):
        wrd = wordlist[i]
        d1sum[i] += d1.get(wrd,0)
        d2sum[i] += d2.get(wrd,0)
    
    for i in range(lenlist):
        d1sum[i] = float(d1fl*d1sum[i])
        d2sum[i] = float(d2fl*d2sum[i])
        q1[i] = float(ALPHA*q1[i])
        q0[i] += (d1sum[i] + d2sum[i] + q1[i])
    
    max1, max2, in1, in2 = 0, 0, 0, 0
    #print(wordlist[in1], wordlist[in2])
    #print(q0)
    for i in range(lenlist):
        
        #if q0[i] >= max1 and i not in spot and wordlist[i] not in stop_words and wordlist[i] != "wikipedia" and wordlist[i] not in q:
        if q0[i] >= max1 and wordlist[i] not in stop_words and wordlist[i] != "wikipedia" and wordlist[i] not in q:
            #print('word: {}, q: {}, wordnotinq bool: {}'.format(wordlist[i], q, wordlist not in q))
            max1 = q0[i]
            in1 = i

            q0[i] = 0

        if q0[i] >= max2 and wordlist[i] not in stop_words and wordlist[i] != "wikipedia" and wordlist[i] not in q:
            #print('word: {}, q: {}, wordnotinq bool: {}'.format(wordlist[i], q, wordlist not in q))
            max2 = q0[i]
            in2 = i
            
            q0[i] = 0
            

    #print(wordlist)
    #print(lenlist)
    #print('q: {}'.format(q))
    #print('to return: "{}" "{}"'.format(wordlist[in1], wordlist[in2]))
    return wordlist[in1], wordlist[in2]

    def wrapup():
        pass


def tok_func(json, it = None, isIt = True):
    bagofwords = []
    baggy = ""
    if(isIt):
        for i in range(len(json)):
            baggy += (json[i]['Title'] + " " + json[i]['Summary'])
    else: 
        baggy = (json[it]['Title'] + " " + json[it]['Summary'])
    
    #print("PRE BOW: ", bagofwords)
    #bagofwords = baggy.split(' ')
    #print("POST BOW: ", bagofwords)
    toks = word_tokenize(baggy)
    excluded = set(string.punctuation)
    excluded.add("...")
    excluded.add("'s")
    excluded.add('·')
    excluded.add('the')

    new_toks = ' '.join(d.lower() for d in toks if d not in stop_words and d not in excluded)
    #new_toks = [','.join(d.lower() for d in bagofwords if d not in stop_words and d not in excluded)]
    new = word_tokenize(new_toks)
    #print("LAST TRY", new)
    
    return new


if __name__ == '__main__':
    client_key = sys.argv[1]
    engine_key = sys.argv[2]
    precision = float(sys.argv[3])
    query = sys.argv[4].lower()

    precision_met = False

    while not precision_met:
        print_parameters(client_key, engine_key, query, precision)
        results_json, acheived_precision = user_interaction(client_key, engine_key, query)
        feedback_summary(query, acheived_precision, precision)
        if acheived_precision < precision:
            for i in range(2):
                print("Indexing results ....")
            w1, w2= rocchio(results_json, query)
            print('Augmenting by  {} {}'.format(w1, w2))
            query += " " +  w1 + " " + w2
        else:
            precision_met = True
