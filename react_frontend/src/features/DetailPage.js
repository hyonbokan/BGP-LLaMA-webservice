import React from "react";
import Header from "../components/Header";
import Navbar from "../components/Navbar";
import { useParams } from 'react-router-dom';
import { useSelector } from "react-redux";

const DetailPage = () => {
    const { sectionId, datasetId } = useParams();
    const dataset = useSelector(state => {
        const section = state.datasets.allDatasets.find(sec => sec.id === sectionId);
        console.log(`section id: ${sectionId}\n dataset id: ${datasetId}`)
        return section ? section.datasets.find(ds => ds.id === datasetId) : null;
    });
    
    if (!dataset) {
        return (
            <div>
                <Header />
                <Navbar />
                <p>Dataset not found.</p>
            </div>
        );
    }

    return (
        <div>
            <Header />
            <Navbar />
            <h1>{dataset.title}</h1>
            <h1>About dataset</h1>
            <p>Dataset description</p>
        </div>
    )
};

export default DetailPage;