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
from itertools import chain
from collections import Counter
from datetime import datetime


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


def generate_topics(
        terms_list,
        similarity_score_fn,
        geometric_mean_of_tfidf_scores_for_term_fn,
        set_progress_callback=None,
        poll_cancel=None,
):
    """
    Generates a list of topics
    :param terms_list: The full list of terms
    :param similarity_score_fn: A function (term1, term2) -> similarity_score
    :param geometric_mean_of_tfidf_scores_for_term_fn: A function with the signature (term -> float) that takes a term and produces the geometric mean of tfidf scores for that term across all documents
    :return: The list of topics (a list of list of terms), sorted in descending order of significance
    """
    THRESH = 0.001

    L = []
    for i, t in enumerate(terms_list):

        if poll_cancel is not None and poll_cancel() is True:
            raise Exception('cancelled')

        was_added = False
        for topic in L:
            if all([similarity_score_fn(t, topic_term) < THRESH if similarity_score_fn(t, topic_term) is not None else False for topic_term in topic]):
                topic.append(t)
                was_added = True
                break
        if not was_added:
            L.append([t])
        if set_progress_callback is not None:
            set_progress_callback(i / len(terms_list))

    return sorted(L, key=lambda l: sum(map(geometric_mean_of_tfidf_scores_for_term_fn, l)) / len(l), reverse=True)


def insert_document(doc_uuid, text, cursor):
    """
    Performs the setup required to ingest a new document into the database.
    This function configures the document, its paragraphs, its sentences, and the terms associated with each of these.
    This function does not recompute the tfidf scores.
    :param doc_uuid: The UUID of the document
    :param text: The raw text of the document
    :param cursor: The database cursor
    """

    """
    Create document entry
    """
    cursor.execute('INSERT INTO document (document_id, timestamp) VALUES (%s, %s)', (doc_uuid, datetime.now()))

    """
    Process document's raw text into terms
    """
    terms = process_raw_document_into_terms(text)
    if len(terms) > 0:
        cursor.execute('INSERT IGNORE INTO term (term_text) VALUES ' + ','.join(['(%s)' for i in range(len(terms))]),
                    tuple(terms))
        cnt = Counter(terms)
        cursor.execute('INSERT INTO document_term (frequency, document_id, term_text) VALUES ' + ','.join(
            ['(%s, %s, %s)' for i in range(len(cnt.most_common()))]),
                    tuple(chain.from_iterable((f, str(doc_uuid), t) for t, f in cnt.most_common())))

    """
    Break document down into paragraphs and insert those records
    """
    paragraphs = break_document_into_paragraphs(text)
    if len(paragraphs) > 0:
        cursor.execute('INSERT INTO paragraph (document_id, position_in_fulltext) VALUES ' + ','.join(
            ['(%s, %s)' for i in range(len(paragraphs))]),
                    tuple(chain.from_iterable(((str(doc_uuid), p[0]) for p in paragraphs))))

    for start, end, paragraph_text in paragraphs:
        cursor.execute('SELECT paragraph_id FROM paragraph WHERE document_id = %s AND position_in_fullText = %s',
                    (str(doc_uuid), start))
        paragraph_id, = cursor.fetchone()

        # The following four lines are abstractable
        terms = process_raw_document_into_terms(paragraph_text)
        if len(terms) > 0:
            cursor.execute('INSERT IGNORE INTO term (term_text) VALUES ' + ','.join(['(%s)' for i in range(len(terms))]),
                        tuple(terms))
            cnt = Counter(terms)
            cursor.execute('INSERT INTO paragraph_term (frequency, paragraph_id, term_text) VALUES ' + ','.join(
                ['(%s, %s, %s)' for i in range(len(cnt.most_common()))]),
                        tuple(chain.from_iterable((f, paragraph_id, t) for t, f in cnt.most_common())))

    """
    Break each paragraph down into sentences and insert those records
    """
    cursor.execute('SELECT paragraph_id, position_in_fulltext FROM paragraph WHERE document_id = %s', (doc_uuid,))
    for paragraph_id, position_in_fulltext in cursor.fetchall():
        sentences = break_paragraph_into_sentences([text for s, e, text in paragraphs if s == position_in_fulltext][0])
        if len(sentences) > 0:
            cursor.execute('INSERT INTO sentence (paragraph_id, position_in_paragraph) VALUES ' + ','.join(
                ['(%s, %s)' for i in range(len(sentences))]),
                        tuple(chain.from_iterable(((str(paragraph_id), s[0]) for s in sentences))))

        for start, end, sentence_text in sentences:
            cursor.execute('SELECT sentence_id FROM sentence WHERE paragraph_id = %s AND position_in_paragraph = %s',
                        (paragraph_id, start))
            sentence_id, = cursor.fetchone()

            terms = process_raw_document_into_terms(sentence_text)
            if len(terms) > 0:
                cursor.execute(
                    'INSERT IGNORE INTO term (term_text) VALUES ' + ','.join(['(%s)' for i in range(len(terms))]),
                    tuple(terms))
                cnt = Counter(terms)
                cursor.execute('INSERT INTO sentence_term (frequency, sentence_id, term_text) VALUES ' + ','.join(
                    ['(%s, %s, %s)' for i in range(len(cnt.most_common()))]),
                            tuple(chain.from_iterable((f, sentence_id, t) for t, f in cnt.most_common())))


def recompute_tfidf_scores(cursor):
    """
    Recomputes all tfidf scores in the database
    :param cursor: The database cursor
    """
    cursor.callproc('recompute_all_document_tfidf_scores')
    cursor.callproc('recompute_all_paragraph_tfidf_scores')
    cursor.callproc('recompute_all_sentence_tfidf_scores')
