# parameters: python3 project2.py [-spanbert|-gpt3] <google api key> <google engine id> <openai secret key> <r> <t> <q> <k>

import sys
import time
import requests
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import spacy
from spacy_help_functions import get_entities, create_entity_pairs
from spanbert import SpanBERT
import openai

'''
method = ""     # -spanbert or -gpt3
api_key = ""    # google api
engine_key = "" # google search engine
secret_key = "" # openapi key
relation = 0    # 1 - 4
threshold = 0   # 0 to 1
query = ""      # seed relation pair
tuples = 0      # number of tuples requested
'''

# prints parameters for api
#doesn't seem to be important
def print_parameters():
    parameters = """\
Parameters:
Client key      = {}
Engine key      = {}
OpenAI key      = {}
Method  = {}
Relation        = {}
Threshold       = {}
Query           = {}
# of Tuples     = {}
Loading necessary libraries; This should take a minute or so ...\
"""
    print(
        parameters.format(
            api_key, engine_key, secret_key, method[1:], relations[relation]['relation'], threshold, query, tuples
        )
    )


# fetches results from api
def get_results(api_key, query, engine_key):
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


def extract_plaintext(webpage):
    print("Fetching text from url ...")
    r = requests.get(webpage)
    soup = BeautifulSoup(r.content, features="html.parser")
    soup = BeautifulSoup(r.content, 'html5lib')
    print("SOUPPPP\n", soup)

    # get rid of non-html elements
    for script in soup(["script", "style", "[document]", "head", "title", "header", "footer", "meta"]):
        script.extract()

    # getting text from page body
    text = soup.body.get_text(separator=' ')

    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)    

    # truncate to 10000 if needed
    
    if len(text) > 10000:
        print('Trimming webpage content from {} to 10000 characters'.format(len(text)))
        text = text[:10000]
    

    print('Webpage length (num characters): {}'.format(len(text)))
    return text


def spacy_entity_extraction(plaintext):
    print('Annotating the webpage using spacy...')
    nlp = spacy.load("en_core_web_lg")
    doc = nlp(plaintext)
    print('Extracted {} sentences. Processing each sentence one by one to check for presence of right pair of named entity types; if so, will run the second pipeline ...'.format(len(list(doc.sents))))

    #all_candidate_pairs = []
    processed_counter = 0
    extracted_sentence_counter = 0
    for sentence in doc.sents:
        ents = get_entities(sentence, relations[relation]['entities_of_interest'])
        
        # create entity pairs
        candidate_pairs = []
        # entity pairs created are already only for the desired entities
        sentence_entity_pairs = create_entity_pairs(sentence, relations[relation]['entities_of_interest'])
        for ep in sentence_entity_pairs:
            # only taking relations that fit the desired relation pairs
            if ep[1][1] == relations[relation]['subject'] and ep[2][1] != relations[relation]['subject']:
                candidate_pairs.append({"tokens": ep[0], "subj": ep[1], "obj": ep[2]})  # e1=Subject, e2=Object
            elif ep[2][1] == relations[relation]['subject'] and ep[1][1] != relations[relation]['subject']:
                candidate_pairs.append({"tokens": ep[0], "subj": ep[2], "obj": ep[1]})  # e1=Object, e2=Subject

        
        # process using gpt or bert if valid pairs exist
        if len(candidate_pairs) > 0:
            extracted_sentence_counter += 1

            if method == '-gpt3':
                # if gpt, use sentence without annotation to run through gpt
                gpt_classification(candidate_pairs, sentence)
            elif method == '-spanbert':
                # if spanbert, run candidate pairs straight through bert prediction
                spanbert_classification(candidate_pairs, sentence)


        #all_candidate_pairs.append(candidate_pairs)
        # print progress message
        processed_counter += 1
        if processed_counter % 5 == 0:
            print('Processed {} / {} sentences'.format(processed_counter, len(list(doc.sents))))

    print('Extracted annotations for  {}  out of total  {}  sentences'.format(extracted_sentence_counter, len(list(doc.sents))))

    #return all_candidate_pairs

