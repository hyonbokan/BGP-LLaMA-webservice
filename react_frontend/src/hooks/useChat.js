import { useState, useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';

const useChat = ({ currentMessage, setCurrentMessage, setIsGenerating, setIsCollectingData, eventSource, setEventSource, setOutputMessage, outputMessage }) => {
    const [chatTabs, setChatTabs] = useState([{ id: 1, label: 'Chat 1', messages: [{ text: "Welcome to BGP-LLaMA Chat!", sender: "system" }] }]);
    const [currentTab, setCurrentTab] = useState(0);
    const [menuAnchorEl, setMenuAnchorEl] = useState(null);
    const [renameDialogOpen, setRenameDialogOpen] = useState(false);
    const [renameValue, setRenameValue] = useState('');
    const [tabToEdit, setTabToEdit] = useState(null);
    const [collectingMessageIndex, setCollectingMessageIndex] = useState(null);

    useEffect(() => {
        console.log('Updated chatTabs:', chatTabs);
    }, [chatTabs]);

    const handleNewChat = () => {
        const newChatId = chatTabs.length + 1;
        setChatTabs([...chatTabs, { id: newChatId, label: `Chat ${newChatId}`, messages: [{ text: "Welcome to BGP-LLaMA Chat!", sender: "system" }] }]);
        setCurrentTab(newChatId - 1);
        if (eventSource) {
            eventSource.close();
        }
    };

    const handleTabChange = (event, newValue) => {
        setCurrentTab(newValue);
        if (eventSource) {
            eventSource.close();
        }
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
            eventSource.close();
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

    const updateChatTabs = (newMessage) => {
        setChatTabs(prevTabs =>
            prevTabs.map((tab, index) =>
                index === currentTab
                    ? { ...tab, messages: [...tab.messages, newMessage] }
                    : tab
            )
        );
    };

    const replaceCollectingMessage = (newMessage) => {
        setChatTabs(prevTabs => 
            prevTabs.map((tab, index) =>
                index === currentTab && collectingMessageIndex !== null
                    ? {
                        ...tab,
                        messages: tab.messages.map((msg, i) =>
                            i === collectingMessageIndex ? newMessage : msg
                        ),
                    }
                    : tab
            )
        );
        setCollectingMessageIndex(null); // Clear the index after replacing
    };
    
    const handleEventSourceMessage = (data) => {
        if (data.status === "collecting") {
            console.log("\nCollecting data event");
            setIsCollectingData(true);

            const collectingMessage = {
                text: (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        Collecting BGP messages
                        <Box sx={{ width: '8px' }} /> {/* Adding space */}
                        <CircularProgress size={16} sx={{ mr: 1 }} />
                    </Box>
                ),
                sender: "system"
            };

            updateChatTabs(collectingMessage);
            setCollectingMessageIndex(chatTabs[currentTab].messages.length);
        }

        if (data.status === "generating" && data.generated_text) {
            console.log("\nGenerating output data event");
            // Replace the "Collecting BGP messages" message with the final output
            replaceCollectingMessage({
                text: outputMessage.trim(),
                sender: 'system'
            });
            setOutputMessage(prev => prev + data.generated_text + ' ');
        }

        if (data.status === "complete") {
            console.log("\nCompleted output data event");
            setIsCollectingData(false);
        }
    };

    const handleEventSourceError = (eventSource) => {
        // updateChatTabs({ text: "Unexpected error happened", sender: "system" });
        console.error('EventSource failed:', eventSource);
        eventSource.close();
        setIsGenerating(false);
        setIsCollectingData(false);
    };
    
    const handleEventSourceClose = () => {
        updateChatTabs({ text: outputMessage.trim(), sender: "system" });
        setOutputMessage('');
        setIsGenerating(false);
        setIsCollectingData(false);
    };
    
    const handleSendMessage = async () => {
        if (currentMessage.trim() === '') return;
    
        setIsGenerating(true);
        setIsCollectingData(false);
    
        const userMessage = { text: currentMessage, sender: "user" };
        updateChatTabs(userMessage);
    
        setCurrentMessage('');
        setOutputMessage('');
    
        if (eventSource) {
            eventSource.close();
        }
    
        const url = `http://127.0.0.1:8000/api/bgp_llama?query=${encodeURIComponent(currentMessage)}`;
        const newEventSource = new EventSource(url);
    
        newEventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log(data);
            handleEventSourceMessage(data);
        };
    
        newEventSource.onerror = () => handleEventSourceError(newEventSource);
    
        newEventSource.onclose = handleEventSourceClose;
    
        setEventSource(newEventSource);
    };
    
    const handleMessageChange = (event) => {
        setCurrentMessage(event.target.value);
    };

    return {
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
        tabToEdit,
        renameValue,
        setRenameValue,
    };
};

export default useChat;