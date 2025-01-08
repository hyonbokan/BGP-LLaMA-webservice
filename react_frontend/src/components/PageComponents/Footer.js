import React from "react";
import logo from '../../logo/logo.png';
import { Link as RouterLink } from 'react-router-dom';
import { Box, Grid, Typography, IconButton, Link as MUILink } from '@mui/material';
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
    
    const iconButtonStyle = { color: 'white', padding: '12px', };

    return (
        <Box component='footer' sx={{ backgroundColor: '#1A202C', padding: 5, marginTop: 2,}}>
            <Grid container sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Grid item xs={12} sm={4}>
                    <img src={logo} alt="logo" style={{ height: 50 }} />
                    <Box sx={{backgroundColor: 'inherit',}}>
                        <IconButton component="a" href="https://github.com/hyonbokan/" target="_blank" aria-label="GitHub" style={ iconButtonStyle }>
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

                <Grid item xs={false} sm={2} />

                <Grid item xs={12} sm={2}>
                    <Typography variant="subtitle1" sx={ titleFontStyle } gutterBottom>Features</Typography>
                    <MUILink component={RouterLink} to="/dataset" underline="hover" sx={ textFontStyle }>Dataset</MUILink><br />
                    <MUILink component={RouterLink} to="/bgp_chat" underline="hover" sx={ textFontStyle }>BGP-LLaMA</MUILink><br />
                    <MUILink href="https://github.com/hyonbokan/LLM-research/blob/main/finetune_main/finetuning_base/llama_bgpstream_finetune.ipynb" underline="hover" sx={ textFontStyle }>Fine-tuning</MUILink>
                </Grid>

                <Grid item xs={12} sm={2}>
                    <Typography variant="subtitle1" sx={ titleFontStyle } gutterBottom>Learn</Typography>
                    <MUILink href="https://ieeexplore.ieee.org/document/10583947/authors#authors" underline="hover" sx={ textFontStyle }>Paper</MUILink><br />
                    <MUILink href="https://github.com/hyonbokan/LLM-research" underline="hover" sx={ textFontStyle }>Documentation</MUILink>
                </Grid>

                <Grid item xs={12} sm={2}>
                    <Typography variant="subtitle1" sx={ titleFontStyle } gutterBottom>Contacts</Typography>
                    <Typography variant="subtitle3" href="#" underline="hover" sx={ textFontStyle }>Address: 99 Daehak-ro, Yuseong-gu, Daejeon, Republic of Korea</Typography><br />
                    <Typography variant="subtitle3" href="#" underline="hover" sx={ textFontStyle }>Email: hyonbokan@cs-cnu.org</Typography>
                </Grid>

            </Grid>
        </Box>
    );
};

export default Footer;