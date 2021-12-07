import React, { useState } from 'react';
import styled from 'styled-components';
import DocumentList from './DocumentList';
import DocumentUpload from './DocumentUpload';
import Tabs from './Tabs';

const Container = styled.div`
    height: 100%;
    position: relative;
    inset: 0% 20%;
    width: 60%;
    display: flex;
    flex-direction: row;
    overflow-x: hidden;

    @media (max-width: 800px) {
        inset: 0;
        padding: 0px 20px;
        width: 100%;
    }
`;

const ContentWrap = styled.div`
    padding: 20px;
    flex-grow: 1;
    max-width: 80%;
`;

const tabConfig = [
    { key: 'manageDocuments', label: 'Manage Documents' },
    { key: 'trends', label: 'Trends' },
    { key: 'topics', label: 'Topics' },
];

const DEFAULT_TAB = 'manageDocuments';

const Nav = (props) => {
    const [activeTab, setActiveTab] = useState(DEFAULT_TAB)

    const contents = {
        'manageDocuments': (
            <>
                <h3>Upload Document</h3>
                <DocumentUpload/>
                <DocumentList/>
            </>
        )
    };

    return (
        <Container>
            <Tabs activeTab={activeTab} onChange={setActiveTab} tabConfig={tabConfig} />
            <ContentWrap>
                {contents[activeTab]}
            </ContentWrap>
        </Container>
    )
};

export default Nav;
