// components/UserMessage/index.tsx
import { Box, Typography } from "@mui/material";
import type { Message, ThemeStyles } from "../../types/chat";

interface UserMessageProps {
  message: Message;
  theme: ThemeStyles;
}

const formatMessageTime = (timestamp: number | string): string => {
  const date = new Date(timestamp);
  
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hou = String(date.getHours()).padStart(2, '0');
  const miu = String(date.getMinutes()).padStart(2, '0');
  return `${day}/${month} ${hou}:${miu}`;
};

const UserMessage = ({ message, theme }: UserMessageProps) => {
  return (
    <Box display="flex" justifyContent="flex-end" mb={1}>
      <Box display="flex" flexDirection="column" alignItems="flex-end">
        <Typography variant="caption" sx={{ color: theme.textColor, opacity: 0.7}}>
          You・{formatMessageTime(message.timestamp.toString())}
        </Typography>
        <Box bgcolor={'#13294B'} color="white" px={1} py={1} maxWidth="90%" sx={{ boxShadow: "0 4px 12px rgba(0,0,0,0.1)", wordWrap: "break-word", transition: 'all 0.3s ease', ':hover': { transform: 'translateY(-2px)' }, position: 'relative', borderRadius: '10px 10px 0 10px', }}>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{message.question}</Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default UserMessage;
