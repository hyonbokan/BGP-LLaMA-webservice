import React from 'react';
import Footer from "../components/PageComponents/Footer";
import Navbar from "../components/PageComponents/Navbar";
import NotFoundPage from "../features/NotFoundPage";
import { Typography, Button, Paper, Box } from '@mui/material';
import useDatasetDetails from '../hooks/useDatasetDetails';

const DetailPage = () => {
    const { dataset, sectionId, handleDownload } = useDatasetDetails();

    if (!dataset) {
        return (
            <div>
                <Navbar />
                <NotFoundPage />
            </div>
        );
    }

    // Placeholder JSON structure
    const placeholderJSON = {
        title: "Sample Dataset",
        description: "This is a placeholder description for the dataset.",
        id: "dataset-123",
        fileType: "csv",
        fileUrl: "/datasets/sample-dataset.csv",
        promptType: "base-prompt",
    };

    // Function to render a download button
    const renderDownloadButton = (label, url, fileId, fileType) => (
        <Button
            onClick={() => handleDownload(url, fileId, fileType)}
            variant='contained'
            color='primary'
            sx={{ marginBottom: '20px', marginRight: '20px', fontFamily: 'monospace' }}
        >
            {label}
        </Button>
    );

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Navbar />
            <Box component="main" sx={{ flexGrow: 1 }}> 
                <Paper sx={{ padding: '20px', marginTop: '20px' }}>
                    <Typography variant='h4' component='h1' sx={{ fontFamily: 'monospace', fontWeight: 550 }} gutterBottom>
                        {dataset.title}
                    </Typography>

                    {/* Dataset download button */}
                    {renderDownloadButton('Download Dataset', dataset.fileUrl, dataset.id, dataset.fileType)}

                    {/* Conditional prompt download button */}
                    {sectionId.includes('manual') && renderDownloadButton('Download Base Prompt', dataset.fileUrl, dataset.id, dataset.promptType)}

                    <Typography variant='h5' component='h2' sx={{ fontFamily: 'monospace', fontWeight: 500, marginBottom: '10px' }}>
                        About Dataset
                    </Typography>
                    <Typography variant='body1' sx={{ fontFamily: 'monospace' }}>
                        {dataset.description}
                    </Typography>

                    <Typography variant='h5' component='h2' sx={{ fontFamily: 'monospace', fontWeight: 500, marginTop: '20px', marginBottom: '10px' }}>
                        JSON Structure
                    </Typography>

                    <Paper elevation={3} sx={{ padding: '15px', backgroundColor: '#e0e0e0', overflowX: 'auto' }}>
                        <pre style={{ 
                            fontFamily: 'monospace', 
                            fontSize: '14px', 
                            whiteSpace: 'pre-wrap',  
                            wordWrap: 'break-word',  
                            margin: 0               
                        }}>
                            {JSON.stringify(dataset || placeholderJSON, null, 2)}
                        </pre>
                    </Paper>
                </Paper>
            </Box>
            <Footer />
        </Box>
    );
};

export default DetailPage;