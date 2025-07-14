// components/ChatContainer/index.tsx
import { useState, useEffect, useCallback } from 'react';
import { Box, Typography } from "@mui/material";
import AIChatIcon from "../../assets/Aichat.png";
import type { Message, ThemeStyles } from "../../types/chat";
import MessageList from "../MessageList";
import InputArea from "../InputArea";
import LoadingIndicator from "../LoadingIndicator";
import { useAuth } from 'react-oidc-context';

interface ChatContainerProps {
  chatHistory: Message[];
  onUpdateChatHistory: (updated: Message[]) => void;
  isLoading: boolean;
  onSend: () => void; 
  question: string;
  setQuestion: React.Dispatch<React.SetStateAction<string>>;
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  scrollToBottom: React.RefObject<HTMLDivElement | null>;
  theme: ThemeStyles;
}

const ChatContainer = ({
  chatHistory,
  onUpdateChatHistory,
  isLoading,
  onSend,
  question,
  setQuestion,
  onKeyDown,
  scrollToBottom,
  theme
}: ChatContainerProps) => {
  // Save fixed welcome message time
  const [welcomeTime, setWelcomeTime] = useState<string>('');
  const { user } = useAuth();
  
  useEffect(() => {
    onUpdateChatHistory(chatHistory);
  }, [chatHistory, onUpdateChatHistory]);
  
  // Get the time once when the component is mounted
  useEffect(() => {
    const date = new Date();
  
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hou = String(date.getHours()).padStart(2, '0');
    const miu = String(date.getMinutes()).padStart(2, '0');
    setWelcomeTime(`${day}/${month} ${hou}:${miu}`);
  }, []);

  // Determine current status
  const getStatus = useCallback(() => {
    if (isLoading) return "loading";
    if (chatHistory.length === 0) return "empty";
    return "success";
  }, [isLoading, chatHistory]);

  return (
    <Box flexGrow={1} display="flex" flexDirection="column" sx={{ backgroundColor: theme.bgColor, overflow: 'hidden' }}>
      <Box flexGrow={1} sx={{  p: 3, display: 'flex', flexDirection: 'column', overflowY: "auto",　backgroundColor: '#ffffff',  }}>
        <Box display="flex" justifyContent="flex-end" alignItems="flex-end" gap={1.5}>
          <Box sx={{ 
            width: 36, 
            height: 36, 
            borderRadius: '50%', 
            overflow: 'hidden', 
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            mt: "6px"
          }}>
            <img 
              src={AIChatIcon} 
              alt="AI Chat Logo"
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </Box>
         
          <Box display="flex" flexDirection="column" alignItems="flex-start" width="100%">
            <Typography variant="caption" sx={{ color: theme.textColor, opacity: 0.7, mt: 1}}>
               Assistant • {welcomeTime}
            </Typography>
            <Box sx={{ backgroundColor: theme.secondaryBg, p: 1, borderRadius: 2, }} maxWidth="60%">
              <Typography variant="body2" sx={{ color: theme.textColor, }}>
                Welcome, {user?.profile?.name}! 🎉<br />
                I'm here to help you explore the world of Aperol and all about its delicious cocktails.<br /> 
                If you have questions or need suggestions 🍹, feel free to ask!
              </Typography>
            </Box>
          </Box>
        </Box>
        <MessageList chatHistory={chatHistory} theme={theme} isLoading={isLoading} onUpdateChatHistory={onUpdateChatHistory} />
        {isLoading && <LoadingIndicator theme={theme} status={getStatus()}/>}
        <div ref={scrollToBottom} />
      </Box>
      <InputArea question={question} setQuestion={setQuestion} onSend={onSend} isLoading={isLoading} onKeyDown={onKeyDown} theme={theme} />
    </Box>
  );
};

export default ChatContainer;
