import React, { useState } from 'react';
import { Box, Paper, List, Typography, Menu, MenuItem, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, TextField, Button } from '@mui/material';
import Navbar from '../components/PageComponents/Navbar';
import ChatTabs from '../components/BGPChatComponents/ChatTabs';
import ChatMessage from '../components/BGPChatComponents/ChatMessage';
import ChatInputField from '../components/BGPChatComponents/ChatInputField';
import useChat from '../hooks/useChat';

const BGPchat = () => {
    const [currentMessage, setCurrentMessage] = useState('');
    const [eventSource, setEventSource] = useState(null);
    const [outputMessage, setOutputMessage] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [isCollectingData, setIsCollectingData] = useState(false);

    const {
        chatTabs,
        currentTab,
        handleNewChat,
        handleTabChange,
        handleSendMessage,
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
    } = useChat({
        currentMessage,
        setCurrentMessage,
        setIsGenerating,
        setIsCollectingData,
        eventSource,
        setEventSource,
        setOutputMessage,
        outputMessage,
    });

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
            <Navbar />
            <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
                <Box sx={{ width: 250, bgcolor: '#f4f4f8', overflowY: 'auto', borderRight: '1px solid #e0e0e0' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
                        <Button
                            variant="contained"
                            onClick={handleNewChat}
                            sx={{ m: 2, width: '200px'}}
                        >
                            <Typography sx={{ fontFamily: 'monospace'}}>
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
                <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', bgcolor: '#ffffff' }}>
                    <Paper sx={{ flex: 1, overflow: 'auto', p: 2 }}>
                        <List sx={{ padding: 0 }}>
                            {chatTabs[currentTab].messages.map((message, index) => (
                                <ChatMessage key={index} message={message} />
                            ))}
                            {outputMessage && <ChatMessage message={{ text: outputMessage, sender: 'system' }} />}
                        </List>
                    </Paper>
                    <ChatInputField
                        currentMessage={currentMessage}
                        handleMessageChange={handleMessageChange}
                        handleSendMessage={handleSendMessage}
                        handleKeyPress={handleKeyPress}
                        isGenerating={isGenerating}
                        isCollectingData={isCollectingData}
                    />
                </Box>
            </Box>

            <Menu
                anchorEl={menuAnchorEl}
                open={Boolean(menuAnchorEl)}
                onClose={handleMenuClose}
            >
                <MenuItem onClick={handleDeleteTab}>Delete</MenuItem>
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
