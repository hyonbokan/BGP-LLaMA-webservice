import React, { useState } from 'react';
import logo from '../../logo/logo.png';
import { Link as RouterLink } from 'react-router-dom';
import {
  AppBar,
  Button,
  Toolbar,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
  Box,
  Stack,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';

const Navbar = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md')); // Adjust breakpoint as needed

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleDownloadClick = () => {
    window.open(
      'https://huggingface.co/hyonbokan/BGPStream13-10k-cutoff-1024-max-2048',
      '_blank'
    );
  };

  const navLinks = [
    { title: 'Dataset', path: '/dataset' },
    { title: 'BGP-LLaMA', path: '/bgp_chat' },
    { title: 'BGP-GPT', path: '/bgp_chat_gpt' },
    { title: 'Fine-tuning', path: '/finetuning' },
  ];

  const drawer = (
    <Box
      onClick={handleDrawerToggle}
      sx={{ width: 250 }}
      role="presentation"
    >
      <List>
        {navLinks.map((item) => (
          <ListItem
            button
            key={item.title}
            component={RouterLink}
            to={item.path}
          >
            <ListItemText primary={item.title} />
          </ListItem>
        ))}
        <ListItem button onClick={handleDownloadClick}>
          <ListItemText primary="DOWNLOAD MODEL" />
        </ListItem>
      </List>
    </Box>
  );

  const buttonSX = {
    fontFamily: 'monospace',
    fontWeight: 700,
    letterSpacing: '.2rem',
    color: 'inherit',
    textDecoration: 'none',
  };

  const appBarStyle = {
    backgroundColor: '#1A202C',
  };

  return (
    <>
      <AppBar position="static" style={appBarStyle}>
        <Toolbar>
          {/* Hamburger Menu Icon for Mobile */}
          {isMobile && (
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              onClick={handleDrawerToggle}
              sx={{ mr: 1 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          {/* Logo */}
          <Box
            component={RouterLink}
            to="/"
            sx={{
              display: 'flex',
              alignItems: 'center',
              textDecoration: 'none',
            }}
          >
            <img src={logo} alt="Logo" style={{ height: 50 }} />
          </Box>

          {/* Navigation Links for Desktop */}
          {!isMobile && (
            <Stack direction="row" spacing={3} sx={{ ml: 3 }}>
              {navLinks.map((item) => (
                <Button
                  key={item.title}
                  component={RouterLink}
                  to={item.path}
                  color="inherit"
                  sx={buttonSX}
                >
                  {item.title}
                </Button>
              ))}
            </Stack>
          )}

          {/* Spacer to push "DOWNLOAD MODEL" button to the right */}
          <Box sx={{ flexGrow: 1 }} />

          {/* "DOWNLOAD MODEL" Button */}
          <Button
            color="primary"
            variant="contained"
            sx={buttonSX}
            onClick={handleDownloadClick}
          >
            DOWNLOAD MODEL
          </Button>
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer
        anchor="left" // Drawer opens from the left
        open={drawerOpen}
        onClose={handleDrawerToggle}
      >
        {drawer}
      </Drawer>
    </>
  );
};

export default Navbar;