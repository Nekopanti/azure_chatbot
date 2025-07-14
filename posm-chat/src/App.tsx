import { useState, useEffect, useRef } from 'react';
import { Box, ThemeProvider, Typography, createTheme } from '@mui/material';
import { useLocalStorage } from 'usehooks-ts';
import { setupApiInterceptors } from '../src/utils/api';
import { useAuth } from 'react-oidc-context';
import myStoreIcon from "../src/assets/Assess.png";

// Import components
import NavigationBar from './components/NavigationBar';
import Sidebar from './components/Sidebar';
import MobileDrawer from './components/MobileDrawer';
import ChatContainer from './components/ChatContainer';
import SnackbarNotification from './components/SnackbarNotification';

// Import type
import type { Message, SavedConversation, ThemeStyles } from './types/chat';

// Importing API and Hooks
import { sendQuestion, getTitle } from './utils/api';
import { useSaveConversation } from './hooks/useSaveConversation';

// Create topic
export const theme = createTheme({
  palette: {
    primary: {
      main: '#13294B',
    },
    secondary: {
      main: '#FFDC8C', 
    },
    text: {
      primary: '#333333', 
      secondary: '#666666', 
    },
    background: {
      default: '#F5F7FA', 
    },
  },
  typography: {
    fontFamily: 'GTEestiProText', 
  },
});

// Custom theme styles
const themeStyles: ThemeStyles = {
  bgColor: '#F4F5F5',
  cardBg: '#fafafa',
  textColor: '#333333',
  primaryColor: '#13294B',
  secondaryBg: '#f5f5f5',
  sidebarBg: '#f9f9f9',
  sidebarText: '#444444',
  borderColor: '#eeeeee',
  palette: {
    primary: {
      main: '#13294B',
    },
    text: {
      primary: '#333333',
      secondary: '#666666',
    },
    background: {
      default: '#F5F7FA',
      paper: '#FFFFFF',
    },
  },
};

