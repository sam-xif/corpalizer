DROP DATABASE IF EXISTS myindex;
CREATE DATABASE myindex;
USE myindex;

CREATE TABLE document (
	document_id VARCHAR(100) PRIMARY KEY, -- this is a UUID
    timestamp DATE
    -- Add a filename or some pointer to a file, or just a TEXT field, but TEXT might be limiting though so I don't think that would work
);

CREATE TABLE paragraph (
	paragraph_id INT PRIMARY KEY AUTO_INCREMENT,
    document_id VARCHAR(100),
    position_in_fullText INT,
    CONSTRAINT paragraph_document_fk FOREIGN KEY (document_id) REFERENCES document(document_id)
--    PRIMARY KEY (document_id, position_in_fullText)
);

CREATE TABLE sentence (
	sentence_id INT PRIMARY KEY AUTO_INCREMENT,
    paragraph_id INT,
    position_in_paragraph INT,
    CONSTRAINT sentence_paragraph_fk FOREIGN KEY (paragraph_id) REFERENCES paragraph(paragraph_id)
);

CREATE TABLE term (
    term_text VARCHAR(100) PRIMARY KEY
);

CREATE TABLE topic (
	topic_id INT PRIMARY KEY AUTO_INCREMENT
);

CREATE TABLE document_term (
	score DECIMAL,
	frequency INT,
    document_id VARCHAR(100),
    term_text VARCHAR(100),
    CONSTRAINT document_term_fk1 FOREIGN KEY (document_id) REFERENCES document(document_id),
    CONSTRAINT document_term_fk2 FOREIGN KEY (term_text) REFERENCES term(term_text)
);

CREATE TABLE paragraph_term (
	score DECIMAL,
    frequency INT,
    paragraph_id INT,
    term_text VARCHAR(100),
    CONSTRAINT paragraph_term_fk1 FOREIGN KEY (paragraph_id) REFERENCES paragraph(paragraph_id),
    CONSTRAINT paragraph_term_fk2 FOREIGN KEY (term_text) REFERENCES term(term_text)
);

CREATE TABLE sentence_term (
	score DECIMAL,
    frequency INT,
    sentence_id INT,
    term_text VARCHAR(100),
    CONSTRAINT sentence_term_fk1 FOREIGN KEY (sentence_id) REFERENCES sentence(sentence_id),
    CONSTRAINT sentence_term_fk2 FOREIGN KEY (term_text) REFERENCES term(term_text)
);

DROP PROCEDURE IF EXISTS recompute_all_document_tfidf_scores;
DELIMITER //
CREATE PROCEDURE recompute_all_document_tfidf_scores()
BEGIN
	DECLARE more BOOLEAN DEFAULT TRUE;
    DECLARE document_id_var VARCHAR(100);
    DECLARE term_text_var VARCHAR(100);
    DECLARE frequency_var INT;
    
	-- calculate tfidf score of term in document
    DECLARE tf_numerator INT;
	DECLARE tf_denominator INT;
    DECLARE tf DECIMAL;
    DECLARE idf_numerator INT;
    DECLARE idf_denominator INT;
    DECLARE idf DECIMAL;
    DECLARE tfidf DECIMAL;


	DECLARE document_term_cursor CURSOR FOR
		SELECT frequency, document_id, term_text FROM document_term;
	DECLARE CONTINUE HANDLER FOR NOT FOUND SET more = FALSE;
    
    OPEN document_term_cursor;
    WHILE more = TRUE AND EXISTS(SELECT * FROM document_term) DO 
		FETCH document_term_cursor INTO frequency_var, document_id_var, term_text_var;

		SET tf_numerator = frequency_var;
		SELECT IFNULL(SUM(frequency), 0) INTO tf_denominator FROM document_term WHERE document_id = document_id_var; -- also add the new frequency
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
    
	-- calculate tfidf score of term in document
    DECLARE tf_numerator INT;
	DECLARE tf_denominator INT;
    DECLARE tf DECIMAL;
    DECLARE idf_numerator INT;
    DECLARE idf_denominator INT;
    DECLARE idf DECIMAL;
    DECLARE tfidf DECIMAL;


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
    
	-- calculate tfidf score of term in document
    DECLARE tf_numerator INT;
	DECLARE tf_denominator INT;
    DECLARE tf DECIMAL;
    DECLARE idf_numerator INT;
    DECLARE idf_denominator INT;
    DECLARE idf DECIMAL;
    DECLARE tfidf DECIMAL;

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

SELECT * FROM sentence_term;
CALL recompute_all_sentence_tfidf_scores();

SELECT * FROM paragraph_term;
SELECT * FROM document_term;