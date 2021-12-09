import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import moment from 'moment';
import _ from 'lodash';

import {
    CartesianGrid,
    Legend,
    ResponsiveContainer,
    Line,
    LineChart,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';

const GRANULARITY = {
    DOCUMENT: 'document',
    PARAGRAPH: 'paragraph',
    SENTENCE: 'sentence',
};

const BIN = {
    DAY: 'day',
    MONTH: 'month',
    YEAR: 'year',
}

const RadioGroup = ({ name, buttonConfig, value, onChange }) => {
    const buttonsRef = useRef([]);

    useEffect(() => {
        buttonsRef.current = buttonsRef.current.slice(0, buttonConfig.length);
    }, [buttonConfig]);

    return (
        <>
            {buttonConfig.map(({ key, label }) => (
                <div>
                    <input type="radio" name={name} value={key} id={key} checked={key === value} onChange={(e) => {
                        onChange(e.target.value);
                    }} />
                    <label for={key}>{label}</label>
                </div>
            ))}
        </>
    );
};

const Trends = ({ query, onQueryChange }) => {
    const [granularity, setGranularity] = useState(GRANULARITY.DOCUMENT);
    const [bin, setBin] = useState(BIN.DAY);
    const [trendsData, setTrendsData] = useState({});
    
    const configFromObject = (obj) => {
        return Object.keys(obj).reduce((soFar, next) => {
            soFar.push({ key: obj[next], label: obj[next].substring(0, 1).toUpperCase() + obj[next].substring(1) });
            return soFar;
        }, [])
    }

    useEffect(() => {
        const terms = query.split(',');
        Promise.all(terms.map(term => axios.get(`http://localhost:5000/trends/${granularity}/${term}`, { params: {
            bin_type: bin
        }}))).then(results => {
            const fullData = {};
            results.forEach((result, i) => {
                const data = result.data.data;
                const dataArray = Object.keys(data).reduce((soFar, next) => {
                    soFar.push({time: moment(next).valueOf(), [terms[i]]: data[next]});
                    return soFar;
                }, [])
                fullData[terms[i]] = dataArray.sort((a, b) => a.time - b.time);
            });
            setTrendsData(fullData);
        })
    }, [query, granularity, bin]);

    const colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"];

    const formats = {
        [BIN.DAY]: 'YYYY-MM-DD',
        [BIN.MONTH]: 'YYYY-MM',
        [BIN.YEAR]: 'YYYY',
    }
    const tickFormatter = (unixTime) => moment(unixTime).format(formats[bin])

    return (
        <>
            <p>Granularity:</p>
            <RadioGroup name="granularity" buttonConfig={configFromObject(GRANULARITY)} value={granularity} onChange={setGranularity}/>
            <p>Binning:</p>
            <RadioGroup name="bin" buttonConfig={configFromObject(BIN)} value={bin} onChange={setBin}/>
            <p>Terms:</p>
            <p>Write terms comma separated with no space like this: "cost,event"</p>
            <input type="text" value={query} onChange={(e) => {
                console.log(e.target.value);
                onQueryChange(e.target.value);
            }} />
            <h3>Chart</h3>
            <ResponsiveContainer width="100%" height={500}>
                <LineChart>
                    <CartesianGrid/>
                    {query.split(',').map((term, i) => <Line data={trendsData[term]} key={term} dataKey={term} stroke={colors[i % colors.length]} />)}
                    <XAxis 
                        dataKey="time" 
                        domain={['auto', 'auto']} 
                        name="Time" 
                        type="number" 
                        tickFormatter={tickFormatter}
                        // label={{ value: "Time", dy: 10 }} 
                    />
                    <YAxis name="Freq" label={{ value: "Freq", dx: -10 }} allowDecimals={false}/>
                    <Legend/>
                </LineChart>
            </ResponsiveContainer>
        </>
    )
}

export default Trends;
