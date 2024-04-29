import Header from '../components/Header';
import Navbar from '../components/Navbar';
import React from 'react';
import { Grid, Card, CardContent, CardMedia, Typography, IconButton } from '@mui/material';

const DatasetPage = () => {

    const sections = [
        {
            title: 'Self-Instruct Generated Dataset',
            datasets: [
                {
                    title:'BGP Knowledge',
                    imageUrl: '',
                    fileCount: 1111,
                    size: '10 MB',
                    fileType: 'json'

                },
                {
                    title:'PyBGPStream Base',
                    imageUrl: '',
                    fileCount: 1111,
                    size: '10 MB',
                    fileType: 'json'

                },
                {
                    title:'PyBGPStream Real-time Stream',
                    imageUrl: '',
                    fileCount: 1111,
                    size: '10 MB',
                    fileType: 'json'

                },
            ],
        },
        {
            title: 'Manual Seed Tasks',
            datasets: [
                {
                    title:'BGP Knowledge I',
                    imageUrl: '',
                    fileCount: 1111,
                    size: '10 MB',
                    fileType: 'json'

                },
                {
                    title:'BGP Knowledge II',
                    imageUrl: '',
                    fileCount: 1111,
                    size: '10 MB',
                    fileType: 'json'

                },
                {
                    title:'PyBGPStream Base',
                    imageUrl: '',
                    fileCount: 1111,
                    size: '10 MB',
                    fileType: 'json'

                },
                {
                    title:'PyBGPStream Real Cases',
                    imageUrl: '',
                    fileCount: 1111,
                    size: '10 MB',
                    fileType: 'json'

                },
                {
                    title:'PyBGPStream Real-time Stream',
                    imageUrl: '',
                    fileCount: 1111,
                    size: '10 MB',
                    fileType: 'json'

                },             
            ]
        }
    ];

    return (
        <div>
            <Header />
            <Navbar />
            <div>
                {sections.map((section, sectionIndex) => (
                    <div
                        key={sectionIndex}
                        // sx={{ mb: 4}}
                        style={{ marginTop:'50px', marginBottom:'50px'}}
                    >
                        <Typography variant='h6' gutterBottom>
                            {section.title}
                        </Typography>
                        <Grid container spacing={2}>
                            {section.datasets.map((dataset, index) => (
                                <Grid item xs={12} sm={6} md={3} key={index}>
                                    <Card>
                                        {/* <CardMedia
                                        component='img'
                                        height='140'
                                        image={dataset.imageUrl}
                                        alt={dataset.title}/> */}
                                        <CardContent>
                                            <Typography variant='subtitle1'>{dataset.title}</Typography>
                                            <Typography variant='body2'>Instruction count: {dataset.fileCount}</Typography>
                                            <Typography variant='body2'>File size: {dataset.size}</Typography>
                                            <Typography variant='body2'>Type: {dataset.fileType}</Typography>
                                        </CardContent>
                                        <IconButton aria-label='settings' size='large'>

                                        </IconButton>

                                    </Card> 
                                </Grid>
                            ))}
                        </Grid>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default DatasetPage;