import { useState, useRef, useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';
import BGPChatTutorial from '../components/BGPChatTutorial';
import GPTChatTutorial from '../components/GPTChatTutorial';

const useBGPChat = ({
    currentMessage,
    setCurrentMessage,
    setIsGenerating,
    setIsCollectingData,
    eventSource,
    setEventSource,
    setOutputMessage,
    outputMessage,
}) => {
    const [chatTabs, setChatTabs] = useState([
        { 
            id: 1, 
            label: 'Chat 1', 
            messages: [] 
        }
    ]);
    const [currentTab, setCurrentTab] = useState(0);
    const [menuAnchorEl, setMenuAnchorEl] = useState(null);
    const [renameDialogOpen, setRenameDialogOpen] = useState(false);
    const [renameValue, setRenameValue] = useState('');
    const [tabToEdit, setTabToEdit] = useState(null);
    const [selectedModel, setSelectedModel] = useState('gpt_4o_mini')

    // Use refs for indices
    const generatingMessageIndexRef = useRef(null);

    // useEffect(() => {
    //     console.log('Updated chatTabs:', chatTabs);
    // }, [chatTabs]);
    useEffect(() => {
        const tutorialMessage = {
            text: selectedModel === 'bgp_llama' ? <BGPChatTutorial /> : <GPTChatTutorial />,
            sender: "system"
        };
    
        setChatTabs((prevTabs) => 
            prevTabs.map((tab, index) => {
                if (index === currentTab) {
                    const messages = [...tab.messages];
                    if (messages.length > 0 && messages[0].sender === 'system') {
                        messages[0] = tutorialMessage; // Replace existing tutorial
                    } else {
                        messages.unshift(tutorialMessage); // Add new tutorial
                    }
                    return { ...tab, messages };
                }
                return tab;
            })
        );
    }, [selectedModel, currentTab]);

    const handleNewChat = () => {
        const newChatId = chatTabs.length + 1;
        const tutorialMessage = {
            text: selectedModel === 'bgp_llama' ? <BGPChatTutorial /> : <GPTChatTutorial />,
            sender: "system"
        };
        setChatTabs([...chatTabs, { 
            id: newChatId, 
            label: `Chat ${newChatId}`, 
            messages: [tutorialMessage] 
        }]);
        setCurrentTab(newChatId - 1);
        if (eventSource) {
            eventSource.close();
        }
        generatingMessageIndexRef.current = null;
    };

    const handleTabChange = (event, newValue) => {
        setCurrentTab(newValue);
        if (eventSource) {
            eventSource.close();
        }
        generatingMessageIndexRef.current = null;
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
        generatingMessageIndexRef.current = null;
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
        setChatTabs((prevTabs) =>
            prevTabs.map((tab, index) =>
                index === currentTab ? { ...tab, messages: [...tab.messages, newMessage] } : tab
            )
        );
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
    
            // Add the new collecting message and reset generating index
            updateChatTabs(collectingMessage);
            generatingMessageIndexRef.current = null;  // Reset for a new message
        }
    
        if (data.status === 'generating' && data.generated_text) {        
            // Append to the current message being generated
            setChatTabs((prevTabs) => {
                return prevTabs.map((tab, index) => {
                    if (index === currentTab) {
                        let messages = [...tab.messages];
    
                        // If no ongoing message, start a new one
                        if (generatingMessageIndexRef.current === null) {
                            const assistantMessage = {
                                text: data.generated_text, // Start with the current token
                                sender: 'system',
                            };
                            messages.push(assistantMessage);
                            generatingMessageIndexRef.current = messages.length - 1; // Track the index of the ongoing message
                        } else {
                            // Append to the ongoing message
                            messages = messages.map((msg, msgIndex) => {
                                if (msgIndex === generatingMessageIndexRef.current) {
                                    return {
                                        ...msg,
                                        text: (msg.text || '') + data.generated_text, // Append tokens to the same message
                                    };
                                } else {
                                    return msg;
                                }
                            });
                        }
    
                        return { ...tab, messages };
                    } else {
                        return tab;
                    }
                });
            });
        }
    
        if (data.status === 'complete') {
            console.log('\nCompleted output data event');
            setIsCollectingData(false);
            setIsGenerating(false);
            generatingMessageIndexRef.current = null; // Reset the index after message completion
            setOutputMessage(''); // Clear the output message
        }

        // if (data.status === 'error' && data.message) {
        //     console.error('\nError event:', data.message);
        //     setIsCollectingData(false);
        //     setIsGenerating(false);
        //     generatingMessageIndexRef.current = null; // Reset the index after message completion

        //     const errorMessage = { text: `Error: ${data.message}`, sender: "system" };
        //     updateChatTabs(errorMessage);
        // }

    };
    
    
    const handleEventSourceError = (eventSource) => {
        console.error('EventSource failed:', eventSource);
        eventSource.close();
        setIsGenerating(false);
        setIsCollectingData(false);
        generatingMessageIndexRef.current = null;
    };
    
    const handleEventSourceClose = () => {
        setOutputMessage('');
        setIsGenerating(false);
        setIsCollectingData(false);
        generatingMessageIndexRef.current = null;
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
        const baseUrl = 'https://llama.cnu.ac.kr/api';
        const endpoint = selectedModel === 'bgp_llama' ? 'bgp_llama' : 'gpt_4o_mini';
        const url = `${baseUrl}/${endpoint}?query=${encodeURIComponent(currentMessage)}`;

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
        selectedModel,
        setSelectedModel,
    };
};

export default useBGPChat;