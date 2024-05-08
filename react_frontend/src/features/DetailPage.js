import React from "react";
import Header from "../components/Header";
import Navbar from "../components/Navbar";
import { useParams } from 'react-router-dom';
import { useSelector } from "react-redux";
import { Typography, Button, Paper } from '@mui/material';


const DetailPage = () => {
    const { sectionId, datasetId } = useParams();
    const dataset = useSelector(state => {
        const section = state.datasets.allDatasets.find(sec => sec.id === sectionId);
        return section ? section.datasets.find(ds => ds.id === datasetId) : null;
    });
    if (!dataset) {
        return (
            <div>
                <Header />
                <Navbar />
                <Typography variant='h6' color='error'>Dataset not found.</Typography>
            </div>
        );
    }
    console.log(`section id: ${sectionId}\n dataset id: ${datasetId}`)

    const handleDownload = (fileUrl) => {
        // Make sure that the url is correct, especially the api
       const url = 'http://127.0.0.1:8000/api/download/' + encodeURIComponent(fileUrl);
       console.log(`Backend URL: ${url}`); 

       fetch(url, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
        }
       })
       .then(response => response.blob())
       .then(blob => {
        // Create a link element to download the file and remove it
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${datasetId}.json`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        
        console.log(`\nDownload URL: ${url}`);
        console.log(`\nFile Path: ${fileUrl}`);
       })
       .catch(error => console.error('Error downloading the file: ', error));
    };

    return (
        <div>
            <Header />
            <Navbar />
            <Paper style={{ padding: '20px', marginTop: '20px' }}>
                <Typography variant='h4' component='h1' sx={{ fontFamily: 'monospace' }} gutterBottom>
                    {dataset.title}
                </Typography>
                <Button 
                onClick={() => handleDownload(dataset.fileUrl)}
                variant='contained' 
                color='primary' 
                style={{ 
                    marginBottom: '20px', 
                    marginRight: '20px', 
                    fontFamily: 'monospace' }}
                >
                    Download Dataset
                </Button>
                {sectionId.includes('manual') && (
                    <Button variant='contained' color='primary' style={{ marginBottom: '20px', fontFamily: 'monospace' }}>
                        Download Base Prompt
                    </Button>
                )}
                <Typography variant='h5' component='h2' sx={{ fontFamily: 'monospace', fontWeight: 600, marginBottom: '10px' }}>
                    About Dataset
                </Typography>
                <Typography variant='body1' sx={{ fontFamily: 'monospace' }}>
                    {dataset.description}
                </Typography>
            </Paper>
        </div>
    )
};

export default DetailPage;