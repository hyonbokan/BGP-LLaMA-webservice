import React from 'react';
import { Box, Tabs, Tab, IconButton } from '@mui/material';
import MoreVertIcon from '@mui/icons-material/MoreVert';

const ChatTabs = ({ chatTabs, currentTab, handleTabChange, handleMenuOpen }) => (
    <Box sx={{ width: 250, bgcolor: '#f4f4f8', overflowY: 'auto', borderRight: '1px solid #e0e0e0' }}>
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
);

export default ChatTabs;
