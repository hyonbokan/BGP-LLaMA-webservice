import { useState, useRef, useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';
import BGPChatTutorial from '../components/BGPChatTutorial';
import GPTChatTutorial from '../components/GPTChatTutorial';

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
    const [selectedModel, setSelectedModel] = useState('gpt_4o_mini');
    
    const [generatedCode, setGeneratedCode] = useState('');
    const [isRunningCode, setIsRunningCode] = useState(false);
    const [executionOutput, setExecutionOutput] = useState('');

    // Ref to track the index of the ongoing message being generated
    const generatingMessageIndexRef = useRef(null);


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
        if (chatTabs.length === 1) {
            alert("Cannot delete the last remaining tab.");
            return;
        }
    
        const updatedTabs = chatTabs.filter(tab => tab.id !== tabToEdit.id);
        setChatTabs(updatedTabs);
        setMenuAnchorEl(null);
        
        if (tabToEdit.id === chatTabs[currentTab].id) {
            // Set to the first tab or the previous one
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
    
        // Handle 'code_ready' status from the backend
        if (data.status === "code_ready") {
            console.log("Code is ready to be executed.");
            const code = data.code; // Extract code from the event data

            if (code) {
                setGeneratedCode(code); // Set the actual code string
                const codeReadyMessage = {
                    text: '📄 Code is ready to be executed.',
                    sender: "system",
                };
            }
        }
    
        // Handle 'no_code_found' status
        if (data.status === 'no_code_found') {
            console.log("No code block was found in the response.");
            setGeneratedCode(false);
        }

        // Handle 'running_code' status
        if (data.status === "running_code") {
            console.log("\nRunning Code");
            setIsRunningCode(true);

            const runningCodeMessage = {
                text: (
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        Running code 
                        <Box sx={{ width: '8px' }} /> {/* Adding space */}
                        <CircularProgress size={16} sx={{ mr: 1 }} />
                    </Box>
                ),
                sender: "system"
            };

            // Add the new running message and reset generating index
            updateChatTabs(runningCodeMessage);
            generatingMessageIndexRef.current = null;
        }

        // Handle 'code_output' status
        if (data.status === 'code_output' && data.code_output) {
            console.log(`\nReceived code output: ${data.code_output}`);
            setIsRunningCode(false);

            const codeOutputMessage = {
                text: data.code_output.includes("Error") ? `⚠️ ${data.code_output}` : data.code_output,
                sender: "system",
            };

            updateChatTabs(codeOutputMessage);
        }

        // Handle 'keep_alive' status (optional: you can log or ignore)
        if (data.status === 'keep_alive') {
            console.log("Received keep_alive event.");
            return;
        }

        // Handle 'error' status
        if (data.status === 'error' && data.message) {
            console.error('\nError event:', data.message);
            setIsRunningCode(false);
            setIsGenerating(false);
            generatingMessageIndexRef.current = null; // Reset the index after message completion

            const errorMessage = { text: `⚠️ Error: ${data.message}`, sender: "system" };
            updateChatTabs(errorMessage);
        }

        if (data.status === 'complete') {
            console.log('\nCompleted output data event');
            setGeneratedCode(false);
            setIsRunningCode(false);
            setIsGenerating(false);
            generatingMessageIndexRef.current = null;
            setOutputMessage(''); // Clear the output message
        }
    };
    
    const handleEventSourceError = (eventSourceInstance) => {
        console.error('EventSource failed:', eventSourceInstance);
        eventSourceInstance.close();
        setIsGenerating(false);
        setIsRunningCode(false);
        generatingMessageIndexRef.current = null;
    };

    const handleSendMessage = async () => {
        if (currentMessage.trim() === '') return;

        setIsGenerating(true);
        setIsRunningCode(false);

        const userMessage = { text: currentMessage, sender: "user" };
        updateChatTabs(userMessage);

        // Encode the currentMessage before sending
        const encodedMessage = encodeURIComponent(currentMessage);
        setCurrentMessage('');
        setOutputMessage('');

        if (eventSource) {
            eventSource.close();
        }
        generatingMessageIndexRef.current = null;

        const baseUrl = 'https://llama.cnu.ac.kr/api'; // Ensure this is correct
        let endpoint;
        
        // Determine the endpoint based on the selected model
        switch(selectedModel) {
            case 'bgp_llama':
                endpoint = 'bgp_llama';
                break;
            case 'model_3':
                endpoint = 'model_3';
                break;
            default:
                endpoint = 'gpt_4o_mini';
        }

        const url = `${baseUrl}/${endpoint}?query=${encodedMessage}`;
        console.log(`Request URL: ${url}`);
        const newEventSource = new EventSource(url);

        newEventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleEventSourceMessage(data);
            } catch (err) {
                console.error("Failed to parse event data:", err);
            }
        };

        newEventSource.onerror = () => handleEventSourceError(newEventSource);

        setEventSource(newEventSource);
    };

    const handleRunCode = async () => {
        if (!generatedCode) {
            alert('No code to run.');
            return;
        }
    
        setIsRunningCode(true);
        setIsGenerating(false);
        setExecutionOutput('');
    
        const baseUrl = 'https://llama.cnu.ac.kr/api'; // Replace with your actual backend URL
        const endpoint = 'execute_code';
        const url = `${baseUrl}/${endpoint}`;
    
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Include cookies with the request
                body: JSON.stringify({}), // Empty body as code is retrieved from the session
            });
    
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Unknown error during code execution.');
            }
    
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
    
            const stream = new ReadableStream({
                start(controller) {
                    function push() {
                        reader.read().then(({ done, value }) => {
                            if (done) {
                                controller.close();
                                setIsRunningCode(false);
                                return;
                            }
                            const chunk = decoder.decode(value, { stream: true });
                            const lines = chunk.split('\n\n');
                            lines.forEach(line => {
                                if (line.startsWith('data: ')) {
                                    const data = line.replace('data: ', '');
                                    try {
                                        const parsed = JSON.parse(data);
                                        if (parsed.status === 'code_output' && parsed.code_output) {
                                            setExecutionOutput(prev => prev + parsed.code_output + '\n');
                                        } else if (parsed.status === 'complete') {
                                            setIsRunningCode(false);
                                        } else if (parsed.status === 'error' && parsed.message) {
                                            setExecutionOutput(prev => prev + `⚠️ ${parsed.message}\n`);
                                            setIsRunningCode(false);
                                        }
                                    } catch (e) {
                                        console.error('Failed to parse SSE data:', e);
                                    }
                                }
                            });
                            push();
                        }).catch(error => {
                            console.error('Stream reading error:', error);
                            setExecutionOutput(prev => prev + `⚠️ Stream error: ${error.message}\n`);
                            setIsRunningCode(false);
                            controller.error(error);
                        });
                    }
                    push();
                }
            });
    
            await new Response(stream).text(); // Consume the stream
    
        } catch (error) {
            console.error('Error during code execution:', error);
            setExecutionOutput(prev => prev + `⚠️ Error: ${error.message}\n`);
            setIsRunningCode(false);
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
        handleSendMessage,    // For generating code
        handleRunCode,        // For executing code
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
        generatedCode,        // Return generatedCode
        isRunningCode,        // Return isRunningCode
        executionOutput,
    };
};
export default useBGPChat;