// import Header from '../components/Header';
import Navbar from '../components/PageComponents/Navbar';
import Footer from '../components/PageComponents/Footer';
import React from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Link as MuiLink } from '@mui/material';
import { Link } from 'react-router-dom';
import { useSelector } from 'react-redux';

const cropDescription = (description, wordLimit) => {
    const words = description.split(' ');
    if (words.length > wordLimit) {
        return words.slice(0, wordLimit).join(' ') + '...';
    }
    return description;
};

const DatasetPage = () => {
    const allDatasets = useSelector(state => state.datasets.allDatasets);

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Navbar />
            <Box component='main' sx={{ flexGrow: 1, width: 'auto', padding: '24px' }}>
                {allDatasets.map((section, sectionIndex) => (
                    <Box key={sectionIndex} sx={{ marginBottom: '20px', padding: '30px' }}>
                        <Typography variant='h6' sx={{ fontFamily: 'monospace', fontWeight: 600, mb: 2 }} gutterBottom>
                            {section.title}
                        </Typography>
                        <TableContainer component={Paper}>
                            <Table sx={{ minWidth: 650 }} aria-label="dataset table">
                                <TableHead>
                                    <TableRow>
                                        <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>Title</TableCell>
                                        <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>Description</TableCell>
                                        <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>Instruction Count</TableCell>
                                        <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>File Size</TableCell>
                                        <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>Type</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {section.datasets.map((dataset, index) => (
                                        <TableRow key={index}>
                                            <TableCell component="th" scope="row" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                                                <MuiLink component={Link} to={`/dataset/${section.id}/${dataset.id}`}>
                                                    {dataset.title}
                                                </MuiLink>
                                            </TableCell>
                                            <TableCell sx={{
                                                display: '-webkit-box',
                                                overflow: 'hidden',
                                                WebkitBoxOrient: 'vertical',
                                                WebkitLineClamp: 4, // Number of lines to show
                                                fontFamily: 'monospace'
                                            }}>
                                                {cropDescription(dataset.description, 20)} {/* Crop to 20 words */}
                                            </TableCell>
                                            <TableCell sx={{ fontFamily: 'monospace' }}>{dataset.fileCount}</TableCell>
                                            <TableCell sx={{ fontFamily: 'monospace' }}>{dataset.size}</TableCell>
                                            <TableCell sx={{ fontFamily: 'monospace' }}>{dataset.fileType}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </Box>
                ))}
            </Box>
            <Footer />
        </Box>
    );
}

export default DatasetPage;