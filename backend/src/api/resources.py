import os
import uuid
from flask import request, current_app as app
from flask_restful import Resource, reqparse
from api.services import (
    generate_topics,
    insert_document,
    recompute_tfidf_scores,
)
import math
from datetime import timedelta
from threading import Thread, Lock
import pymysql


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
        from api import get_mysql

        parser = reqparse.RequestParser()
        parser.add_argument('content')
        args = parser.parse_args()
        text = args.content
        if text is None:
            return {
                'error': 'no content'
            }, 400

        # Create file
        with open(os.path.join(app.config['documents_dir'], '{}.txt'.format(doc_uuid)), 'w+') as f:
            f.write(text)

        cur = get_mysql().connection.cursor()

        cur.execute('DELETE FROM document WHERE document_id = %s', (doc_uuid,))
        insert_document(doc_uuid, text, cur)
        recompute_tfidf_scores(cur)
        cur.callproc('cleanup_terms')

        get_mysql().connection.commit()
        return 204, None

    def delete(self, doc_uuid):
        """
        Deletes document, from filesystem and from database
        :param doc_uuid:
        :return:
        """
        from api import get_mysql
        cur = get_mysql().connection.cursor()
        try:
            os.remove(os.path.join(app.config['documents_dir'], '{}.txt'.format(doc_uuid)))
        except FileNotFoundError:
            print("Corresponding file wasn't found")

        cur.execute('DELETE FROM document WHERE document_id = %s', (doc_uuid,))
        recompute_tfidf_scores(cur)
        cur.callproc('cleanup_terms')

        get_mysql().connection.commit()
        return 204, None


class DocumentListCreateResource(Resource):
    def get(self):
        from api import get_mysql
        cur = get_mysql().connection.cursor()

        cur.execute('SELECT document_id, timestamp FROM document LIMIT 1000')
        tuples = cur.fetchall()

        return {
            'documents': [{'id': doc_id, 'date': date.strftime('%Y-%m-%d')} for doc_id, date in tuples]
        }, 200

    def post(self):
        from api import get_mysql

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

        insert_document(doc_uuid, text, cur)
        recompute_tfidf_scores(cur)

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
        from api import get_mysql

        cur = get_mysql().connection.cursor()

        bin_type = request.args.get('bin_type', self.BIN_DAY)

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
        import random
        for freq, date in freq_date_pairs:
            key = (date - timedelta(days=random.randint(1, 100))).strftime(date_format[bin_type])
            if key in date_to_freq_map:
                date_to_freq_map[key] += freq
            else:
                date_to_freq_map[key] = freq

        return {
            'data': date_to_freq_map
        }, 200


class TopicsResource(Resource):
    topic_thread = None
    topic_thread_lock = Lock()
    cached_results = {}

    cancel_token = None
    cancel_token_lock = Lock()

    @classmethod
    def _compute_topics(cls, cancellation_token, cancellation_token_lock):
        from api import pymysql_connect_kwargs
        conn = pymysql.connect(**pymysql_connect_kwargs)

        cur = conn.cursor()

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

        def set_progress(progress):
            cls.topic_thread_lock.acquire()
            txid, _, thread = cls.topic_thread
            cls.topic_thread = (txid, progress, thread)
            cls.topic_thread_lock.release()

        def poll_cancel():
            cancellation_token_lock.acquire()
            ret = cancellation_token[0]
            cancellation_token_lock.release()
            return ret

        try:
            results = generate_topics(
                terms_list,
                similarity_score_fn,
                geometric_mean_of_tfidf_scores_for_term_fn,
                set_progress_callback=set_progress,
                poll_cancel=poll_cancel,
            )

            cls.topic_thread_lock.acquire()
            txid = cls.topic_thread[0]
            cls.cached_results[txid] = results
            cls.topic_thread_lock.release()
        except Exception as e:
            pass

        cur.close()
        conn.close()

    @classmethod
    def get(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('transaction_id')
        parser.add_argument('cancel')
        args = parser.parse_args()

        txid = int(args.transaction_id) if args.transaction_id is not None else None
        cancel = bool(args.cancel) if args.cancel is not None else None

        if txid in cls.cached_results:
            cls.topic_thread_lock.acquire()
            if cls.topic_thread is not None and txid == cls.topic_thread[0]:
                cls.topic_thread = None
            cls.topic_thread_lock.release()
            return {
                'status': 'done',
                'result': cls.cached_results[txid]
           }, 200

        if cls.topic_thread is not None:
            if cancel is True:
                cls.cancel_token_lock.acquire()
                cls.cancel_token[0] = True
                cls.cancel_token_lock.release()

                cls.topic_thread_lock.acquire()
                txid, _, thread = cls.topic_thread
                cls.topic_thread_lock.release()

                thread.join()

                cls.topic_thread = None

                return {
                    'status': 'cancelled',
                    'transaction_id': txid,
                }, 200

            cls.topic_thread_lock.acquire()
            running_txid, progress, thread = cls.topic_thread
            if txid == running_txid:
                if progress == 1 and txid in cls.cached_results:
                    cls.topic_thread = None
                    cls.topic_thread_lock.release()
                    return {
                        'status': 'done',
                        'result': cls.cached_results[txid],
                       }, 200
                else:
                    cls.topic_thread_lock.release()
                    return {
                        'status': 'running',
                        'progress': progress,
                    }, 200
            else:
                cls.topic_thread_lock.release()
                return {
                    'error': 'Cannot start a new transaction while one is running. Supply the currently running transaction ID to view its status.'
                }, 400

        if cancel is True:
            return {
                'error': 'No transaction to cancel'
            }, 400

        txid = max(cls.cached_results.keys()) + 1 if len(cls.cached_results.keys()) > 0 else 0
        cls.cancel_token = [False]
        thread = Thread(target=cls._compute_topics, args=(cls.cancel_token, cls.cancel_token_lock))
        thread.start()
        cls.topic_thread = (txid, 0, thread)

        return {
            'status': 'started',
            'progress': 0,
            'transaction_id': txid,
        }, 200
