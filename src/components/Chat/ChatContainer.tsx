import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, IconButton } from '@mui/material';
import { KeyboardArrowDown } from '@mui/icons-material';
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
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [isUserScrolledUp, setIsUserScrolledUp] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Check if user is scrolled near the bottom
  const isNearBottom = () => {
    if (!chatContainerRef.current) return true;
    
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const threshold = 100; // pixels from bottom
    return scrollHeight - scrollTop - clientHeight < threshold;
  };

  // Handle scroll events to detect if user scrolled up
  const handleScroll = () => {
    const nearBottom = isNearBottom();
    setIsUserScrolledUp(!nearBottom);
  };

  // Smart auto-scroll: only scroll if user is near bottom
  useEffect(() => {
    if (!isUserScrolledUp) {
      scrollToBottom();
    }
  }, [messages, streamingResponse, isUserScrolledUp]);

  // Log session ID whenever it changes
  useEffect(() => {
    console.log('Current Session ID:', sessionId);
  }, [sessionId]);

  // Initialize with "hello" only when component mounts or new chat is started
  useEffect(() => {
    if (!isInitialized) {
      initializeChat();
    }
  }, [isInitialized]); // Only depend on initialization state

  const initializeChat = async () => {
    console.log('=== INITIALIZING CHAT ===');
    console.log('Previous session ID:', sessionId);
    console.log('Initializing chat with:');
    console.log('  - Model:', selectedModel);
    console.log('  - Personality:', selectedPersonality);
    
    // Generate a new session ID for each initialization
    const newSessionId = generateSessionId(userName);
    setSessionId(newSessionId);
    console.log('Generated NEW session ID:', newSessionId);
    console.log('=== CHAT INITIALIZED ===');
    
    setIsInitialized(true);
    
    // Send "Hello" to initialize the model
    await handleSubmit('Hello', true); // true flag indicates this is an initialization
  };

  const handleNewChat = () => {
    console.log('=== NEW CHAT CLICKED ===');
    console.log('Current session ID before new chat:', sessionId);
    setMessages([]);
    setStreamingResponse('');
    setIsLoading(false);
    setPrompt('');
    setIsInitialized(false); // This will trigger re-initialization (which creates new sessionId)
    console.log('New chat initiated - will generate new session ID on initialization');
  };

  const handlePersonalityChange = (newPersonality: string) => {
    if (newPersonality !== selectedPersonality) {
      console.log('=== PERSONALITY CHANGED ===');
      console.log('Personality changed from', selectedPersonality, 'to', newPersonality);
      console.log('Current session ID before personality change:', sessionId);
      setSelectedPersonality(newPersonality);
      
      // Clear chat and re-initialize with new personality and new session ID
      setMessages([]);
      setStreamingResponse('');
      setIsLoading(false);
      setPrompt('');
      setIsInitialized(false); // This will trigger re-initialization with new session ID
      console.log('Personality change will generate new session ID');
    }
  };

  const handleModelChange = (newModel: string) => {
    if (newModel !== selectedModel) {
      console.log('=== MODEL CHANGED ===');
      console.log('Model changed from', selectedModel, 'to', newModel);
      console.log('Current session ID before model change:', sessionId);
      setSelectedModel(newModel);
      
      // Clear chat and re-initialize with new model and new session ID
      setMessages([]);
      setStreamingResponse('');
      setIsLoading(false);
      setPrompt('');
      setIsInitialized(false); // This will trigger re-initialization with new session ID
      console.log('Model change will generate new session ID');
    }
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
      const requestPayload = {
        prompt: message,
        session_id: sessionId,
        model: selectedModel,
        personality: selectedPersonality
      };
      
      console.log('Sending request with payload:', requestPayload);
      
      const response = await makeAuthenticatedRequest(requestPayload);

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
      console.error('Error during streaming:', error);
      
      let errorText = `**Error:** ${error instanceof Error ? error.message : 'Failed to get response from AI'}`;
      
      // Handle rate limiting with user-friendly message
      if (error instanceof Error && (error.message.includes('429') || error.message.includes('Rate Exceeded'))) {
        errorText = '⚠️ **Rate limit exceeded.** Please wait a moment before sending another message. AWS Bedrock has temporary usage limits to ensure fair access.';
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: errorText,
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
          maxWidth: 1100, // Increased width for bigger chat box
          height: '95vh', // Increased height for bigger chat box
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 3,
          overflow: 'hidden',
          background: 'rgba(255, 255, 255, 0.98)',
          backdropFilter: 'blur(20px)',
          position: 'relative', // For absolute positioned scroll button
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
          chatContainerRef={chatContainerRef}
          onScroll={handleScroll}
        />
        
        {/* Scroll to bottom button */}
        {isUserScrolledUp && (
          <Box sx={{ 
            position: 'absolute', 
            bottom: 80, 
            right: 20, 
            zIndex: 1000 
          }}>
            <IconButton
              onClick={scrollToBottom}
              sx={{
                backgroundColor: 'primary.main',
                color: 'white',
                '&:hover': {
                  backgroundColor: 'primary.dark',
                },
                boxShadow: 2,
              }}
              size="small"
            >
              <KeyboardArrowDown />
            </IconButton>
          </Box>
        )}
        
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
