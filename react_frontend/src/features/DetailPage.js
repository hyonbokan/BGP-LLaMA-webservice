import React from "react";
// import Header from "../components/Header";
import Navbar from "../components/Navbar";
import NotFoundPage from "../features/NotFoundPage";
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
                {/* <Header /> */}
                <Navbar />
                <NotFoundPage />
            </div>
        );
    }
    console.log(`section id: ${sectionId}\n dataset id: ${datasetId}`)

    const handleDownload = (fileUrl, fileName, fileExtension = '') => {
       const relativeFileUrl = fileUrl.replace(/^\/+/, '');
       const url = `http://127.0.0.1:8000/api/download/?file=${encodeURIComponent(relativeFileUrl)}`;
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
        const dowloadUrl = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement('a');
        link.href = dowloadUrl;
        link.setAttribute('download', `${fileName}${fileExtension ? '.' + fileExtension : ''}`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        
        console.log(`\nDownload URL: ${dowloadUrl}`);
        console.log(`\nFile Path: ${fileUrl}`);
       })
       .catch(error => console.error('Error downloading the file: ', error));
    };

    return (
        <div>
            {/* <Header /> */}
            <Navbar />
            <Paper style={{ padding: '20px', marginTop: '20px' }}>
                <Typography variant='h4' component='h1' sx={{ fontFamily: 'monospace' }} gutterBottom>
                    {dataset.title}
                </Typography>
                <Button 
                onClick={() => handleDownload(dataset.fileUrl, dataset.id, dataset.fileType)}
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
                    <Button
                    onClick={() => handleDownload(dataset.fileUrl, dataset.id, dataset.promptType)}
                    variant='contained' 
                    color='primary' 
                    style={{ marginBottom: '20px', fontFamily: 'monospace' }}>
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