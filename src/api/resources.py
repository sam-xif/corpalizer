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


class Document(Resource):
    def get(self, doc_uuid):
        pass

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
        # for start, end, paragraph_text in paragraphs:
        #


        cur.execute('SELECT paragraph_id, position_in_fulltext FROM paragraph WHERE document_id = %s', (doc_uuid,))
        for paragraph_id, position_in_fulltext, in cur.fetchall():
            sentences = break_paragraph_into_sentences([text for s, e, text in paragraphs if s == position_in_fulltext][0])

            cur.execute('INSERT INTO sentence (paragraph_id, position_in_paragraph) VALUES ' + ','.join(['(%s, %s)' for i in range(len(sentences))]),
                        tuple(chain.from_iterable(((str(paragraph_id), s[0]) for s in sentences))))
            # TODO: create linkage between terms and sentences here



        # process raw text into a list of unique stemmed words to be added to terms
        # add the terms that dont already exist to the db, and then add document_term links
        terms = process_raw_document_into_terms(text)
        print(terms)
        cur.execute('INSERT IGNORE INTO term (term_text) VALUES ' + ','.join(['(%s)' for i in range(len(terms))]), tuple(terms))
        cnt = Counter(terms)
        cur.execute('INSERT INTO document_term (frequency, document_id, term_text) VALUES ' + ','.join(['(%s, %s, %s)' for i in range(len(cnt.most_common()))]),
                    tuple(chain.from_iterable((f, str(doc_uuid), t) for t, f in cnt.most_common())))

        cur.callproc('recompute_all_tfidf_scores')  # recomputes tfidf scores at the database level

        get_mysql().connection.commit()

        # Return document uuid as response
        return {
            'doc_uuid': str(doc_uuid)
        }, 201

    def put(self, doc_uuid):
        pass

    def delete(self, doc_uuid):
        pass
