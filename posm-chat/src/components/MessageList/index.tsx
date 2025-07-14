// components/MessageList/index.tsx
import { Box, Typography } from "@mui/material";
import UserMessage from "../UserMessage";
import AiMessage from "../AiMessage/index";
import type { Message, ThemeStyles } from "../../types/chat";

interface MessageListProps {
  chatHistory: Message[];
  theme: ThemeStyles;
  isLoading: boolean;
  onUpdateChatHistory: (updatedHistory: Message[]) => void; 
}

const MessageList = ({ chatHistory, theme, isLoading, onUpdateChatHistory }: MessageListProps) => {
  // If there is no message, show empty state
  if (chatHistory.length === 0) {
    return (
      <Box mt={8} textAlign="center" p={4}>
        <Typography variant="body1" color={theme.textColor} sx={{ opacity: 0.7 }}>
          Start a conversation by typing a message below.
        </Typography>
      </Box>
    );
  }
    // chat AI
  const handleUpdateMessages = (updatedAiMessages: Message[]) => {
    const updatedHistory = chatHistory.map(oldMsg => {
      const updatedMsg = updatedAiMessages.find(msg => msg.id === oldMsg.id);
      return updatedMsg || oldMsg;
    });

    onUpdateChatHistory(updatedHistory);
  };

  // Group user messages and corresponding AI replies in order
  const messageGroups: { userMsg: Message; aiReplies: Message[] }[] = [];
  let currentUserMsg: Message | null = null;
  let aiReplies: Message[] = [];

  // Iterate through all messages and group them
  chatHistory.forEach((msg) => {
    if (msg.role === 'user') {
      // When encountering a new user message, save the previous grouping (if any)
      if (currentUserMsg) {
        messageGroups.push({
          userMsg: currentUserMsg,
          aiReplies: aiReplies
        });
      }
      
      // Start a new user message group
      currentUserMsg = msg;
      aiReplies = [];
    } else if (msg.role === 'assistant' && currentUserMsg) {
      // Add AI reply to the reply list of the current user's message
      aiReplies.push(msg);
    }
  });

  // Add last group
  if (currentUserMsg) {
    messageGroups.push({
      userMsg: currentUserMsg,
      aiReplies: aiReplies
    });
  }

  return (
    <Box>
      {messageGroups.map(group => (
        <Box key={group.userMsg.id} mb={6} sx={{ display: 'flex', flexDirection: 'column' }}>
          {/* Render user messages */}
          <UserMessage message={group.userMsg} theme={theme} />
          
          {/* Rendering corresponding multiple AI answers */}
          {group.aiReplies.length > 0 ? (
            <AiMessage messages={group.aiReplies} theme={theme} showIcon={true} onUpdateMessages={handleUpdateMessages}/>
          ) : isLoading ? (
            // If loading, don't show empty state
            null
          ) : (
            // No AI response and not loading
            <Box sx={{ mt: 2, padding: 2, border: '1px dashed #eee', borderRadius: 8 }}>
              <Typography variant="body2" color="text.secondary">
                No responses yet
              </Typography>
            </Box>
          )}
        </Box>
      ))}
    </Box>
  );
};

export default MessageList;