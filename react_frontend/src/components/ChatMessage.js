import React from 'react';
import { ListItem, Card, CardContent, Typography } from '@mui/material';

const ChatMessage = ({ message }) => (
    <ListItem alignItems="flex-start" sx={{ display: 'flex', flexDirection: message.sender === "user" ? 'row-reverse' : 'row' }}>
        <Card sx={{ bgcolor: message.sender === "user" ? '#e3f2fd' : '#e0e0e0', borderRadius: 2, maxWidth: '60%' }}>
            <CardContent>
                <Typography sx={{ fontFamily: 'monospace', fontWeight: 'medium', color: message.sender === "user" ? 'primary.main' : 'gray', textAlign: message.sender === "user" ? 'right' : 'left' }}>
                    {message.text}
                </Typography>
            </CardContent>
        </Card>
    </ListItem>
);

export default ChatMessage;