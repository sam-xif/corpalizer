DROP DATABASE IF EXISTS corpalizer;
CREATE DATABASE corpalizer;
USE corpalizer;

CREATE TABLE document (
	document_id VARCHAR(100) PRIMARY KEY,
    timestamp DATE
);

CREATE TABLE paragraph (
	paragraph_id INT PRIMARY KEY AUTO_INCREMENT,
    document_id VARCHAR(100),
    position_in_fullText INT,
    CONSTRAINT paragraph_document_fk FOREIGN KEY (document_id) REFERENCES document(document_id) ON UPDATE RESTRICT ON DELETE CASCADE
);

CREATE TABLE sentence (
	sentence_id INT PRIMARY KEY AUTO_INCREMENT,
    paragraph_id INT,
    position_in_paragraph INT,
    CONSTRAINT sentence_paragraph_fk FOREIGN KEY (paragraph_id) REFERENCES paragraph(paragraph_id) ON UPDATE RESTRICT ON DELETE CASCADE
);

CREATE TABLE term (
    term_text VARCHAR(100) PRIMARY KEY
);

CREATE TABLE document_term (
	score DOUBLE,
	frequency INT,
    document_id VARCHAR(100),
    term_text VARCHAR(100),
    CONSTRAINT document_term_fk1 FOREIGN KEY (document_id) REFERENCES document(document_id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT document_term_fk2 FOREIGN KEY (term_text) REFERENCES term(term_text) ON UPDATE RESTRICT ON DELETE CASCADE
);

CREATE TABLE paragraph_term (
	score DOUBLE,
    frequency INT,
    paragraph_id INT,
    term_text VARCHAR(100),
    CONSTRAINT paragraph_term_fk1 FOREIGN KEY (paragraph_id) REFERENCES paragraph(paragraph_id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT paragraph_term_fk2 FOREIGN KEY (term_text) REFERENCES term(term_text) ON UPDATE RESTRICT ON DELETE CASCADE
);

CREATE TABLE sentence_term (
	score DOUBLE,
    frequency INT,
    sentence_id INT,
    term_text VARCHAR(100),
    CONSTRAINT sentence_term_fk1 FOREIGN KEY (sentence_id) REFERENCES sentence(sentence_id) ON UPDATE RESTRICT ON DELETE CASCADE,
    CONSTRAINT sentence_term_fk2 FOREIGN KEY (term_text) REFERENCES term(term_text) ON UPDATE RESTRICT ON DELETE CASCADE
);

DROP PROCEDURE IF EXISTS cleanup_terms;
DELIMITER //
CREATE PROCEDURE cleanup_terms()
BEGIN
    DROP TABLE IF EXISTS terms_to_delete;
    CREATE TEMPORARY TABLE terms_to_delete (t VARCHAR(100));
    INSERT INTO terms_to_delete SELECT term.term_text FROM term LEFT JOIN document_term USING (term_text) WHERE document_id IS NULL;
    DELETE FROM term WHERE term_text IN (SELECT t FROM terms_to_delete);
END //
DELIMITER ;

DROP PROCEDURE IF EXISTS recompute_all_document_tfidf_scores;
DELIMITER //
CREATE PROCEDURE recompute_all_document_tfidf_scores()
BEGIN
	DECLARE more BOOLEAN DEFAULT TRUE;
    DECLARE document_id_var VARCHAR(100);
    DECLARE term_text_var VARCHAR(100);
    DECLARE frequency_var INT;
    
    DECLARE tf_numerator DOUBLE;
	DECLARE tf_denominator DOUBLE;
    DECLARE tf DOUBLE;
    DECLARE idf_numerator DOUBLE;
    DECLARE idf_denominator DOUBLE;
    DECLARE idf DOUBLE;
    DECLARE tfidf DOUBLE;


	DECLARE document_term_cursor CURSOR FOR
		SELECT frequency, document_id, term_text FROM document_term;
	DECLARE CONTINUE HANDLER FOR NOT FOUND SET more = FALSE;
    
    OPEN document_term_cursor;
    WHILE more = TRUE AND EXISTS(SELECT * FROM document_term) DO 
		FETCH document_term_cursor INTO frequency_var, document_id_var, term_text_var;

		SET tf_numerator = frequency_var;
		SELECT IFNULL(SUM(frequency), 0) INTO tf_denominator FROM document_term WHERE document_id = document_id_var;
		SET tf = tf_numerator / tf_denominator;
			 
		SELECT COUNT(*) INTO idf_numerator FROM document;
		SELECT COUNT(DISTINCT document_id) INTO idf_denominator FROM document_term WHERE term_text = term_text_var AND frequency > 0;
		SET idf = LOG(idf_numerator / idf_denominator);
		SET tfidf = tf * idf;
			
		UPDATE document_term SET score = tfidf WHERE document_id = document_id_var AND term_text = term_text_var;
	END WHILE;
END //
DELIMITER ;


DROP PROCEDURE IF EXISTS recompute_all_paragraph_tfidf_scores;
DELIMITER //
CREATE PROCEDURE recompute_all_paragraph_tfidf_scores()
BEGIN
	DECLARE more BOOLEAN DEFAULT TRUE;
    DECLARE paragraph_id_var VARCHAR(100);
    DECLARE term_text_var VARCHAR(100);
    DECLARE frequency_var INT;
    
    DECLARE tf_numerator DOUBLE;
	DECLARE tf_denominator DOUBLE;
    DECLARE tf DOUBLE;
    DECLARE idf_numerator DOUBLE;
    DECLARE idf_denominator DOUBLE;
    DECLARE idf DOUBLE;
    DECLARE tfidf DOUBLE;


	DECLARE document_term_cursor CURSOR FOR
		SELECT frequency, paragraph_id, term_text FROM paragraph_term;
	DECLARE CONTINUE HANDLER FOR NOT FOUND SET more = FALSE;
    
    OPEN document_term_cursor;
    WHILE more = TRUE AND EXISTS(SELECT * FROM paragraph_term) DO 
		FETCH document_term_cursor INTO frequency_var, paragraph_id_var, term_text_var;

		SET tf_numerator = frequency_var;
		SELECT IFNULL(SUM(frequency), 0) INTO tf_denominator FROM paragraph_term WHERE paragraph_id = paragraph_id_var;
		SET tf = tf_numerator / tf_denominator;
			 
		SELECT COUNT(*) INTO idf_numerator FROM paragraph;
		SELECT COUNT(DISTINCT paragraph_id) INTO idf_denominator FROM paragraph_term WHERE term_text = term_text_var AND frequency > 0;
		SET idf = LOG(idf_numerator / idf_denominator);
		SET tfidf = tf * idf;
			
		UPDATE paragraph_term SET score = tfidf WHERE paragraph_id = paragraph_id_var AND term_text = term_text_var;
	END WHILE;
END //
DELIMITER ;


DROP PROCEDURE IF EXISTS recompute_all_sentence_tfidf_scores;
DELIMITER //
CREATE PROCEDURE recompute_all_sentence_tfidf_scores()
BEGIN
	DECLARE more BOOLEAN DEFAULT TRUE;
    DECLARE sentence_id_var VARCHAR(100);
    DECLARE term_text_var VARCHAR(100);
    DECLARE frequency_var INT;
    
    DECLARE tf_numerator DOUBLE;
	DECLARE tf_denominator DOUBLE;
    DECLARE tf DOUBLE;
    DECLARE idf_numerator DOUBLE;
    DECLARE idf_denominator DOUBLE;
    DECLARE idf DOUBLE;
    DECLARE tfidf DOUBLE;

	DECLARE document_term_cursor CURSOR FOR
		SELECT frequency, sentence_id, term_text FROM sentence_term;
	DECLARE CONTINUE HANDLER FOR NOT FOUND SET more = FALSE;
    
    OPEN document_term_cursor;
    WHILE more = TRUE AND EXISTS(SELECT * FROM sentence_term) DO 
		FETCH document_term_cursor INTO frequency_var, sentence_id_var, term_text_var;

		SET tf_numerator = frequency_var;
		SELECT IFNULL(SUM(frequency), 0) INTO tf_denominator FROM sentence_term WHERE sentence_id = sentence_id_var;
		SET tf = tf_numerator / tf_denominator;
			 
		SELECT COUNT(*) INTO idf_numerator FROM sentence;
		SELECT COUNT(DISTINCT sentence_id) INTO idf_denominator FROM sentence_term WHERE term_text = term_text_var AND frequency > 0;
		SET idf = LOG(idf_numerator / idf_denominator);
		SET tfidf = tf * idf;
			
		UPDATE sentence_term SET score = tfidf WHERE sentence_id = sentence_id_var AND term_text = term_text_var;
	END WHILE;
END //
DELIMITER ;


DROP FUNCTION IF EXISTS compute_similarity_score;
DELIMITER //
CREATE FUNCTION compute_similarity_score(t1 VARCHAR(100), t2 VARCHAR(100))
RETURNS DOUBLE
DETERMINISTIC
READS SQL DATA
BEGIN
	DECLARE ret DOUBLE;
    
	SELECT SUM(ABS(dt1.score - dt2.score)) INTO ret FROM document 
    JOIN document_term as dt1 
    ON document.document_id = dt1.document_id AND (dt1.term_text = t2 OR dt1.term_text = t1)
    LEFT JOIN document_term as dt2
    ON document.document_id = dt2.document_id AND (dt2.term_text = t2 OR dt2.term_text = t1);
    
    RETURN(ret);
END // 
DELIMITER ;


DROP PROCEDURE IF EXISTS compute_all_similarity_scores;
DELIMITER //
CREATE PROCEDURE compute_all_similarity_scores()
BEGIN
	SELECT DISTINCT t1.term_text, t2.term_text, compute_similarity_score(t1.term_text, t2.term_text) FROM term as t1 CROSS JOIN term as t2 WHERE t1.term_text < t2.term_text;
END //
DELIMITER ;
