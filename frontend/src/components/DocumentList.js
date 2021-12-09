import React, { useEffect, useState } from 'react';
import axios from 'axios';
import DocumentCard from './DocumentCard';
import UpdateDocumentForm from './UpdateDocumentForm';

const DocumentList = (props) => {
    const [documents, setDocuments] = useState([]);
    const [updatingDocUuid, setUpdatingDocUuid] = useState(undefined);

    const fetchDocs = () => {
        axios.get('http://localhost:5000/doc')
        .then(results => {
            const data = results.data;
            setDocuments(data.documents);
        })
    }
    
    useEffect(() => {
        fetchDocs();
    }, []);
    

    return (
        <div>
            {updatingDocUuid && (
                <>
                    <h3>Update Document</h3>
                    <UpdateDocumentForm docUuid={updatingDocUuid} onCancel={() => setUpdatingDocUuid(undefined)} />
                </>
            )}
            <h3>All Documents</h3>
            <button style={{ marginBottom: '8px' }} onClick={fetchDocs}>Refresh</button>
            {documents.map(({id, date}, idx) => (
                <DocumentCard key={id} docUuid={id} timestamp={date} onDelete={() => {
                    axios.delete(`http://localhost:5000/doc/${id}`);
                    documents.splice(idx, 1);
                    setDocuments([...documents]);
                }} onUpdate={() => {
                    setUpdatingDocUuid(id);
                }} />
            ))}
        </div>
    );
};

export default DocumentList;