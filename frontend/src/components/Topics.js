import axios from 'axios';
import React, { useEffect, useState, useRef } from 'react';
import styled from 'styled-components';

const TermBox = styled.span`
    display: inline-block;
    margin: 4px;
    padding: 4px;
    border: 1px solid black;
    border-radius: 4px;
`;

const Topics = ({ isStarted, onStart, onFinish, onViewInTrends }) => {
    const [progress, setProgress] = useState('N/A');
    const [result, setResult] = useState();
    const progressPollIntervalId = useRef(null);

    const getProgress = () => {
        axios.get('http://localhost:5000/topics')
        .then(result => {
            const data = result.data;
            if (data.status === 'running') {
                setProgress(`${Math.round(data.progress * 100)}%`);
            } else if (data.status === 'done') {
                setResult(data.result);
                setProgress('100%');
                onFinish();
            }
        })
    }

    useEffect(() => {
        if (isStarted && !result) {
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
    }, [isStarted, result]);

    return (
        <>
            <h3>Topics</h3>
            <p>
                Generating topics is an expensive operation that can take many minutes, so it has been made to happen asynchronously
                on the backend. Press the button below to trigger a new topic generation. Feel free to navigate to other pages in the app.
                If you close the webpage and come back, you will have to press the start button again to access the cached result.
                If any records are created, updated, or deleted, the cached result will be invalidated and topics will have to be regenerated.
            </p>
            <button onClick={() => {
                axios.get('http://localhost:5000/topics')
                .then(result => {
                    const data = result.data;
                    onStart();
                })
                .catch(() => {
                    console.error('Error when starting new topic gen')
                })
            }}>Start</button>
            {isStarted && (<button onClick={() => {
                axios.get('http://localhost:5000/topics', { params: { cancel: true }})
                .then(result => {
                    const data = result.data;
                    if (data.status === 'cancelled') {
                        setProgress('N/A');
                        onFinish();
                    }
                })
            }}>Cancel</button>)}
            <p>Progress: {progress}</p>
            {result && result.map((topic, i) => (
                <>
                    <h4>Topic {i + 1}</h4>
                    <button style={{ display: 'inline'}} onClick={() => {
                        onViewInTrends(topic);
                    }}>View In Trends</button>
                    <div>
                        {topic.map(term => <TermBox>{term}</TermBox>)}
                    </div>
                </>
            ))}
        </>
    );
};

export default Topics;
