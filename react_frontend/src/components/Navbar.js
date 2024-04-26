import React from 'react';
import logo from '../logo/logo.png';
import { Link } from 'react-router-dom';
import { AppBar, Button, Toolbar, Stack } from '@mui/material';

const Navbar = () => {
  const handleDownloadClick = () => {
    window.open('https://huggingface.co/hyonbokan/BGPStream13-10k-cutoff-1024-max-2048', '_blank');
  };

  const sx = {
    fontFamily: 'monospace',
    fontWeight: 700,
    letterSpacing: '.2rem',
    color: 'inherit',
    textDecoration: 'none',
  };
  const appBarStyle = {
    backgroundColor: '#1A202C', // This is the color code for TailwindCSS's bg-gray-900
  };

  return (
    <AppBar position='static' style={appBarStyle}>
      <Toolbar>
        <Link to="/">
        <img src={logo} alt='Logo' style={{ height: 50 }} />
        </Link>
        <Stack direction='row' spacing={2}>
          <Button color='inherit' sx={ sx }>
            <Link to="/dataset">
              Dataset
            </Link>
          </Button>
          <Button color='inherit' sx={ sx }>
            <Link to="/bgp_llama">
              BGP-LLaMA
            </Link>
          </Button>
          <Button 
            color="primary" 
            variant="contained"
            sx={ sx }
            onClick={handleDownloadClick}
            >
            DOWNLOAD THE MODEL
          </Button>
        </Stack>
      </Toolbar>
    </AppBar>
  )
};

export default Navbar;