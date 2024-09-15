import React from 'react';
import Footer from "../components/PageComponents/Footer";
import Navbar from "../components/PageComponents/Navbar";
import NotFoundPage from "../features/NotFoundPage";
import { Typography, Button, Paper, Box, Grid } from '@mui/material';
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

    // Function to render a download button
    const renderDownloadButton = (label, url, fileId, fileType) => (
        <Button
            onClick={() => handleDownload(url, fileId, fileType)}
            variant='contained'
            color='primary'
            sx={{ fontFamily: 'monospace', ml: 2 }}
        >
            {label}
        </Button>
    );

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Navbar />
            <Box component="main" sx={{ flexGrow: 1 }}>
                <Grid container spacing={2} alignItems="flex-start">
                    {/* Left side: About section */}
                    <Grid item xs={12} sm={6}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, mt: 2, ml: 2}}>
                            <Typography variant='h5' component='h2' sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                                About Dataset
                            </Typography>
                        </Box>
                        <Typography variant='body1' sx={{ fontFamily: 'monospace', ml: 2}}>
                            {dataset.description}
                        </Typography>
                    </Grid>
    
                    {/* Right side: JSON Structure */}
                    <Grid item xs={12} sm={6}>
                        <Box sx={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', mb: 2, mt: 2, ml: 2}}>
                            <Typography variant='h5' component='h2' sx={{ fontFamily: 'monospace', fontWeight: 500, mr: 2}}>
                                JSON Structure
                            </Typography>
                            <Box>
                                {renderDownloadButton('Download Dataset', dataset.fileUrl, dataset.id, dataset.fileType)}
                                {sectionId.includes('manual') && renderDownloadButton('Download Base Prompt', dataset.fileUrl, dataset.id, dataset.promptType)}
                            </Box>
                        </Box>
                        <Paper
                            elevation={3}
                            sx={{
                                padding: '10px',
                                backgroundColor: '#e0e0e0',
                                overflowX: 'auto',
                                maxHeight: '650px',
                                width: '100%',
                                maxWidth: '550px',
                                ml: 2
                            }}
                        >
                            <pre style={{ 
                                fontFamily: 'monospace', 
                                fontSize: '14px', 
                                whiteSpace: 'pre-wrap',  
                                wordWrap: 'break-word',  
                                margin: 0               
                            }}>
                                {dataset ? JSON.stringify(dataset.jsonSnapshot, null, 2) : '{}'}
                            </pre>
                        </Paper>
                    </Grid>
                </Grid>
            </Box>
            <Footer />
        </Box>
    );    
};

export default DetailPage;