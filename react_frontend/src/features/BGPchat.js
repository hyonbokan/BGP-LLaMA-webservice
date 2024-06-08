import React, { useState } from 'react';
import { Box, Paper, List, ListItem, ListItemText, TextField, IconButton, Button, Tabs, Tab, Typography, Menu, MenuItem, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import Navbar from '../components/Navbar';

const BGPchat = () => {
    const [currentMessage, setCurrentMessage] = useState('');
    const [eventSource, setEventSource] = useState(null);
    const [chatTabs, setChatTabs] = useState([{ id: 1, label: 'Chat 1', messages: [{ text: <Typography sx={{ fontFamily: "monospace" }}>Welcome to BGP-LLaMA Chat!</Typography>, sender: "system" }] }]);
    const [currentTab, setCurrentTab] = useState(0);
    const [menuAnchorEl, setMenuAnchorEl] = useState(null);
    const [renameDialogOpen, setRenameDialogOpen] = useState(false);
    const [renameValue, setRenameValue] = useState('');
    const [tabToEdit, setTabToEdit] = useState(null);

    const handleNewChat = () => {
        const newChatId = chatTabs.length + 1;
        setChatTabs([...chatTabs, { id: newChatId, label: `Chat ${newChatId}`, messages: [{ text: <Typography sx={{ fontFamily: "monospace" }}>Welcome to BGP-LLaMA Chat!</Typography>, sender: "system" }] }]);
        setCurrentTab(newChatId - 1);
        if (eventSource) {
            eventSource.close(); // Close any existing connection
        }
    };

    const handleTabChange = (event, newValue) => {
        setCurrentTab(newValue);
        if (eventSource) {
            eventSource.close(); // Close any existing connection
        }
    };

    const handleSendMessage = () => {
        if (currentMessage.trim() !== '') {
            const updatedTabs = chatTabs.map((tab, index) => {
                if (index === currentTab) {
                    return { ...tab, messages: [...tab.messages, { text: currentMessage, sender: "user" }] };
                }
                return tab;
            });

            setChatTabs(updatedTabs);
            setCurrentMessage('');

            if (eventSource) {
                eventSource.close();  // Close any existing connection
            }

            const url = `http://127.0.0.1:8001/api/bgp-llama?query=${encodeURIComponent(currentMessage)}`;
            const newEventSource = new EventSource(url);

            let accumulatedResponse = '';  // Initialize accumulated response

            newEventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.generated_text) {
                    accumulatedResponse += data.generated_text + ' ';
                    const updatedTabsWithResponse = chatTabs.map((tab, index) => {
                        if (index === currentTab) {
                            const updatedMessages = [...tab.messages];
                            const lastMessageIndex = updatedMessages.length - 1;
                            if (updatedMessages[lastMessageIndex].sender === "system") {
                                updatedMessages[lastMessageIndex].text = accumulatedResponse;
                            } else {
                                updatedMessages.push({ text: accumulatedResponse, sender: "system" });
                            }
                            return { ...tab, messages: updatedMessages };
                        }
                        return tab;
                    });
                    setChatTabs(updatedTabsWithResponse);
                }
            };

            newEventSource.onerror = function(error) {
                console.error('EventSource failed:', error);
                newEventSource.close();
            };

            newEventSource.onclose = function() {
                const updatedTabsWithFinalResponse = chatTabs.map((tab, index) => {
                    if (index === currentTab) {
                        const updatedMessages = [...tab.messages];
                        const lastMessageIndex = updatedMessages.length - 1;
                        if (updatedMessages[lastMessageIndex].sender === "system") {
                            updatedMessages[lastMessageIndex].text = accumulatedResponse.trim();
                        } else {
                            updatedMessages.push({ text: accumulatedResponse.trim(), sender: "system" });
                        }
                        return { ...tab, messages: updatedMessages };
                    }
                    return tab;
                });
                setChatTabs(updatedTabsWithFinalResponse);
            };

            setEventSource(newEventSource);
        }
    };

    const handleMessageChange = (event) => {
        setCurrentMessage(event.target.value);
    };

    const handleMenuOpen = (event, tab) => {
        setMenuAnchorEl(event.currentTarget);
        setTabToEdit(tab);
    };

    const handleMenuClose = () => {
        setMenuAnchorEl(null);
        setTabToEdit(null);
    };

    const handleDeleteTab = () => {
        const updatedTabs = chatTabs.filter(tab => tab.id !== tabToEdit.id);
        setChatTabs(updatedTabs);
        setMenuAnchorEl(null);
        if (tabToEdit.id === currentTab) {
            setCurrentTab(0);
        }
        if (eventSource) {
            eventSource.close(); // Close any existing connection
        }
    };

    const handleRenameTab = () => {
        setRenameDialogOpen(true);
        setRenameValue(tabToEdit.label);
        setMenuAnchorEl(null);
    };

    const handleRenameDialogClose = () => {
        setRenameDialogOpen(false);
        setRenameValue('');
        setTabToEdit(null);
    };

    const handleRenameDialogSave = () => {
        const updatedTabs = chatTabs.map(tab => tab.id === tabToEdit.id ? { ...tab, label: renameValue } : tab);
        setChatTabs(updatedTabs);
        setRenameDialogOpen(false);
        setRenameValue('');
        setTabToEdit(null);
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
                    <Tabs
                        orientation="vertical"
                        value={currentTab}
                        onChange={handleTabChange}
                        sx={{ borderRight: 1, borderColor: 'divider' }}
                    >
                        {chatTabs.map((tab, index) => (
                            <Tab
                                key={tab.id}
                                label={
                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                        {tab.label}
                                        <IconButton
                                            size="small"
                                            onClick={(event) => handleMenuOpen(event, tab)}
                                            sx={{ ml: 1 }}
                                        >
                                            <MoreVertIcon fontSize="small" />
                                        </IconButton>
                                    </Box>
                                }
                                sx={{ fontFamily: 'monospace' }}
                            />
                        ))}
                    </Tabs>
                </Box>
                <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', bgcolor: '#ffffff' }}>
                    <Paper sx={{ flex: 1, overflow: 'auto', p: 2 }}>
                        <List sx={{ padding: 0 }}>
                            {chatTabs[currentTab].messages.map((message, index) => (
                                <ListItem key={index} alignItems="flex-start" sx={{ display: 'flex', flexDirection: message.sender === 'system' ? 'row' : 'row-reverse' }}>
                                    <ListItemText
                                        primary={<Typography sx={{ fontFamily: 'monospace' }}>{message.text}</Typography>}
                                        primaryTypographyProps={{
                                            sx: {
                                                fontWeight: 'medium',
                                                color: message.sender === 'system' ? 'gray' : 'primary.main',
                                                textAlign: message.sender === 'system' ? 'left' : 'right',
                                                bgcolor: message.sender === 'system' ? '#e0e0e0' : '#e3f2fd',
                                                borderRadius: 2,
                                                p: 1,
                                            }
                                        }}
                                    />
                                </ListItem>
                            ))}
                        </List>
                    </Paper>
                    <Box
                        component="form"
                        sx={{ display: 'flex', alignItems: 'center', p: 2, bgcolor: '#f4f4f8' }}
                        onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
                    >
                        <TextField
                            label="Type your message..."
                            fullWidth
                            variant="outlined"
                            value={currentMessage}
                            onChange={handleMessageChange}
                            multiline
                            maxRows={4}
                            sx={{ mr: 1 }}
                        />
                        <IconButton 
                            color="primary" 
                            onClick={handleSendMessage}
                            sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}
                        >
                            <SendIcon sx={{ transform: 'rotate(-45deg)' }}/>
                        </IconButton>
                    </Box>
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