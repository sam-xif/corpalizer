import axios from 'axios';
import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';

const reader = new FileReader();
const SUCCESS = 'Upload succeeded';
const FAIL = 'Upload failed';

const StatusText = styled.span`
    padding-left: 8px;
    color: ${({ status }) => status === SUCCESS ? 'green' : status === FAIL ? 'red' : 'gray'};
`;

const DocumentUpload = (props) => {
    const [files, setFiles] = useState();
    const fileInputRef = useRef();
    const [uploadProgress, setUploadProgress] = useState();
    const [uploadStatus, setUploadStatus] = useState();

    useEffect(() => {
        if (files) {
            if (uploadProgress === undefined) {
                setUploadProgress(0);
            } else {
                reader.onload = (e) => {
                    const text = e.target.result.toString();

                    axios.post('http://localhost:5000/doc', { content: text })
                    .then(result => {
                        setUploadProgress(uploadProgress + 1);
                    })
                    .catch(() => {
                        setUploadStatus(FAIL);
                        setFiles(undefined);
                        setUploadProgress(undefined);
                    });
                }

                if (uploadProgress === files.length) {
                    setUploadStatus(SUCCESS);
                    setFiles(undefined);
                    setUploadProgress(undefined);
                    return;
                }

                const file = files[uploadProgress];
                reader.readAsText(file);
            }
        }
    }, [files, uploadProgress])

    useEffect(() => {
        if (uploadStatus && (uploadStatus === SUCCESS || uploadStatus === FAIL)) {
            setTimeout(() => {
                setUploadStatus(undefined);
            }, 5000);
        }
    }, [uploadStatus])

    return (
        <div>
            <input type="file" ref={fileInputRef} style={{ display: 'none' }} onChange={(e) => {
                setFiles(Array.from(e.target.files));
            }} multiple></input>
            <input type="submit" value="Upload" onClick={() => {
                fileInputRef.current.value = '';
                fileInputRef.current.click();
            }}></input>
            {uploadProgress !== undefined && <StatusText>{`${uploadProgress} / ${files.length}`}</StatusText>}
            <StatusText status={uploadStatus}>{uploadStatus}</StatusText>
        </div>
    )
};

export default DocumentUpload;
