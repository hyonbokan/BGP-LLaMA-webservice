import React, { useState, useEffect } from 'react';
import { Box, TextField, IconButton, List, ListItem, ListItemText, Paper, Typography, Button } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import Navbar from '../components/Navbar';

const BGPchat = () => {
    const [messages, setMessages] = useState([{ text: "Welcome to BGP-LLaMA Chat!", sender: "system" }]);
    const [currentMessage, setCurrentMessage] = useState('');
    const [eventSource, setEventSource] = useState(null);

    const handleSendMessage = () => {
        if (currentMessage.trim() !== '') {
            setMessages(prevMessages => [...prevMessages, { text: currentMessage, sender: "user" }]);
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
                    setMessages(prevMessages => {
                        const updatedMessages = [...prevMessages];
                        const lastMessageIndex = updatedMessages.length - 1;
                        if (updatedMessages[lastMessageIndex].sender === "system") {
                            updatedMessages[lastMessageIndex].text = accumulatedResponse;
                        } else {
                            updatedMessages.push({ text: accumulatedResponse, sender: "system" });
                        }
                        return updatedMessages;
                    });
                }
            };

            newEventSource.onerror = function(error) {
                console.error('EventSource failed:', error);
                newEventSource.close();
            };

            newEventSource.onclose = function() {
                // Ensure the final accumulated response is added to the messages
                setMessages(prevMessages => {
                    const updatedMessages = [...prevMessages];
                    const lastMessageIndex = updatedMessages.length - 1;
                    if (updatedMessages[lastMessageIndex].sender === "system") {
                        updatedMessages[lastMessageIndex].text = accumulatedResponse.trim();
                    } else {
                        updatedMessages.push({ text: accumulatedResponse.trim(), sender: "system" });
                    }
                    return updatedMessages;
                });
            };

            setEventSource(newEventSource);
        }
    };

    const handleMessageChange = (event) => {
        setCurrentMessage(event.target.value);
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
            <Navbar />
            <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
                <Box sx={{ width: 250, bgcolor: '#f4f4f8', overflowY: 'auto', borderRight: '1px solid #e0e0e0' }}>
                    {/* Sidebar setup */}
                </Box>
                <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', bgcolor: '#ffffff' }}>
                    <Paper sx={{ flex: 1, overflow: 'auto', p: 2 }}>
                        <List sx={{ padding: 0 }}>
                            {messages.map((message, index) => (
                                <ListItem key={index} alignItems="flex-start" sx={{ display: 'flex', flexDirection: message.sender === 'system' ? 'row' : 'row-reverse' }}>
                                    <ListItemText
                                        primary={message.text}
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
                        <IconButton color="primary" onClick={handleSendMessage}>
                            <SendIcon />
                        </IconButton>
                    </Box>
                </Box>
            </Box>
        </Box>
    );
};

export default BGPchat;