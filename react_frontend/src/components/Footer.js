import React from "react";
import { Box, Grid, Typography, Link, IconButton, } from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import FacebookIcon from '@mui/icons-material/Facebook';
import InstagramIcon from '@mui/icons-material/Instagram';
import LanguageIcon from '@mui/icons-material/Language';
import LinkedInIcon from '@mui/icons-material/LinkedIn';

const Footer = () => {

    const titleFontStyle = {
        fontFamily: 'monospace',
        color: 'white',
        fontWeight: 550,
      }
    
    const textFontStyle = {
        fontFamily: 'monospace',
        color: 'white',
      }
    
    const iconButtonStyle = { color: 'white' };



    return (
        <Box component='footer' sx={{ backgroundColor: '#1A202C', padding: 5, marginTop: 2,}}>
            <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                    <img src="" alt="logo" style={{ height: 30 }} />
                    <Box>
                        <IconButton component="a" href="https://github.com/hyonbokan/LLM-research" target="_blank" aria-label="GitHub" style={ iconButtonStyle }>
                            <GitHubIcon />
                        </IconButton>
                        <IconButton component="a" href="https://www.facebook.com" target="_blank" aria-label="Facebook" style={ iconButtonStyle }>
                            <FacebookIcon />
                        </IconButton>
                        <IconButton component="a" href="https://www.instagram.com" target="_blank" aria-label="Instagram" style={ iconButtonStyle }>
                            <InstagramIcon />
                        </IconButton>
                        <IconButton component="a" href="https://www.linkedin.com/in/khen-bo-kan-2909a716b/" target="_blank" aria-label="LinkedIn" style={ iconButtonStyle }>
                            <LinkedInIcon />
                        </IconButton>
                        <IconButton component="a" href="https://dnlab.cs-cnu.org/" target="_blank" aria-label="Lab Website" style={ iconButtonStyle }>
                            <LanguageIcon />
                        </IconButton>
                    </Box>
                </Grid>

                <Grid item xs={12} sm={2}>
                    <Typography variant="subtitle1" sx={ titleFontStyle } gutterBottom>Main</Typography>
                    <Link href="#" underline="hover" sx={ textFontStyle }>Dataset</Link><br />
                    <Link href="#" underline="hover" sx={ textFontStyle }>Fine-tuning</Link><br />
                    <Link href="#" underline="hover" sx={ textFontStyle }>BGP-LLaMA</Link>
                </Grid>

                <Grid item xs={12} sm={2}>
                    <Typography variant="subtitle1" sx={ titleFontStyle } gutterBottom>Learn</Typography>
                    <Link href="#" underline="hover" sx={ textFontStyle }>Paper</Link><br />
                    <Link href="#" underline="hover" sx={ textFontStyle }>Tutotial</Link>
                </Grid>

            </Grid>
        </Box>
    );
};

export default Footer;