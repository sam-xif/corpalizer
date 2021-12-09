import React from 'react';
import styled from 'styled-components';

const Container = styled.div`
    max-width: 20%;
    border-right: 1px solid gray;
    display: flex;
    flex-direction: column;
    justify-content: start;
    padding: 20px 0px;
    position: sticky;
    top: 0;
`;

const Tab = styled.p`
    color: ${props => props.selected ? 'black' : 'gray'};
    cursor: pointer;
    transition: all 0.2s ease;
`;

const Tabs = ({ activeTab, onChange, tabConfig }) => {
    // tab config is array of { key: string, label: string }
    return (
        <Container>
            {tabConfig.map(tab => (
                <Tab key={tab.key} selected={tab.key === activeTab} onClick={() => onChange(tab.key)}>{tab.label}</Tab>
            ))}
        </Container>
    )
};

export default Tabs;
