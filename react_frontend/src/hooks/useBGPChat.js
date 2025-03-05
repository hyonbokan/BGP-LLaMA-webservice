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

    const [wsLLM, setWsLLM] = useState(null);
    const [wsCode, setWsCode] = useState(null);
    const generatingMessageIndexRef = useRef(null);
    const baseWsUrl = 'wss://llama.cnu.ac.kr/ws/';


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
            // sender: "system"
            sender: "tutorial"
        };
    
        setChatTabs((prevTabs) => 
            prevTabs.map((tab, index) => {
                if (index === currentTab) {
                    const messages = [...tab.messages];
                    if (messages.length > 0 && messages[0].sender === 'tutorial') {
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
            text: <BGPChatTutorial />,
            sender: "tutorial"
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
        const updatedTabs = chatTabs.map(
            (tab) => tab.id === tabToEdit.id ? { ...tab, label: renameValue } : tab
        );
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
            const code = data.code; // Extract code from the event data

            if (code) {
                setGeneratedCode(code); // Set the actual code string
                const codeReadyMessage = {
                    text: '📄 Code is ready to be executed.',
                    sender: "system",
                };
                updateChatTabs(codeReadyMessage);
            }
        }
    
        // Handle 'no_code_found' status
        if (data.status === 'no_code_found') {
            // console.log("No code block was found in the response.");
            setGeneratedCode(false);
            updateChatTabs({
              text: 'No code block was found in the response.',
              sender: 'system',
            });
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
                text: data.code_output.includes("Error") 
                ? `⚠️ ${data.code_output}` : data.code_output,
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

    const handleSendMessage = () => {
        if (currentMessage.trim() === '') return;

        setIsGenerating(true);
        const userMessage = { text: currentMessage, sender: "user" };
        updateChatTabs(userMessage);

        const messageToSend = currentMessage;
        setCurrentMessage('');
        
        if (wsLLM) wsLLM.close();
        generatingMessageIndexRef.current = null;

        const socketUrl = `${baseWsUrl}llm/`;
        const newWsLLM = new WebSocket(socketUrl);

        newWsLLM.onopen = () => {
            newWsLLM.send(JSON.stringify({ query: messageToSend }));
        };

        newWsLLM.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data);
              if (data.status === 'generating') {
                // Append the new token to a system message that is already in the chat history.
                setChatTabs(prevTabs => {
                  const updatedTabs = [...prevTabs];
                  const currentMessages = [...updatedTabs[currentTab].messages];
                  // If there’s already an ongoing system message, append to it.
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
              } else if (data.status === 'code_ready') {
                // Mark the last system message as final (if you're using that flag)
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
              } else if (data.status === 'no_code_found') {
                // Similar handling here.
              } else if (data.status === 'error') {
                console.error('Error:', data.message);
              }
            } catch (err) {
              console.error("Failed to parse WebSocket message:", err);
            }
          };

        newWsLLM.onerror = (error) => {
            console.error("WebSocket error:", error);
            setIsGenerating(false);
        };

        newWsLLM.onclose = () => {
            console.log("LLM WebSocket connection closed.");
            setIsGenerating(false);
        };

        setWsLLM(newWsLLM);
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