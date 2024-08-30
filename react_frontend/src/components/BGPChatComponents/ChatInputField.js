import React from 'react';
import { Box, TextField, IconButton, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const ChatInputField = ({ currentMessage, handleMessageChange, handleSendMessage, handleKeyPress, isGenerating, isCollectingData }) => (
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
            onKeyPress={handleKeyPress}  // Add this line
            multiline
            maxRows={4}
            sx={{ mr: 1 }}
        />
        {isGenerating || isCollectingData ? (
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
);

export default ChatInputField;
