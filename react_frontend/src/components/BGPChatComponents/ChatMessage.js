import React from 'react';
import { ListItem, Card, CardContent, Typography } from '@mui/material';

const ChatMessage = ({ message }) => (
    <ListItem
        alignItems="flex-start"
        sx={{
            display: 'flex',
            flexDirection: message.sender === "user" ? 'row-reverse' : 'row',
        }}
    >
        <Card
            sx={{
                bgcolor: message.sender === "user" ? '#90d3ff' : '#ededed',
                borderRadius: 2,
                maxWidth: '70%',
            }}
        >
            <CardContent>
                <Typography
                    sx={{
                        fontFamily: 'monospace',
                        fontWeight: 'medium',
                        color: 'black',
                        textAlign: message.sender === "user" ? 'right' : 'left', // Align right for user, left for system
                        whiteSpace: 'pre-line', // Preserve line breaks
                    }}
                >
                    {message.text}
                </Typography>
            </CardContent>
        </Card>
    </ListItem>
);

export default ChatMessage;