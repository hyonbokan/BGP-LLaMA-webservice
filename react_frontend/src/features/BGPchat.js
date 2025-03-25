import React, { useState } from 'react';
import {
    Box, Button, Typography, Paper, List, Menu, MenuItem, Dialog,
    DialogTitle, DialogContent, DialogContentText, DialogActions,
    TextField, useTheme, useMediaQuery,
    Drawer, ToggleButton, ToggleButtonGroup,
    } from '@mui/material';
import { styled } from '@mui/material/styles';
import Navbar from '../components/PageComponents/Navbar';
import ChatTabs from '../components/BGPChatComponents/ChatTabs';
import ChatMessage from '../components/BGPChatComponents/ChatMessage';
import ChatInputField from '../components/BGPChatComponents/ChatInputField';
import useBGPChat from '../hooks/useBGPChat';

const RoundToggleButton = styled(ToggleButton)(({ theme }) => ({
  width: '100px',
  height: '40px',
  minWidth: '40px',
  minHeight: '40px',
  padding: '0',
}));

const BGPchat = () => {
    const [currentMessage, setCurrentMessage] = useState('');
    const [eventSource, setEventSource] = useState(null);
    const [outputMessage, setOutputMessage] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);

    const {
      chatTabs,
      currentTab,
      handleNewChat,
      handleTabChange,
      handleSendMessage, 
      handleRunCode, 
      handleMessageChange,
      handleMenuOpen,
      handleMenuClose,
      handleDeleteTab,
      handleRenameTab,
      handleRenameDialogClose,
      handleRenameDialogSave,
      renameDialogOpen,
      menuAnchorEl,
      renameValue,
      setRenameValue,
      selectedModel,
      setSelectedModel,
      generatedCode,
      executionOutput,
      isRunningCode,
  } = useBGPChat({
      currentMessage,
      setCurrentMessage,
      setIsGenerating,
      eventSource,
      setEventSource,
      setOutputMessage,
      outputMessage,
  });

  const handleModelChange = (event, newModel) => {
    if (newModel !== null) {
        setSelectedModel(newModel);
    }
};

const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
};

const [mobileOpen, setMobileOpen] = useState(false);

const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
};

const theme = useTheme();
const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
const drawerWidth = 250;

const drawerContent = (
  <Box
    sx={{
      width: drawerWidth,
      bgcolor: '#f4f4f8',
      overflowY: 'auto',
      borderRight: '1px solid #e0e0e0',
      height: '100%',
      p: 0,
      m: 0,
    }}
  >
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 0, m: 0 }}>
      <Button
        variant="contained"
        onClick={handleNewChat}
        sx={{ m: 2, width: { xs: '100%', sm: '200px' } }}
      >
        <Typography sx={{ fontFamily: 'monospace' }}>
          New Chat
        </Typography>
      </Button>
    </Box>
    <ChatTabs
      chatTabs={chatTabs}
      currentTab={currentTab}
      handleTabChange={handleTabChange}
      handleNewChat={handleNewChat}
      handleMenuOpen={handleMenuOpen}
    />
  </Box>
);

return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Navbar />
      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        <Drawer
          variant={isMobile ? "temporary" : "permanent"}
          open={isMobile ? mobileOpen : true}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            '& .MuiDrawer-paper': {
              borderBottom: 'none',
              boxShadow: 'none',
              [theme.breakpoints.up('sm')]: {
                width: drawerWidth,
                position: 'relative',
              },
            },
          }}
        >
          {drawerContent}
        </Drawer>
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', bgcolor: '#ffffff' }}>

          {/* Model switch button */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 1 }}>
            <ToggleButtonGroup
                value={selectedModel}
                exclusive
                onChange={handleModelChange}
                aria-label="Model selection"
            >
                <RoundToggleButton value="bgp_llama" aria-label="BGP LLaMA">
                  <Typography variant="caption" fontFamily='monospace' fontWeight={700}>BGP-LLaMA</Typography>
                </RoundToggleButton>
                <RoundToggleButton value="gpt_4o_mini" aria-label="GPT-4o-mini">
                    <Typography variant="caption" fontFamily='monospace' fontWeight={700}>BGP-GPT</Typography>
                </RoundToggleButton>
            </ToggleButtonGroup>
        </Box>

        {/* Chat Messages */}
          <Paper sx={{ flex: 1, overflow: 'auto', p: 2 }}>
            <List sx={{ padding: 0 }}>
              {chatTabs[currentTab]?.messages.map((message, index) => (
                <ChatMessage key={index} message={message} />
              ))}
              {/* Display execution output if available */}
              {executionOutput && (
                  <ChatMessage message={{ text: executionOutput, sender: 'system' }} />
              )}
            </List>
          </Paper>
          {/* Conditionally Render "Run Code" Button */}
          {generatedCode && (
              <Box sx={{ p: 1 }}>
                  <Button 
                      variant="contained" 
                      color="success"
                      onClick={handleRunCode}
                      disabled={isRunningCode}
                      fullWidth
                  >
                      {isRunningCode ? 'Running...' : 'Run Code'}
                  </Button>
              </Box>
          )}
          <ChatInputField
            currentMessage={currentMessage}
            handleMessageChange={handleMessageChange}
            handleSendMessage={handleSendMessage}
            handleKeyPress={handleKeyPress}
            isGenerating={isGenerating}
            isRunningCode={isRunningCode}
          />
        </Box>
      </Box>
      {/* Menu and dialog code */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleDeleteTab} disabled={chatTabs.length === 1}>
            Delete
        </MenuItem>
        <MenuItem onClick={handleRenameTab}>Rename</MenuItem>
      </Menu>

      <Dialog open={renameDialogOpen} onClose={handleRenameDialogClose}>
        <DialogTitle>Rename Chat</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Enter a new name for the chat.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            label="Chat Name"
            fullWidth
            variant="outlined"
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleRenameDialogClose}>Cancel</Button>
          <Button onClick={handleRenameDialogSave} color="primary">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BGPchat;