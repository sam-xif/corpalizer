import os
import uuid
from collections import Counter
from datetime import datetime
from flask import request, current_app as app
from flask_restful import Resource, reqparse
from api.services import (
    break_document_into_paragraphs,
    break_paragraph_into_sentences,
    process_raw_document_into_terms,
    generate_topics,
)
from itertools import chain
import math


class DocumentRetrieveUpdateDeleteResource(Resource):
    def get(self, doc_uuid):
        """
        Retrieves document content
        :param doc_uuid:
        :return:
        """
        with open(os.path.join(app.config['documents_dir'], '{}.txt'.format(doc_uuid)), 'r') as f:
            out = f.read()

        return {
            'content': out
        }, 200

    def put(self, doc_uuid):
        """
        Updates document, and database
        :param doc_uuid:
        :return:
        """
        pass

    def delete(self, doc_uuid):
        """
        Deletes document, from filesystem and from database
        :param doc_uuid:
        :return:
        """
        pass


class DocumentListCreateResource(Resource):
    def get(self):
        from src.api import get_mysql
        cur = get_mysql().connection.cursor()

        cur.execute('SELECT document_id, timestamp FROM document LIMIT 1000')
        tuples = cur.fetchall()

        return {
            'documents': [{'id': doc_id, 'date': date.strftime('%Y-%m-%d')} for doc_id, date in tuples]
        }, 200

    def post(self):
        from src.api import get_mysql

        parser = reqparse.RequestParser()
        parser.add_argument('content')
        args = parser.parse_args()
        text = args.content
        if text is None:
            return {
                'error': 'no content'
            }, 400

        doc_uuid = uuid.uuid4()
        cur = get_mysql().connection.cursor()

        # Create file
        with open(os.path.join(app.config['documents_dir'], '{}.txt'.format(doc_uuid)), 'w+') as f:
            f.write(text)

        # create db record
        cur.execute('INSERT INTO document (document_id, timestamp) VALUES (%s, %s)', (doc_uuid, datetime.now()))

        # Break document down into paragraphs and sentences and create those records
        paragraphs = break_document_into_paragraphs(text)
        if len(paragraphs) > 0:
            cur.execute('INSERT INTO paragraph (document_id, position_in_fulltext) VALUES ' + ','.join(['(%s, %s)' for i in range(len(paragraphs))]),
                        tuple(chain.from_iterable(((str(doc_uuid), p[0]) for p in paragraphs))))
        # TODO: create linkage between terms and paragraphs here
        for start, end, paragraph_text in paragraphs:
            cur.execute('SELECT paragraph_id FROM paragraph WHERE document_id = %s AND position_in_fullText = %s', (str(doc_uuid), start))
            paragraph_id, = cur.fetchone()

            # The following four lines are abstractable
            terms = process_raw_document_into_terms(paragraph_text)
            if len(terms) > 0:
                cur.execute('INSERT IGNORE INTO term (term_text) VALUES ' + ','.join(['(%s)' for i in range(len(terms))]), tuple(terms))
                cnt = Counter(terms)
                cur.execute('INSERT INTO paragraph_term (frequency, paragraph_id, term_text) VALUES ' + ','.join(
                    ['(%s, %s, %s)' for i in range(len(cnt.most_common()))]),
                            tuple(chain.from_iterable((f, paragraph_id, t) for t, f in cnt.most_common())))

        cur.execute('SELECT paragraph_id, position_in_fulltext FROM paragraph WHERE document_id = %s', (doc_uuid,))
        for paragraph_id, position_in_fulltext in cur.fetchall():
            sentences = break_paragraph_into_sentences([text for s, e, text in paragraphs if s == position_in_fulltext][0])
            if len(sentences) > 0:
                cur.execute('INSERT INTO sentence (paragraph_id, position_in_paragraph) VALUES ' + ','.join(['(%s, %s)' for i in range(len(sentences))]),
                            tuple(chain.from_iterable(((str(paragraph_id), s[0]) for s in sentences))))

            for start, end, sentence_text in sentences:
                cur.execute('SELECT sentence_id FROM sentence WHERE paragraph_id = %s AND position_in_paragraph = %s',
                            (paragraph_id, start))
                sentence_id, = cur.fetchone()

                terms = process_raw_document_into_terms(sentence_text)
                if len(terms) > 0:
                    cur.execute(
                        'INSERT IGNORE INTO term (term_text) VALUES ' + ','.join(['(%s)' for i in range(len(terms))]),
                        tuple(terms))
                    cnt = Counter(terms)
                    cur.execute('INSERT INTO sentence_term (frequency, sentence_id, term_text) VALUES ' + ','.join(
                        ['(%s, %s, %s)' for i in range(len(cnt.most_common()))]),
                                tuple(chain.from_iterable((f, sentence_id, t) for t, f in cnt.most_common())))

        # process raw text into a list of unique stemmed words to be added to terms
        # add the terms that dont already exist to the db, and then add document_term links
        terms = process_raw_document_into_terms(text)
        if len(terms) > 0:
            cur.execute('INSERT IGNORE INTO term (term_text) VALUES ' + ','.join(['(%s)' for i in range(len(terms))]), tuple(terms))
            cnt = Counter(terms)
            cur.execute('INSERT INTO document_term (frequency, document_id, term_text) VALUES ' + ','.join(['(%s, %s, %s)' for i in range(len(cnt.most_common()))]),
                        tuple(chain.from_iterable((f, str(doc_uuid), t) for t, f in cnt.most_common())))

        cur.callproc('recompute_all_document_tfidf_scores')
        cur.callproc('recompute_all_paragraph_tfidf_scores')
        cur.callproc('recompute_all_sentence_tfidf_scores')

        get_mysql().connection.commit()

        # Return document uuid as response
        return {
            'doc_uuid': str(doc_uuid)
        }, 201


