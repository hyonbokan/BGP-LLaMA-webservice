import { useState, useRef, useEffect } from 'react';
import BGPChatTutorial from '../components/BGPChatComponents/BGPChatTutorial';
import GPTChatTutorial from '../components/BGPChatComponents/GPTChatTutorial';

const useBGPChat = ({
    currentMessage,
    setCurrentMessage,
    setIsGenerating,
    eventSource,
    setEventSource,
    setOutputMessage,
    outputMessage,
}) => {
    const [chatTabs, setChatTabs] = useState([
        { id: 1, label: 'Chat 1', messages: [] }
    ]);
    const [currentTab, setCurrentTab] = useState(0);
    const [menuAnchorEl, setMenuAnchorEl] = useState(null);
    const [renameDialogOpen, setRenameDialogOpen] = useState(false);
    const [renameValue, setRenameValue] = useState('');
    const [tabToEdit, setTabToEdit] = useState(null);
    const [selectedModel, setSelectedModel] = useState('bgp_llama'); // or 'gpt_4o_mini'
    
    const [generatedCode, setGeneratedCode] = useState('');
    const [isRunningCode, setIsRunningCode] = useState(false);
    const [executionOutput, setExecutionOutput] = useState('');
    
    const [wsLLM, setWsLLM] = useState(null);
    const [wsGPT, setWsGPT] = useState(null);
    const [wsCode, setWsCode] = useState(null);
    const generatingMessageIndexRef = useRef(null);
    const baseWsUrl = 'wss://llama.cnu.ac.kr/ws/';

    // Set a tutorial message based on selected model
    const getTutorialMessage = (selectedModel) => {
        switch (selectedModel) {
            case 'bgp_llama':
                return <BGPChatTutorial />;
            case 'gpt_4o_mini':
                return <GPTChatTutorial />;
            default:
                return <BGPChatTutorial />;
        }
    };
    
    useEffect(() => {
        const tutorialMessage = {
            text: getTutorialMessage(selectedModel),
            sender: "tutorial"
        };
    
        setChatTabs((prevTabs) => 
            prevTabs.map((tab, index) => {
                if (index === currentTab) {
                    const messages = [...tab.messages];
                    // Replace the existing tutorial if present or add one at the beginning
                    if (messages.length > 0 && messages[0].sender === 'tutorial') {
                        messages[0] = tutorialMessage;
                    } else {
                        messages.unshift(tutorialMessage);
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
            text: <BGPChatTutorial />,
            sender: "tutorial"
        };
        setChatTabs([...chatTabs, { id: newChatId, label: `Chat ${newChatId}`, messages: [tutorialMessage] }]);
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
        if (chatTabs.length === 1) {
            alert("Cannot delete the last remaining tab.");
            return;
        }
    
        const updatedTabs = chatTabs.filter(tab => tab.id !== tabToEdit.id);
        setChatTabs(updatedTabs);
        setMenuAnchorEl(null);
        
        if (tabToEdit.id === chatTabs[currentTab].id) {
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
        const updatedTabs = chatTabs.map(
            (tab) => tab.id === tabToEdit.id ? { ...tab, label: renameValue } : tab
        );
        setChatTabs(updatedTabs);
        setRenameDialogOpen(false);
        setRenameValue('');
        setTabToEdit(null);
    };
    
    // Append a new message to the current chat tab.
    const updateChatTabs = (newMessage) => {
        setChatTabs((prevTabs) =>
            prevTabs.map((tab, index) =>
                index === currentTab ? { ...tab, messages: [...tab.messages, newMessage] } : tab
            )
        );
    };
    
    // Handle messages received over WebSocket (both GPT and LLaMA use similar message structures)
    const handleWebSocketMessage = (data) => {    
        if (data.status === 'generating' && data.generated_text) {        
            setChatTabs(prevTabs => {
                const updatedTabs = [...prevTabs];
                const currentMessages = [...updatedTabs[currentTab].messages];
    
                // If there's already an ongoing system message (not final), append the new token.
                if (currentMessages.length > 0 && currentMessages[currentMessages.length - 1].sender === 'system' && !currentMessages[currentMessages.length - 1].final) {
                    currentMessages[currentMessages.length - 1] = {
                        ...currentMessages[currentMessages.length - 1],
                        text: currentMessages[currentMessages.length - 1].text + data.generated_text,
                    };
                } else {
                    // Otherwise, start a new system message.
                    currentMessages.push({ text: data.generated_text, sender: 'system', final: false });
                }
                updatedTabs[currentTab].messages = currentMessages;
                return updatedTabs;
            });
        }
    
        if (data.status === 'code_ready') {
            // Mark the last system message as final.
            setChatTabs(prevTabs => {
                const updatedTabs = [...prevTabs];
                const currentMessages = [...updatedTabs[currentTab].messages];
                if (currentMessages.length > 0 && currentMessages[currentMessages.length - 1].sender === 'system') {
                    currentMessages[currentMessages.length - 1] = {
                        ...currentMessages[currentMessages.length - 1],
                        final: true,
                    };
                }
                updatedTabs[currentTab].messages = currentMessages;
                return updatedTabs;
            });
            setGeneratedCode(data.code);
        }
    
        if (data.status === 'no_code_found') {
            updateChatTabs({
                text: 'No code block was found in the response.',
                sender: 'system',
                final: true,
            });
            setGeneratedCode('');
        }
    
        if (data.status === 'error' && data.message) {
            updateChatTabs({ text: `⚠️ Error: ${data.message}`, sender: 'system', final: true });
        }
    
        if (data.status === 'complete') {
            setGeneratedCode('');
            setIsRunningCode(false);
            setIsGenerating(false);
        }
    };
    
    // Handle sending a message. This function chooses the correct endpoint based on the selected model.
    const handleSendMessage = () => {
        if (currentMessage.trim() === '') return;
    
        setIsGenerating(true);
        const userMessage = { text: currentMessage, sender: "user" };
        updateChatTabs(userMessage);
    
        const messageToSend = currentMessage;
        setCurrentMessage('');
    
        // Choose endpoint based on selected model.
        let endpoint = '';
        if (selectedModel === 'gpt_4o_mini') {
            endpoint = 'gpt/';
        } else {
            endpoint = 'llm/';
        }
    
        // Close any existing WebSocket for the selected model.
        if (selectedModel === 'gpt_4o_mini' && wsGPT) {
            wsGPT.close();
        }
        if (selectedModel === 'bgp_llama' && wsLLM) {
            wsLLM.close();
        }
    
        const socketUrl = `${baseWsUrl}${endpoint}`;
        const newWs = new WebSocket(socketUrl);
    
        newWs.onopen = () => {
            newWs.send(JSON.stringify({ query: messageToSend }));
        };
    
        newWs.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (err) {
                console.error("Failed to parse WebSocket message:", err);
            }
        };
    
        newWs.onerror = (error) => {
            console.error("WebSocket error:", error);
            setIsGenerating(false);
        };
    
        newWs.onclose = () => {
            console.log("WebSocket connection closed.");
            setIsGenerating(false);
        };
    
        if (selectedModel === 'gpt_4o_mini') {
            setWsGPT(newWs);
        } else {
            setWsLLM(newWs);
        }
    };
    
    const handleRunCode = () => {
        if (!generatedCode) {
            alert('No code to run.');
            return;
        }
    
        setIsRunningCode(true);
        setExecutionOutput('');
    
        const socketUrl = `${baseWsUrl}execute_code/`;
        if (wsCode) wsCode.close();
        const newWsCode = new WebSocket(socketUrl);
    
        newWsCode.onopen = () => {
            newWsCode.send(JSON.stringify({ command: "execute" }));
        };
    
        newWsCode.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.status === 'code_output' && data.code_output) {
                    setExecutionOutput(prev => prev + data.code_output + '\n');
                } else if (data.status === 'complete') {
                    setIsRunningCode(false);
                } else if (data.status === 'error' && data.message) {
                    setExecutionOutput(prev => prev + `⚠️ ${data.message}\n`);
                    setIsRunningCode(false);
                }
            } catch (err) {
                console.error('Failed to parse code execution message:', err);
            }
        };
    
        newWsCode.onerror = (error) => {
            console.error('Code execution WebSocket error:', error);
            setIsRunningCode(false);
        };
    
        newWsCode.onclose = () => {
            console.log('Code execution WebSocket closed.');
            setIsRunningCode(false);
        };
    
        setWsCode(newWsCode);
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
        handleRunCode,
        handleMessageChange,
        handleMenuOpen,
        handleMenuClose,
        handleDeleteTab,
        handleRenameTab,
        handleRenameDialogClose,
        handleRenameDialogSave,
        renameDialogOpen,
        menuAnchorEl,
        renameValue,
        setRenameValue,
        selectedModel,
        setSelectedModel,
        generatedCode,
        isRunningCode,
        executionOutput,
    };
};
    
export default useBGPChat;