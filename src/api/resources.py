import os
import uuid
from collections import Counter
from datetime import datetime
from flask import request, current_app as app
from flask_restful import Resource, reqparse
from src.api.services import (
    break_document_into_paragraphs,
    break_paragraph_into_sentences,
    process_raw_document_into_terms,
)
from itertools import chain


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


class DocumentCreateResource(Resource):
    def post(self):
        from src.api import get_mysql

        parser = reqparse.RequestParser()
        parser.add_argument('content')
        args = parser.parse_args()
        text = args.content

        doc_uuid = uuid.uuid4()
        cur = get_mysql().connection.cursor()

        # Create file
        with open(os.path.join(app.config['documents_dir'], '{}.txt'.format(doc_uuid)), 'w+') as f:
            f.write(text)

        # create db record
        cur.execute('INSERT INTO document (document_id, timestamp) VALUES (%s, %s)', (doc_uuid, datetime.now()))

        # Break document down into paragraphs and sentences and create those records
        paragraphs = break_document_into_paragraphs(text)
        cur.execute('INSERT INTO paragraph (document_id, position_in_fulltext) VALUES ' + ','.join(['(%s, %s)' for i in range(len(paragraphs))]),
                    tuple(chain.from_iterable(((str(doc_uuid), p[0]) for p in paragraphs))))
        # TODO: create linkage between terms and paragraphs here
        for start, end, paragraph_text in paragraphs:
            cur.execute('SELECT paragraph_id FROM paragraph WHERE document_id = %s AND position_in_fullText = %s', (str(doc_uuid), start))
            paragraph_id, = cur.fetchone()

            # The following four lines are abstractable
            terms = process_raw_document_into_terms(paragraph_text)
            cur.execute('INSERT IGNORE INTO term (term_text) VALUES ' + ','.join(['(%s)' for i in range(len(terms))]), tuple(terms))
            cnt = Counter(terms)
            cur.execute('INSERT INTO paragraph_term (frequency, paragraph_id, term_text) VALUES ' + ','.join(
                ['(%s, %s, %s)' for i in range(len(cnt.most_common()))]),
                        tuple(chain.from_iterable((f, paragraph_id, t) for t, f in cnt.most_common())))

        cur.execute('SELECT paragraph_id, position_in_fulltext FROM paragraph WHERE document_id = %s', (doc_uuid,))
        for paragraph_id, position_in_fulltext, in cur.fetchall():
            sentences = break_paragraph_into_sentences([text for s, e, text in paragraphs if s == position_in_fulltext][0])

            cur.execute('INSERT INTO sentence (paragraph_id, position_in_paragraph) VALUES ' + ','.join(['(%s, %s)' for i in range(len(sentences))]),
                        tuple(chain.from_iterable(((str(paragraph_id), s[0]) for s in sentences))))

            for start, end, sentence_text in sentences:
                cur.execute('SELECT sentence_id FROM sentence WHERE paragraph_id = %s AND position_in_paragraph = %s',
                            (paragraph_id, start))
                sentence_id, = cur.fetchone()

                terms = process_raw_document_into_terms(sentence_text)
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
