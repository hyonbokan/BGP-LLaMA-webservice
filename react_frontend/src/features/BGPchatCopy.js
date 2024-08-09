import React, { useState, useEffect } from 'react';
import { Box, Paper, List, ListItem, TextField, IconButton, Button, Tabs, Tab, Typography, Menu, MenuItem, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, CircularProgress, Card, CardContent } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import Navbar from '../components/Navbar';
import axiosInstance from '../utils/axiosInstance';

const BGPchatCopy = () => {
    const [currentMessage, setCurrentMessage] = useState('');
    const [eventSource, setEventSource] = useState(null);
    const [chatTabs, setChatTabs] = useState([{ id: 1, label: 'Chat 1', messages: [{ text: "Welcome to BGP-LLaMA Chat!", sender: "system" }] }]);
    const [currentTab, setCurrentTab] = useState(0);
    const [menuAnchorEl, setMenuAnchorEl] = useState(null);
    const [renameDialogOpen, setRenameDialogOpen] = useState(false);
    const [renameValue, setRenameValue] = useState('');
    const [tabToEdit, setTabToEdit] = useState(null);
    const [isLoadingModel, setIsLoadingModel] = useState(true);
    const [partialMessage, setPartialMessage] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);


    // useEffect(() => {
    //     // Function to load the model
    //     const loadModel = async () => {
    //         try {
    //             const response = await axiosInstance.post('load_model');
    //             console.log(response.data);
    //             setIsLoadingModel(false);
    //         } catch (error) {
    //             console.error('Error loading model:', error);
    //             setIsLoadingModel(false);
    //         }
    //     };

    //     // Function to unload the model
    //     const unloadModel = async () => {
    //         try {
    //             const response = await axiosInstance.post('unload_model');
    //             console.log('Model unloaded successfully:', response.data);
    //         } catch (error) {
    //             console.error('Error unloading model:', error);
    //         }
    //     };

    //     loadModel();

    //     // Unload model on component unmount
    //     return () => {
    //         unloadModel();
    //     };
    // }, []);

    const handleNewChat = () => {
        const newChatId = chatTabs.length + 1;
        setChatTabs([...chatTabs, { id: newChatId, label: `Chat ${newChatId}`, messages: [{ text: "Welcome to BGP-LLaMA Chat!", sender: "system" }] }]);
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
            const userMessage = { text: currentMessage, sender: "user" };
            const updatedTabs = chatTabs.map((tab, index) => {
                if (index === currentTab) {
                    return { ...tab, messages: [...tab.messages, userMessage] };
                }
                return tab;
            });

            setChatTabs(updatedTabs);
            setCurrentMessage('');
            setPartialMessage('');
            setIsGenerating(true);

            if (eventSource) {
                eventSource.close();  // Close any existing connection
            }

            const url = `http://127.0.0.1:8000/api/bgp_llama?query=${encodeURIComponent(currentMessage)}`;
            const newEventSource = new EventSource(url);

            newEventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.generated_text) {
                    setPartialMessage(prev => prev + data.generated_text + ' ');
                }
            };

            newEventSource.onerror = function(error) {
                console.error('EventSource failed:', error);
                newEventSource.close();
                setIsGenerating(false);
            };

            newEventSource.onclose = function() {
                setChatTabs(prevTabs => prevTabs.map((tab, index) => {
                    if (index === currentTab) {
                        return { ...tab, messages: [...tab.messages, { text: partialMessage.trim(), sender: "system" }] };
                    }
                    return tab;
                }));
                setPartialMessage('');
                setIsGenerating(false);
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
            {isLoadingModel ? (
                <Box sx={{ display: 'flex', flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                    <CircularProgress />
                    <Typography sx={{ ml: 2, fontFamily: 'monospace', fontWeight: 'bold' }}>Loading the model, please wait...</Typography>
                </Box>
            ) : (
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
                                    <React.Fragment key={index}>
                                        {message.sender === "user" && (
                                            <ListItem alignItems="flex-start" sx={{ display: 'flex', flexDirection: 'row-reverse' }}>
                                                <Card sx={{ bgcolor: '#e3f2fd', borderRadius: 2, maxWidth: '60%' }}>
                                                    <CardContent>
                                                        <Typography sx={{ fontFamily: 'monospace', fontWeight: 'medium', color: 'primary.main', textAlign: 'right' }}>
                                                            {message.text}
                                                        </Typography>
                                                    </CardContent>
                                                </Card>
                                            </ListItem>
                                        )}
                                        {message.sender === "system" && (
                                            <ListItem alignItems="flex-start" sx={{ display: 'flex', flexDirection: 'row' }}>
                                                <Card sx={{ bgcolor: '#e0e0e0', borderRadius: 2, maxWidth: '60%' }}>
                                                    <CardContent>
                                                        <Typography sx={{ fontFamily: 'monospace', fontWeight: 'medium', color: 'gray', textAlign: 'left' }}>
                                                            {message.text}
                                                        </Typography>
                                                    </CardContent>
                                                </Card>
                                            </ListItem>
                                        )}
                                    </React.Fragment>
                                ))}
                                {partialMessage && (
                                    <ListItem alignItems="flex-start" sx={{ display: 'flex', flexDirection: 'row' }}>
                                        <Card sx={{ bgcolor: '#e0e0e0', borderRadius: 2, maxWidth: '60%' }}>
                                            <CardContent>
                                                <Typography sx={{ fontFamily: 'monospace', fontWeight: 'medium', color: 'gray', textAlign: 'left' }}>
                                                    {partialMessage}
                                                </Typography>
                                            </CardContent>
                                        </Card>
                                    </ListItem>
                                )}
                            </List>
                        </Paper>
                        <Box
                            component="form"
                            sx={{ display: 'flex', alignItems: 'center', p: 2, bgcolor: '#f4f4f8' }}
                            onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
                        >
                            <TextField
                                label="Input your prompt..."
                                fullWidth
                                variant="outlined"
                                value={currentMessage}
                                onChange={handleMessageChange}
                                multiline
                                maxRows={4}
                                sx={{ mr: 1 }}
                            />
                            {isGenerating ? (
                                <CircularProgress 
                                    size={24}
                                    sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }} 
                                />
                            ) : (
                                <IconButton 
                                    color="primary" 
                                    onClick={handleSendMessage}
                                    sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}
                                >
                                    <SendIcon sx={{ transform: 'rotate(-45deg)' }}/>
                                </IconButton>
                            )}
                        </Box>
                    </Box>
                </Box>
            )}

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

export default BGPchatCopy;