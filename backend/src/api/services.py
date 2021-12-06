"""
Service functions for the API resources
"""

import nltk
nltk.download('stopwords')

from nltk import RegexpTokenizer
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from pysbd import Segmenter
from tqdm import tqdm


def break_document_into_paragraphs(doc):
    """
    Extracts information about paragraphs in the given document
    :param doc: The document text
    :return: A list of 3-tuples, which are start and end indices of each paragraph within the given string, and the paragraph text itself as the third item
    """
    splits = []
    last_end = 0
    for i, char in enumerate(doc):
        if char == '\n':
            splits.append((last_end, i, doc[last_end:i]))
            last_end = i

    splits.append((last_end, len(doc), doc[last_end:]))

    return splits


def break_paragraph_into_sentences(doc):
    """
    Extracts information about sentences from the given paragraph
    :param doc: The paragraph text
    :return: A list of 3-tuples, which are start and end indices of each sentence within the given string, and the text itself as the third item
    """
    seg = Segmenter(char_span=True)

    processed_doc = seg.segment(doc)
    return [(s.start, s.end, s.sent) for s in processed_doc]


def process_raw_document_into_terms(text):
    """
    Processes the given raw document text into terms
    :param text: The raw text to process
    :return: A set of terms
    """
    # TODO: Include position information for each of the terms
    stop_words = set(stopwords.words('english'))
    stemmer = PorterStemmer()
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = [stemmer.stem(w.lower()) for w in tokenizer.tokenize(text) if w.lower() not in stop_words]
    return tokens


def generate_topics(terms_list, similarity_score_fn, geometric_mean_of_tfidf_scores_for_term_fn):
    """
    Generates a list of topics
    :param terms_list: The full list of terms
    :param similarity_score_fn: A function (term1, term2) -> similarity_score
    :param geometric_mean_of_tfidf_scores_for_term_fn: A function with the signature (term -> float) that takes a term and produces the geometric mean of tfidf scores for that term across all documents
    :return: The list of topics (a list of list of terms), sorted in descending order of significance
    """
    THRESH = 0.001

    L = []
    for t in tqdm(terms_list):
        was_added = False
        for topic in L:
            if all([similarity_score_fn(t, topic_term) < THRESH for topic_term in topic]):
                topic.append(t)
                was_added = True
                break
        if not was_added:
            L.append([t])

    return sorted(L, key=lambda l: sum(map(geometric_mean_of_tfidf_scores_for_term_fn, l)) / len(l), reverse=True)
