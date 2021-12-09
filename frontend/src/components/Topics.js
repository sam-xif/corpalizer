import axios from 'axios';
import React, { useEffect, useState, useRef } from 'react';

const Topics = ({ transactionId, onTransactionChange, onViewInTrends }) => {
    const [progress, setProgress] = useState('N/A');
    const [result, setResult] = useState();
    const progressPollIntervalId = useRef(null);

    const getProgress = () => {
        if (transactionId === undefined) {
            return;
        }
        
        axios.get('http://localhost:5000/topics', { params: { transaction_id: transactionId } })
        .then(result => {
            const data = result.data;
            if (data.status === 'running') {
                setProgress(`${Math.round(data.progress * 100)}%`);
            } else if (data.status === 'done') {
                setResult(data.result);
                setProgress('100%');
            }
        })
    }

    useEffect(() => {
        if (transactionId !== undefined && !result) {
            if (progressPollIntervalId.current !== null) {
                clearInterval(progressPollIntervalId.current);
            }
            progressPollIntervalId.current = setInterval(getProgress, 1000);
        }

        return () => {
            if (progressPollIntervalId.current !== null) {
                clearInterval(progressPollIntervalId.current);
            }
            progressPollIntervalId.current = null;
        }
    }, [transactionId, result]);

    return (
        <>
            <h3>Topics</h3>
            <p>
                Generating topics is an expensive operation that can take many minutes, so it has been made to happen asynchronously
                on the backend. Press the button below to trigger a new topic generation. Feel free to navigate to other pages in the app,
                but if you close the webpage then you may not be able to access the results once they are generated.
            </p>
            <button onClick={() => {
                axios.get('http://localhost:5000/topics')
                .then(result => {
                    const data = result.data;
                    onTransactionChange(data.transaction_id);
                })
                .catch(() => {
                    console.error('Error when starting new topic gen')
                })
            }}>Start</button>
            {transactionId !== undefined && (<button onClick={() => {
                axios.get('http://localhost:5000/topics', { params: { cancel: true }})
                .then(result => {
                    const data = result.data;
                    if (data.status === 'cancelled') {
                        setProgress('N/A');
                        onTransactionChange(undefined);
                    }
                })
            }}>Cancel</button>)}
            {transactionId !== undefined && <p>Transaction Id: {transactionId}</p>}
            <p>Progress: {progress}</p>
            {result && result.map((topic, i) => (
                <>
                    <h4>Topic {i + 1}</h4>
                    <button style={{ display: 'inline'}} onClick={() => {
                        onViewInTrends(topic);
                    }}>View In Trends</button>
                    <ul>
                        {topic.map(term => <li>{term}</li>)}
                    </ul>
                </>
            ))}
        </>
    );
};

export default Topics;