class TrendsResource(Resource):
    """
    A resource for getting term trends
    """

    GRANULARITY_DOCUMENT = 'document'
    GRANULARITY_PARAGRAPH = 'paragraph'
    GRANULARITY_SENTENCE = 'sentence'

    BIN_DAY = 'day'
    BIN_MONTH = 'month'
    BIN_YEAR = 'year'

    def get(self, granularity, term_text):
        from src.api import get_mysql

        cur = get_mysql().connection.cursor()

        bin_type = request.args.get('bin_type')

        if granularity == self.GRANULARITY_DOCUMENT:
            cur.execute('SELECT frequency, timestamp FROM document_term JOIN document USING (document_id) WHERE term_text = %s', (term_text,))
            freq_date_pairs = cur.fetchall()
        elif granularity == self.GRANULARITY_PARAGRAPH:
            cur.execute(
                'SELECT frequency, timestamp FROM paragraph_term JOIN paragraph USING (paragraph_id) JOIN document USING (document_id) WHERE term_text = %s',
                (term_text,))
            freq_date_pairs = cur.fetchall()
        elif granularity == self.GRANULARITY_SENTENCE:
            cur.execute(
                'SELECT frequency, timestamp FROM sentence_term JOIN sentence USING (sentence_id) JOIN paragraph USING (paragraph_id) JOIN document USING (document_id) WHERE term_text = %s',
                (term_text,))
            freq_date_pairs = cur.fetchall()
        else:
            return {
                'error': 'unknown granularity'
            }, 400

        date_to_freq_map = {}
        date_format = {
            self.BIN_DAY: '%Y-%m-%d',
            self.BIN_MONTH: '%Y-%m',
            self.BIN_YEAR: '%Y',
        }
        for freq, date in freq_date_pairs:
            key = date.strftime(date_format[bin_type])
            if key in date_to_freq_map:
                date_to_freq_map[key] += freq
            else:
                date_to_freq_map[key] = freq

        return {
            'data': date_to_freq_map
        }, 200


class TopicsResource(Resource):
    def get(self):
        from src.api import get_mysql

        cur = get_mysql().connection.cursor()

        cur.execute('SELECT term_text FROM term')
        terms_list = [x[0] for x in cur.fetchall()]

        similarity_score_fn_memo = {}

        def similarity_score_fn(t1, t2):
            if (t1, t2) in similarity_score_fn_memo:
                return similarity_score_fn_memo[t1, t2]
            cur.execute('SELECT compute_similarity_score(%s, %s)', (t1, t2))
            ret = cur.fetchone()[0]
            similarity_score_fn_memo[(t1, t2)] = ret
            similarity_score_fn_memo[(t2, t1)] = ret
            return ret

        def geometric_mean_of_tfidf_scores_for_term_fn(term):
            cur.execute('SELECT score FROM document_term WHERE term_text = %s', (term,))
            scores = cur.fetchall()
            product = 1
            for score, in scores:
                product *= score
            product = math.pow(product, 1 / len(scores))
            return product

        print('here!')

        return {
            'data': generate_topics(terms_list, similarity_score_fn, geometric_mean_of_tfidf_scores_for_term_fn)
        }
