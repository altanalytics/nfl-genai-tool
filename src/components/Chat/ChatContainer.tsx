import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper } from '@mui/material';
import ChatHeader from './ChatHeader';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { Message } from '../../types/message';
import { generateSessionId } from '../../utils/sessionUtils';
import { makeAuthenticatedRequest } from '../../utils/apiUtils';
import { DEFAULT_MODEL, DEFAULT_PERSONALITY } from '../../config/agentConfig';

interface ChatContainerProps {
  userName: string;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ userName }) => {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingResponse, setStreamingResponse] = useState('');
  const [sessionId, setSessionId] = useState(() => generateSessionId(userName));
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL);
  const [selectedPersonality, setSelectedPersonality] = useState(DEFAULT_PERSONALITY);
  const [isInitialized, setIsInitialized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingResponse]);

  // Log session ID whenever it changes
  useEffect(() => {
    console.log('Current Session ID:', sessionId);
  }, [sessionId]);

  // Initialize with "hello" when component mounts or personality changes
  useEffect(() => {
    if (!isInitialized) {
      initializeChat();
    }
  }, [selectedPersonality]); // Re-run when personality changes

  const initializeChat = async () => {
    console.log('Initializing chat with personality:', selectedPersonality);
    
    // Generate a new session ID for each initialization
    const newSessionId = generateSessionId(userName);
    setSessionId(newSessionId);
    console.log('New session ID for initialization:', newSessionId);
    
    setIsInitialized(true);
    
    // Send "Hello" to initialize the model
    await handleSubmit('Hello', true); // true flag indicates this is an initialization
  };

  const handleNewChat = () => {
    setMessages([]);
    setStreamingResponse('');
    setIsLoading(false);
    setPrompt('');
    setIsInitialized(false); // This will trigger re-initialization (which creates new sessionId)
    console.log('New chat initiated - will generate new session ID on initialization');
  };

  const handlePersonalityChange = (newPersonality: string) => {
    if (newPersonality !== selectedPersonality) {
      console.log('Personality changed from', selectedPersonality, 'to', newPersonality);
      setSelectedPersonality(newPersonality);
      
      // Clear chat and re-initialize with new personality
      setMessages([]);
      setStreamingResponse('');
      setIsLoading(false);
      setPrompt('');
      setIsInitialized(false); // This will trigger re-initialization with new personality
    }
  };

  const handleModelChange = (newModel: string) => {
    console.log('Model changed from', selectedModel, 'to', newModel);
    setSelectedModel(newModel);
    // Note: Model change does NOT clear the chat or re-initialize
  };

  const parseSSEChunk = (chunk: string): string => {
    const lines = chunk.split('\n');
    let extractedText = '';
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const jsonStr = line.slice(6); // Remove 'data: ' prefix
          const data = JSON.parse(jsonStr);
          
          if (data.type === 'token' && data.text) {
            extractedText += data.text;
          }
        } catch (e) {
          // Skip invalid JSON lines
          console.warn('Failed to parse SSE line:', line);
        }
      }
    }
    
    return extractedText;
  };

  const handleSubmit = async (message: string, isInitialization: boolean = false) => {
    if (!message.trim() || isLoading) return;
    
    // Only add user message to UI if it's not an initialization
    if (!isInitialization) {
      const userMessage: Message = {
        id: Date.now().toString(),
        text: message,
        isUser: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
    }

    setPrompt('');
    setIsLoading(true);
    setStreamingResponse('');
    
    try {
      const response = await makeAuthenticatedRequest({
        prompt: message,
        session_id: sessionId,
        model: selectedModel,
        personality: selectedPersonality
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          console.log('Received chunk:', chunk); // Debug log
          
          // Parse the SSE format and extract text tokens
          const extractedText = parseSSEChunk(chunk);
          
          if (extractedText) {
            fullResponse += extractedText;
            setStreamingResponse(fullResponse);
            console.log('Updated streaming response:', fullResponse); // Debug log
          }
        }

        // Add the complete response as a message (always add AI responses)
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: fullResponse,
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
        setStreamingResponse('');
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `**Error:** ${error instanceof Error ? error.message : 'Failed to get response from AI'}`,
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ 
      height: '100%', 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center',
      p: 2 
    }}>
      <Paper 
        elevation={3}
        sx={{ 
          width: '100%',
          maxWidth: 900, // Increased width to accommodate settings
          height: '90vh',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 3,
          overflow: 'hidden',
          background: 'rgba(255, 255, 255, 0.98)',
          backdropFilter: 'blur(20px)',
        }}
      >
        <ChatHeader 
          onNewChat={handleNewChat} 
          isLoading={isLoading}
          selectedModel={selectedModel}
          selectedPersonality={selectedPersonality}
          onModelChange={handleModelChange}
          onPersonalityChange={handlePersonalityChange}
        />
        
        <MessageList 
          messages={messages}
          streamingResponse={streamingResponse}
          isLoading={isLoading}
          messagesEndRef={messagesEndRef}
        />
        <MessageInput
          prompt={prompt}
          setPrompt={setPrompt}
          onSubmit={(message) => handleSubmit(message, false)}
          isLoading={isLoading}
        />
      </Paper>
    </Box>
  );
};

export default ChatContainer;
