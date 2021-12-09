import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { buildUrl } from '../utils';

const UpdateDocumentForm = ({ docUuid, onCancel }) => {
    const [text, setText] = useState(undefined);
    const textAreaRef = useRef();
    useEffect(() => {
        axios.get(buildUrl(`doc/${docUuid}`))
        .then(results => {
            const data = results.data;
            setText(data.content);
            textAreaRef.current.innerHTML = data.content;
        })
    }, [docUuid])

    return (
        <>
            <textarea rows="20" cols="60" ref={textAreaRef}></textarea>
            <br/>
            <button onClick={() => {
                console.log(textAreaRef.current.value)
                axios.put(buildUrl(`doc/${docUuid}`), { content: textAreaRef.current.value });
            }}>Submit</button>
            <button onClick={onCancel}>Cancel</button>
        </>
    )
}

export default UpdateDocumentForm;