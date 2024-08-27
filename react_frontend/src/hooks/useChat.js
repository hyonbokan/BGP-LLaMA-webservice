import { useState } from 'react';

const useChat = ({ currentMessage, setCurrentMessage, setIsGenerating, setIsCollectingData, eventSource, setEventSource, setOutputMessage, outputMessage }) => {
    const [chatTabs, setChatTabs] = useState([{ id: 1, label: 'Chat 1', messages: [{ text: "Welcome to BGP-LLaMA Chat!", sender: "system" }] }]);
    const [currentTab, setCurrentTab] = useState(0);
    const [menuAnchorEl, setMenuAnchorEl] = useState(null);
    const [renameDialogOpen, setRenameDialogOpen] = useState(false);
    const [renameValue, setRenameValue] = useState('');
    const [tabToEdit, setTabToEdit] = useState(null);

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

    const handleSendMessage = async () => {
        if (currentMessage.trim() !== '') {
            setIsGenerating(true);
            setIsCollectingData(true);

            const userMessage = { text: currentMessage, sender: "user" };
            const collectingMessage = { text: "Collecting BGP messages...", sender: "system" };

            const updatedTabs = chatTabs.map((tab, index) => {
                if (index === currentTab) {
                    return { ...tab, messages: [...tab.messages, userMessage, collectingMessage] };
                }
                return tab;
            });

            setChatTabs(updatedTabs);
            setCurrentMessage('');
            setOutputMessage('');

            if (eventSource) {
                eventSource.close();  // Close any existing connection
            }

            const url = `http://127.0.0.1:8000/api/bgp_llama?query=${encodeURIComponent(currentMessage)}`;
            const newEventSource = new EventSource(url);

            newEventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);

                if (data.status === "collecting") {
                    setIsCollectingData(true);
                }

                else if (data.status === "generating" && data.generated_text) {
                    setOutputMessage(prev => prev + data.generated_text + ' ');
                }
            };

            newEventSource.onerror = function(error) {
                console.error('EventSource failed:', error);
                newEventSource.close();
                setIsGenerating(false);
                setIsCollectingData(false);
            };

            newEventSource.onclose = function() {
                setChatTabs(prevTabs => prevTabs.map((tab, index) => {
                    if (index === currentTab) {
                        return { ...tab, messages: [...tab.messages, { text: outputMessage.trim(), sender: "system" }] };
                    }
                    return tab;
                }));
                setOutputMessage('');
                setIsGenerating(false);
                setIsCollectingData(false);
            };

            setEventSource(newEventSource);
        }
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
