import React from 'react';
import { Typography } from '@mui/material';

const Header = () => {
  const sx = { fontFamily: 'monospace', fontWeight: 700, letterSpacing: '.1rem',}
  return (
    <header className="bg-gray-900 text-white text-center p-4">
      {/* <h1 className="text-3xl roboto-condensed font-bold tracking-wider">BGP-LLaMA</h1> */}
      <Typography variant='h4' sx={ sx }>BGP-LLaMA</Typography>
    </header>
  );
};

export default Header;
