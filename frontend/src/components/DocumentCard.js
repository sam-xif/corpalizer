import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';

const Card = styled.div`
    border-radius: 10px;
    border: 1px solid black;
    padding: 10px;
    margin-bottom: 5px;
    max-width: 100%;
`;

const Fields = styled.div`
    display: flex;
    flex-direction: column;
`;

const Label = styled.span`
    font-weight: bold;
`;

const PreviewBox = styled.p`
    word-break: break-all;
`;

const DeleteText = styled.span`
    margin-left: 8px;
    color:red;
`;

const NONE = null;
const DELETING = 'deleting';
const DELETION_FAILED = 'fail';


const DocumentCard = ({ docUuid, timestamp, onDelete, onUpdate }) => {
    const [preview, setPreview] = useState(null);
    const [deletionStatus, setDeletionStatus] = useState(NONE);

    useEffect(() => {
        axios.get(`http://localhost:5000/doc/${docUuid}`)
        .then(result => {
            const data = result.data;
            setPreview(data.content)
        })
    }, [])

    useEffect(() => {
        if (deletionStatus == 'deleting') {
            axios.delete(`http://localhost:5000/doc/${docUuid}`)
            .then(result => {
                onDelete();
            })
            .catch(() => {
                setDeletionStatus(DELETION_FAILED);
            })
        }
    }, [deletionStatus])

    const handleDelete = () => {
        setDeletionStatus(DELETING);
    }

    return (
        <Card>
            <Fields>
                <div>
                    <Label>UUID:</Label>{' '}{docUuid}
                </div>
                <div>
                    <Label>Timestamp:</Label>{' '}{timestamp}
                </div>
                {preview && (
                    <div>
                        <Label>Preview:</Label>{' '}
                        <PreviewBox>"{preview.substring(0, 300)}{preview.length > 300 ? '...' : ''}"</PreviewBox>
                    </div>
                )}
                <div>
                    <a href="javascript:void(0);" onClick={handleDelete}>Delete</a>
                    {deletionStatus !== NONE 
                    && (<DeleteText>
                        {deletionStatus === DELETING ? 'Deletion in progress...': 'Deletion failed, likely because of deadlock. Try again later'}
                    </DeleteText>)}
                    <br/>
                    <a href="javascript:void(0);" onClick={onUpdate}>Update</a>
                </div>
            </Fields>
        </Card>
    )
};

export default DocumentCard;
