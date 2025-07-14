// components/AiMessage/index.tsx
import { Box, Typography, IconButton } from "@mui/material";
import AIChatIcon from "../../assets/Aichat.png";
import AudioButtonWithPulse from "./AudioButtonWithPulse";
import type { Message, ThemeStyles } from "../../types/chat";
import { ThumbUp, ThumbDown } from '@mui/icons-material';

interface AiMessageProps {
  messages: Message[];
  theme: ThemeStyles;
  showIcon?: boolean;
  onUpdateMessages: (updatedMessages: Message[]) => void;
}

const formatMessageTime = (timestamp: number | string): string => {
  const date = new Date(timestamp);
  
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hou = String(date.getHours()).padStart(2, '0');
  const miu = String(date.getMinutes()).padStart(2, '0');
  return `${day}/${month} ${hou}:${miu}`;
};

const AiMessage = ({ messages, theme, showIcon = true, onUpdateMessages }: AiMessageProps) => {
  // Color function definition
  const getScoreColor = (score: number) => {
    if (score >= 0.9) return 'rgba(22, 163, 74, 0.9)'; 
    if (score >= 0.7) return 'rgba(59, 130, 246, 0.9)'; 
    return ' rgba(239, 68, 68, 0.9)'; 
  };

  // Handle the like operation
  const handleLike = (index: number) => {
    const updatedMessages = [...messages];
    const targetMsg = updatedMessages[index];
    
    // Switch the like status 
    if (targetMsg.liked) {
      targetMsg.likes = (targetMsg.likes || 0) - 1;
    } else {
      targetMsg.likes = (targetMsg.likes || 0) + 1;
      // The tapping status is mutually exclusive
      if (targetMsg.disliked) {
        targetMsg.dislikes = (targetMsg.dislikes || 0) - 1;
        targetMsg.disliked = false;
      }
    }
    targetMsg.liked = !targetMsg.liked;
    onUpdateMessages(updatedMessages);
  };

  // Handle the tap operation
  const handleDislike = (index: number) => {
    const updatedMessages = [...messages];
    const targetMsg = updatedMessages[index];
    
    // Switch the tap status
    if (targetMsg.disliked) {
      targetMsg.dislikes = (targetMsg.dislikes || 0) - 1;
    } else {
      targetMsg.dislikes = (targetMsg.dislikes || 0) + 1;
      // The like status is mutually exclusive
      if (targetMsg.liked) {
        targetMsg.likes = (targetMsg.likes || 0) - 1;
        targetMsg.liked = false;
      }
    }
    targetMsg.disliked = !targetMsg.disliked;
    onUpdateMessages(updatedMessages);
  };

  return (
    <Box display="flex" justifyContent="flex-end" alignItems="flex-end" gap={1}>
      {showIcon && (
        <Box sx={{ 
          width: 36, 
          height: 36, 
          borderRadius: '50%',
          overflow: 'hidden',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)', 
          mb: 5
        }}>
          <img 
            src={AIChatIcon} 
            alt="AI Chat Logo"
            style={{ 
              width: '100%', 
              height: '100%', 
              objectFit: 'cover',
            }}
          />
        </Box>
      )}
      <Box display="flex" flexDirection="column" alignItems="flex-start" width="100%">
        {messages.map((msg, index) => {
          // Extract the match_score from answer (assuming the format is text containing the match_score)
          const matchScore = msg.match_score;
          const percentage = Math.round(Number(matchScore) * 100);
          
          return (
            <Box key={index} width="100%">
            {index === 0 && ( 
              <Typography 
                variant="caption" 
                sx={{ 
                  color: theme.textColor, 
                  opacity: 0.9, 
                  mb: 2, 
                  fontWeight: 500 
                }}
                >
                Assistant • {formatMessageTime(msg.timestamp.toString())}
              </Typography>
            )}
              <Box bgcolor={theme.secondaryBg} px={1} py={1} borderRadius={2} maxWidth="60%" 
                sx={{ 
                  // boxShadow: "0 4px 12px rgba(0,0,0,0.1)", 
                  wordWrap: "break-word", 
                  position: 'relative', 
                  mt: index > 0 ? 2 : 0 
                }}>
              {/* Card header: contains matching degree and message content */}
              <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                <Typography variant="body2" color={theme.textColor} sx={{ mb: 1, whiteSpace: 'pre-wrap' }}>
                  {msg.answer}
                </Typography>
                {/* play button area */}
                <Box sx={{ borderTop: `1px dashed rgba(136, 136, 136, 0.3)`, pt: 1, mt: 1, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 2 }}>
                  {/* Confidence tag */}
                  {msg.confidence && (<Box sx={{ display: "flex", alignItems: "center", gap: 1, backgroundColor: "rgba(0, 128, 0, 0.1)", borderRadius: '8px', padding: '4px 8px', boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)" }}>
                    <Typography variant="caption" sx={{ color: "#13294B", fontWeight: 600, fontSize: "0.75rem" }}>
                      Confidence:
                    </Typography>
                    <Typography variant="caption" sx={{ color: "rgba(0, 128, 0, 0.9)", fontWeight: 600, fontSize: "0.75rem" }}>
                      {msg.confidence}
                    </Typography>
                  </Box>)}
                  {/* Match display (now inside the card) */}
                  {msg.match_score && (<Box sx={{ display: "flex", alignItems: "center", gap: 1, backgroundColor: "rgba(0, 128, 0, 0.1)", borderRadius: '8px', padding: '4px 8px', boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)" }}>
                    <Typography variant="caption" sx={{ color: "#13294B", fontWeight: 600, fontSize: "0.75rem" }}>
                      Match Score:
                    </Typography>
                    <Typography variant="caption" sx={{ color: getScoreColor(Number(matchScore)), fontWeight: 600, fontSize: "0.75rem" }}>
                      {`${percentage}%`}
                    </Typography>
                  </Box>)}
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography variant="caption" sx={{ color: "rgba(136, 136, 136, 0.85)", userSelect: "none", letterSpacing: "0.05em", fontWeight: 500, fontSize: "0.75rem" }}>
                      Click to play voice
                    </Typography>
                    <AudioButtonWithPulse text={msg.answer} color={theme.primaryColor} />
                  </Box>
                </Box>
                
                {/* Picture display */}
                {msg.imageUrls && (
                  <Box mt={2}>
                    <img key={index} src={msg.imageUrls} alt={`image-${index}`} style={{ width: '100%', maxWidth: '500px', height: 'auto', objectFit: 'cover',  borderRadius: '8px', boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',}} />
                  </Box>
                )}
               </Box> 
            </Box>
              {/* likes/dislikes display */}
              {index === messages.length - 1 && (<Box maxWidth="60%" sx={{ display: 'flex',  justifyContent: 'flex-end', alignItems: 'center', mt: 1, flexWrap: 'wrap' }}>
                  <Typography variant="caption" sx={{ color: "#13294B", letterSpacing: "0.05em", fontWeight: 500, fontSize: "0.75rem", mr: 0.5, }}>
                    Was it helpful?
                  </Typography>
                  <IconButton size="small" onClick={() => handleLike(index)} 
                    sx={{ 
                      color: msg.liked ? theme.primaryColor : "rgba(136, 136, 136, 0.8)", 
                      '&:hover': { color: theme.primaryColor } 
                    }}>
                    <ThumbUp fontSize="small" />
                    <Typography variant="caption" sx={{ ml: 0.5, fontSize: '0.75rem' }}>
                      {msg.likes || 0}
                    </Typography>
                  </IconButton>

                  <IconButton size="small" onClick={() => handleDislike(index)} 
                    sx={{ 
                      color: msg.disliked ? "#EF4444" : "rgba(136, 136, 136, 0.8)", 
                      '&:hover': { color: "#EF4444" } 
                    }}>
                    <ThumbDown fontSize="small"/>
                    <Typography variant="caption" sx={{ ml: 0.5, fontSize: '0.75rem' }}>
                      {msg.dislikes || 0}
                    </Typography>
                  </IconButton>
              </Box>)}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};

export default AiMessage;