function App() {
  const {user, isAuthenticated, isLoading: isAuthLoading, signinRedirect } = useAuth();

  // Configure the useEffect of the API interceptor (at the top level of all Hooks)
  useEffect(() => {
    setupApiInterceptors(() => user?.access_token ?? null);
  }, [user]);

  // chat status
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [showSidebar, setShowSidebar] = useState(false);
  const [currentTitle, setCurrentTitle] = useState('Untitled Chat');

  // Remember last search keywords（searchText）
  const [searchText, setSearchText] = useLocalStorage<string>('lastSearchText', '');
  // Remember last opened session ID
  // const [currentConversationId, setCurrentConversationId] = useLocalStorage<string | null>('lastConversationId', null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);

  const [filteredConversations, setFilteredConversations] = useState<SavedConversation[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  // Use localStorage to save conversation history
  const [savedConversations, setSavedConversations] = useLocalStorage<SavedConversation[]>(
    'aperolConversations', 
    []
  );

  // The useEffect (top-level) for handling the authentication status
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      signinRedirect();
    }
  }, [isAuthenticated, isAuthLoading, signinRedirect]);

  // Function to scroll to the bottom
  const scrollToBottom = () => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };
  
  // Monitor chat history changes and automatically scroll to the bottom
  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);
  
  // Handle search conversations
  useEffect(() => {
    if (searchText.trim() === '') {
      setFilteredConversations(savedConversations);
      return;
    }
    
    // Conversation title contains search text
    const filtered = savedConversations.filter(conversation => 
      // The conversation title contains the search text (ignore case)
      conversation.title.toLowerCase().includes(searchText.toLowerCase()) 
      // ||
      // // Any message (question or answer) in the conversation contains the search text
      // conversation.messages.some(msg => 
      //   msg.question.toLowerCase().includes(searchText.toLowerCase()) ||
      //   msg.answer.toLowerCase().includes(searchText.toLowerCase())
      // )
    );
    
    setFilteredConversations(filtered);
  }, [searchText, savedConversations]);
  
  // Function to automatically generate conversation title
  const generateAutoTitle = async (messages: Message[], timestamp: Date) => {
    if (messages.length === 0) return 'Untitled Chat';
    
    // Try generating the headers from the first message
    const firstMessage = messages[0];
    if (firstMessage.question) {
      try {
        // Call API to get the answer
        const response = await getTitle(firstMessage.question);
        return response.title;
      } catch (error) {
        console.error('Failed to generate title:', error);
        // Returns the default title on error
        return `Chat on ${new Date(timestamp).toLocaleTimeString()}`;
      }
    }
    
    // default title
    return `Chat on ${new Date(timestamp).toLocaleTimeString()}`;
  };
  
  // Send message processing
  const handleSendMessage = async () => {
    if (!question.trim() || isLoading) return;
    
    const newQuestion = question.trim();
    setIsLoading(true);
    
    // create new message
    const userMessage: Message = {
      question: newQuestion,
      answer: '',
      imageUrls: '',
      timestamp: new Date(),
      id: Date.now().toString(),
      role: 'user',
      match_score:'',
      confidence:''
    };
    
    // Add question to chat history
    setChatHistory(prev => [...prev, userMessage]);
    setQuestion('');
    
    try {
      // Call API to get the answer
      const response = await sendQuestion(newQuestion);
       
      // Processing API responses - ensuring all messages are formatted consistently
      let aiMessages: Message[] = [];

      // Handling API responses
      if (Array.isArray(response)) {
        // If the API returns multiple messages
        aiMessages = response.map((item, index) => ({
          ...userMessage, // Inherit basic properties
          id: `${userMessage.id}-ai-${index}`, 
          question: '', 
          answer: item.text_content || '',
          imageUrls: item.image_sas_url || '', 
          timestamp: new Date(),
          role: 'assistant',
          match_score:item.match_score,
          confidence:item.confidence
        }));
      } else {
        // If the API returns a single message
        aiMessages = [{
          ...userMessage,
          id: `${userMessage.id}-ai`,
          question: '',
          answer:  'I\'m sorry, I don\'t have an answer for that.',
          imageUrls:  '', 
          timestamp: new Date(),
          role: 'assistant',
          match_score:'',
          confidence:''
        }];
      }
      
      // Append AI answers to chat history
      setChatHistory(prev => [...prev, ...aiMessages]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      setSnackbarMessage('Failed to send message. Please try again.');
      setSnackbarOpen(true);
    } finally {
      setIsLoading(false);
    }
  };
  // Automatically restore the last conversation based on lastConversationId at startup
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current) return;

    if (currentConversationId && savedConversations.length > 0) {
      const conversation = savedConversations.find(c => c.id === currentConversationId);
      if (conversation) {
        setChatHistory(conversation.messages);

        setSavedConversations(prev =>
          prev.map(convo => ({
            ...convo,
            isCurrent: convo.id === conversation.id,
          }))
        );

        initializedRef.current = true;
      }
    }
  }, [currentConversationId, savedConversations]);

  // Handle keyboard events
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Sidebar width state (uses localStorage to remember user preference)
  const [sidebarWidth, setSidebarWidth] = useLocalStorage<number>('sidebarWidth', 280);
  // drag state
  const [isDragging, setIsDragging] = useState(false);
  
  // Separator reference
  const resizerRef = useRef<HTMLDivElement>(null);
  
  // Handling mouse press events
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    // Prevent events from bubbling up to parent elements
    e.stopPropagation();
    // Prevent text selection
    e.preventDefault();
    
    setIsDragging(true);
    
    // Add drag style class
    if (resizerRef.current) {
      resizerRef.current.classList.add('active-resizer');
    }
  };
  
  // Handling mouse movement events
  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return;
    
    // Calculate new sidebar width
    const container = document.querySelector('.app-container') as HTMLElement;
    if (!container) return;
    
    // Get the left edge position of the container
    const containerRect = container.getBoundingClientRect();
    const containerLeft = containerRect.left;
    
    // Calculates the mouse position relative to the left edge of the container
    const relativeX = e.clientX - containerLeft;
    
    // Set the new sidebar width
    setSidebarWidth(relativeX);
  };
  
  // Handling mouse release events
  const handleMouseUp = () => {
    setIsDragging(false);
    
    // Remove the dragging style class
    if (resizerRef.current) {
      resizerRef.current.classList.remove('active-resizer');
    }
  };
  
  // Listen to window events to ensure that dragging is effective anywhere in the window
  useEffect(() => {
    // Add global event listener only when dragging
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      // Prevent text selection during dragging
      document.body.style.userSelect = 'none';
    }
    
    // Cleanup function
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Calculate the title of the current conversation
  const title = currentConversationId 
  ? savedConversations.find(convo => convo.id === currentConversationId)?.title || 'Untitled'
  : 'Untitled';

  // Save current conversation
  const saveCurrentConversation = useSaveConversation({
    chatHistory,
    currentConversationId,
    savedConversations,
    setSavedConversations,
    setCurrentConversationId,
    showSnackbar: (message) => {
      setSnackbarMessage(message);
      setSnackbarOpen(true);
    },
    currentTitle:title
  });

  // Calculate the title of the current conversation
  useEffect(() => {
    const generateTitle = async () => {
      const title = await generateAutoTitle(chatHistory, new Date());
      setCurrentTitle(title);
    };

    generateTitle();
  }, [chatHistory]);

  // Save current conversation
  const saveNewCurrentConversation = useSaveConversation({
    chatHistory,
    currentConversationId,
    savedConversations,
    setSavedConversations,
    setCurrentConversationId,
    showSnackbar: (message) => {
      setSnackbarMessage(message);
      setSnackbarOpen(true);
    },
    currentTitle:currentTitle
  });
  
  // Save first then switch
  const handleClickConversation = (conversation: SavedConversation) => {
    if (chatHistory.length > 0 && chatHistory.length > length && currentConversationId !== conversation.id) {
      const currentLen =  savedConversations.find(convo => convo.id === currentConversationId)?.messages.length || 0;
      if (chatHistory.length > currentLen) {
        // Switching between historical records
        if(currentConversationId != null){
          saveCurrentConversation(); // save
        }
        // New Chat Switch History
        else {
          saveNewCurrentConversation(); // save
        }
      }
    }
    initializedRef.current = false;

    handleLoadConversation(conversation); // switch
  };

  // Load historical conversations
  const handleLoadConversation = (conversation: SavedConversation) => {
    setCurrentConversationId(conversation.id);
    // If the current session is not the one to be loaded, save and switch are processed
    if (conversation.id !== currentConversationId) {
      // Switch to target conversation
      setChatHistory(conversation.messages);
      setCurrentConversationId(conversation.id);
      setSavedConversations(prev =>
        prev.map(convo => ({
          ...convo,
          isCurrent: convo.id === conversation.id
        }))
      );

      if (window.innerWidth < 900) {
        setShowSidebar(false);
      }
    }
  };

  const handleDeleteConversation = (id: string) => {
    // Delete conversation
    setSavedConversations(prev => prev.filter(convo => convo.id !== id));
    
    // If the current conversation is deleted, clear the current conversation
    if (id === currentConversationId) {
      setChatHistory([]); // Clear chat history
      setCurrentConversationId(null); // Clear the current conversation ID
    }
  };

  // Start a new chat
  const handleNewChat = async () => {
    setCurrentConversationId(null);
    // Clear isCurrent of all historical sessions
    setSavedConversations(prev =>
      prev.map(convo => ({ ...convo, isCurrent: false }))
    );

    if (chatHistory.length > 0) {
      if (currentConversationId) {
        // The current conversation is a historical conversation. Update the original conversation content
        const now = new Date();
        // Get the title first, then update the conversation
        // const title = await generateAutoTitle(chatHistory, now);
        setSavedConversations(prev =>
          prev.map(convo =>
            convo.id === currentConversationId
              ? { ...convo, messages: chatHistory, timestamp: now, lastSaved: now, title: convo.title }
              : convo
          )
        );
      } else {
        // The current session is NewChat. Create a new session.
        const now = new Date();
        const newId = Date.now().toString();

        // Get the title first, then create the conversation
        const title = await generateAutoTitle(chatHistory, now);
        setSavedConversations(prev => [
          // Add a new conversation first
          {
            id: newId,
            title: title,
            messages: chatHistory,
            timestamp: now,
            lastSaved: now, // Last saved time
            isCurrent: false,
          },
          // Keep the original conversation (excluding possible identical IDs)
          ...prev.filter(convo => convo.id !== newId)
        ]);
        
        // Sort new chats by timestamp in descending order (latest first)
        sortConversationsByTimestamp();
      }
    } else {
      // No content, only clear isCurrent status
      setSavedConversations(prev =>
        prev.map(convo => ({ ...convo, isCurrent: false }))
      );
    }

    // Clear the current conversation status
    setChatHistory([]);
    setCurrentConversationId(null);

    // (document.activeElement as HTMLElement)?.blur();
    // Safely removing focus
    const activeElement = document.activeElement;
    if (activeElement instanceof HTMLElement) {
      activeElement.blur();
    }
  };

  // Sort conversations by timestamp in descending order (newest first)
  const sortConversationsByTimestamp = () => {
    setSavedConversations(prev => 
      prev.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    );
  };

  // Show notification message
  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

   // Save state to local storage (when browser is closed/refreshed)
  const saveStateBeforeUnload = () => {
    localStorage.setItem('currentChatHistory', JSON.stringify(chatHistory));
    localStorage.setItem('currentConversationId', currentConversationId || 'null');
    
    if (chatHistory.length > 0 && !currentConversationId) {
      handleNewChat();
    }
  };
  
  // Manage event listeners when components are mounted/unmounted
  useEffect(() => {
    window.addEventListener('beforeunload', saveStateBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', saveStateBeforeUnload);
    };
  }, [chatHistory, currentConversationId, handleNewChat]);
  
  // Restore history state on startup
  useEffect(() => {
    const savedHistory = localStorage.getItem('currentChatHistory');
    const savedConversationId = localStorage.getItem('currentConversationId');
    
    if (savedHistory) {
      setChatHistory(JSON.parse(savedHistory));
    }
    
    if (savedConversationId && savedConversationId !== 'null') {
      setCurrentConversationId(savedConversationId);
    }
  }, []);

  // Display status during loading
  if (isAuthLoading) {
    return (
      <Box 
        sx={{minHeight: '100vh', width: '100vw', backgroundColor: themeStyles.bgColor, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 3, padding: 2,}}>
        {/* Logo */}
        <Box sx={{ mb: 4 }}>
          <img src={myStoreIcon} alt="Campari Logo" 
            style={{ 
              height: '60px', 
              opacity: 0.9,
              animation: 'pulse 2s infinite ease-in-out'
            }} />
        </Box>

        <Box sx={{
            width: '50px',
            height: '50px',
            border: '4px solid',
            borderColor: `${theme.palette.secondary.main}40`, 
            borderTopColor: theme.palette.secondary.main, 
            borderRadius: '50%',
            animation: 'spin 1.2s infinite linear',
          }}/>

        {/* Load text */}
        <Typography 
          variant="h6" 
          sx={{
            color: themeStyles.textColor,
            fontWeight: 500,
            letterSpacing: 0.5,
            textAlign: 'center',
          }}>
          Authenticating your account
        </Typography>

        {/* Status prompt */}
        <Typography 
          variant="body2" 
          sx={{
            color: themeStyles.textColor + '80',
            maxWidth: '300px',
            textAlign: 'center',
            mt: 1,
            animation: 'fade 3s infinite alternate',
          }} >
          Please wait while we verify your credentials...
        </Typography>
      </Box>
    );
  }
  return (
    <ThemeProvider theme={theme}>
      <Box className="app-container" height="97.5vh" width="98vw" sx={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Navigation bar */}
        <NavigationBar  onMenuClick={() => setShowSidebar(true)}  title="CAMPARI GROUP" />
        
        {/* Main content area */}
        <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
            {/* Sidebar - fixed width or adjustable based on state */}
          <Box sx={{ width: { xs: showSidebar ? '100%' : 0, md: `${sidebarWidth}px` }, flexShrink: 0,  overflow: 'hidden', display: 'flex',  backgroundColor: '#F4F5F5', }} >
            {/* sidebar */}
            <Sidebar 
              onNewChat={handleNewChat}
              savedConversations={savedConversations}
              searchText={searchText}
              setSearchText={setSearchText}
              filteredConversations={filteredConversations}
              onLoadConversation={handleClickConversation}
              onDeleteConversation={handleDeleteConversation}
              currentConversationId={currentConversationId}
            />
          </Box>

          {/* Divider - Draggable */}
          <Box ref={resizerRef}
            sx={{borderStyle: 'groove', borderWidth: '0 1px', 
                borderColor: 'theme.palette.grey[300]', cursor: isDragging ? 'move' : 'col-resize', display: { xs: 'none', md: 'block' }, transition: 'all 0.2s ease', 
              // Style when dragging
              '&.active-resizer': {
                borderColor: theme.palette.grey[300],
                opacity: 0.8,
                boxShadow: '0 0 8px rgba(255, 101, 0, 0.5)',
              }
            }}
            onMouseDown={handleMouseDown}
          />
          
          {/* Chat container - adaptive remaining width */}
          <Box sx={{flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }} >
            <ChatContainer 
              chatHistory={chatHistory}
              onUpdateChatHistory={(updated) => setChatHistory(updated)}
              isLoading={isLoading}
              onSend={handleSendMessage}
              question={question}
              setQuestion={setQuestion}
              onKeyDown={handleKeyDown}
              scrollToBottom={chatEndRef}
              theme={themeStyles}
            />
          </Box>
        </Box>
        
        {/* Mobile sidebar */}
        <MobileDrawer 
          open={showSidebar}
          onClose={() => setShowSidebar(false)}
          onNewChat={handleNewChat}
          savedConversations={savedConversations}
          searchText={searchText}
          setSearchText={setSearchText}
          filteredConversations={filteredConversations}
          currentConversationId={currentConversationId}
          onLoadConversation={handleClickConversation}
          onDeleteConversation={handleDeleteConversation}
        />

        {/* Notification tips */}
        <SnackbarNotification 
          open={snackbarOpen} 
          message={snackbarMessage} 
          onClose={handleCloseSnackbar} 
        />
      </Box>
    </ThemeProvider>
  );
}

export default App;