def get_openai_completion(prompt, model, max_tokens, temperature = 0.2, top_p = 1, frequency_penalty = 0, presence_penalty =0):
    response = openai.Completion.create(
        model=model,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )
    response_text = response['choices'][0]['text']
    return response_text

def gpt_classification(candidate_pairs, sentence):
    # load gpt api and prompt
    prompt_text = """ Given a sentence, extract all the Nouns.

sentence: Rob is an engineer at NASA and he lives in California.
extracted: """

    model = 'text-davinci-003'
    max_tokens = 100
    temperature = 0.2
    top_p = 1
    frequency_penalty = 0
    presence_penalty = 0

    response_text = get_openai_completion(prompt_text, model, max_tokens, temperature, top_p, frequency_penalty, presence_penalty)
    print(response_text)

    #for pair in candidate_pairs:
    #    print('sent: {}\nsubj: {}\nobj: {}\n'.format(sentence, pair['subj'][0], pair['obj'][0]))

def spanbert_classification(candidate_pairs, sentence):
    # Load pre-trained SpanBERT model
    spanbert = SpanBERT("./pretrained_spanbert")

    relation_preds = spanbert.predict(candidate_pairs)  # get predictions: list of (relation, confidence) pairs

    # Print Extracted Relations
    print("\nExtracted relations:")
    for ex, pred in list(zip(candidate_pairs, relation_preds)):
        print("\tSubject: {}\tObject: {}\tRelation: {}\tConfidence: {:.2f}".format(ex["subj"][0], ex["obj"][0], pred[0], pred[1]))
    

def process_urls(api_key, query, engine_key):
    global iterations
    # top print tag
    print('=========== Iteration: {} - Query: {} ===========\n\n'.format(iterations, query))
    urls = get_results(api_key, query, engine_key)

    # processing each individual url
    for i in range(len(urls)):
        print('URL ( {} / {}): {}\n'.format(i + 1, len(urls), urls[i]))
        webpage = requests.get(urls[i], timeout=5)
        plaintext = extract_plaintext(webpage.content)
        
        spacy_entity_extraction(plaintext)



if __name__ == "__main__":
    try:
        method = sys.argv[1]            # -spanbert or -gpt3
        api_key = sys.argv[2]           # google api
        engine_key = sys.argv[3]        # google search engine
        secret_key = sys.argv[4]        # openapi key
        relation = int(sys.argv[5])     # 1 - 4
        threshold = float(sys.argv[6])  # 0 to 1
        query = sys.argv[7].lower()     # seed relation pair
        tuples = int(sys.argv[8])       # number of tuples requested
    except:
        print("invalid parameter list")

    X = set()           # set of extracted tuples
    Q = set()           # set of previously used queries
    OldURLs = set()     # set of previously used URLs
    iterations = 0

    relations = {
        1: {
            'relation': "Schools_Attended",
            'bert-relation': 'schools_attended',
            'entities_of_interest': ["ORGANIZATION", "PERSON"],
            'subject': "PERSON",
            },
        2: {
            'relation': "Work_For",
            'bert-relation': 'employee_of',
            'entities_of_interest': ["ORGANIZATION", "PERSON"],
            'subject': "PERSON"
            },
        3: {'relation': "Live_In",
            'bert-relation': '',
            'entities_of_interest': ["PERSON", "LOCATION", "CITY", "STATE_OR_PROVINCE", "COUNTRY"],
            'subject': "PERSON"
            },
        4: {'relation': "Top_Member_Employee",
            'entities_of_interest': ["ORGANIZATION", "PERSON"],
            'subject': "PERSON"
            }
    }

    # adding query parameter to used queries
    Q.add(query)

    # print parameters
    #print_parameters()

    # run iterations until desired tuples extracted
    #while len(X) < tuples:
    process_urls(api_key,query,engine_key)