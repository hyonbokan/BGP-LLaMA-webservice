import Header from '../components/Header';
import Navbar from '../components/Navbar';
import React from 'react';
import { Grid, Card, CardContent, Typography, IconButton } from '@mui/material';
import { Link } from 'react-router-dom';
import { useSelector } from 'react-redux';

const DatasetPage = () => {
    const allDatasets = useSelector(state => state.datasets.allDatasets);

    return (
        <div>
            <Header />
            <Navbar />
            <div>
                {allDatasets.map((section, sectionIndex) => (
                    <div
                        key={sectionIndex}
                        // padding: $ $ $ $
                        style={{ marginBottom:'20px', padding: '30px'}}
                    >
                        <Typography variant='h6' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 2, ml: 3 }} gutterBottom>
                            {section.title}
                        </Typography>
                        <Grid container spacing={2}>
                            {section.datasets.map((dataset, index) => (
                                <Grid item xs={12} sm={6} md={4} key={index}>
                                    <Link to={`/dataset/${section.id}/${section.datasets[index].id}`}>
                                        <Card>
                                            {/* <CardMedia
                                            component='img'
                                            height='140'
                                            image={dataset.imageUrl}
                                            alt={dataset.title}/> */}
                                            <CardContent>
                                                {/* <Typography variant='subtitle1' sx={{ mb: 1, fontFamily: 'monospace', fontWeight: 600 }}>{dataset.title}</Typography> */}
                                                <Typography sx={{ mb: 1, fontFamily: 'monospace', fontWeight: 600, fontSize: '18px' }}>{dataset.title}</Typography>
                                                <Typography variant='body2' sx={{
                                                    display: '-webkit-box',
                                                    overflow: 'hidden',
                                                    // textOverflow: 'ellipsis',
                                                    WebkitBoxOrient: 'vertical',
                                                    WebkitLineClamp: 4, // Number of lines to show
                                                    fontFamily: 'monospace',
                                                    mb: 1
                                                    }}>
                                                    {dataset.description}
                                                </Typography>
                                                <Typography variant='body2' sx={{ fontFamily: 'monospace' }}>Instruction count: {dataset.fileCount}</Typography>
                                                <Typography variant='body2' sx={{ fontFamily: 'monospace' }}>File size: {dataset.size}</Typography>
                                                <Typography variant='body2' sx={{ fontFamily: 'monospace' }}>Type: {dataset.fileType}</Typography>
                                            </CardContent>
                                            <IconButton aria-label='settings' size='large'>
                                            </IconButton>
                                        </Card> 
                                    </Link>
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