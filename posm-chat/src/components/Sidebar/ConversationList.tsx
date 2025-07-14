// components/Sidebar/ConversationList.tsx
import { List, ListItem, ListItemText, Typography } from "@mui/material";
import type { SavedConversation } from "../../types/chat";
import { useTheme } from "@mui/material/styles";
import { IconButton } from "@mui/material";
import { ExpandLess, ExpandMore } from "@mui/icons-material"
import DeleteOutlineOutlinedIcon from '@mui/icons-material/DeleteOutlineOutlined';
import { alpha } from '@mui/system';
import { useMemo, memo, useCallback, useEffect, useState, useRef } from "react";
import { Box } from '@mui/material';

interface ConversationListProps {
  conversations: SavedConversation[];
  onLoadConversation: (conversation: SavedConversation) => void;
  onDeleteConversation: (id: string) => void;
  currentConversationId: string | null;
}

const formatListItemTime = (timestamp: number | string): string => {
  const date = new Date(timestamp);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${day}/${month}`; 
};

const formatMessageTime = (timestamp: number | string): string => {
  const date = new Date(timestamp);
  const year = String(date.getFullYear());
  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June', 
    'July', 'August', 'September', 'October', 'November', 'December'
  ];
  
  const monthIndex = date.getMonth(); // 0-11
  const monthName = monthNames[monthIndex];
  return `${monthName} ${year}`;
};

// Grouping function: Group by yyyy-mm-dd date
const groupConversationsByDate = (conversations: SavedConversation[]) => {
  return conversations.reduce((groups, convo) => {
    const timestamp =
      typeof convo.timestamp === "string"
        ? new Date(convo.timestamp)
        : convo.timestamp;

    // Generate UTC date key (YYYY-MM-DD format)
    // const dateKey = timestamp.toISOString().split("T")[0];

    // Get the local date part
    const year = timestamp.getFullYear();
    const month = String(timestamp.getMonth() + 1).padStart(2, '0');
    // const day = String(timestamp.getDate()).padStart(2, '0');
    const dateKey = `${year}-${month}`;

    // Group by date
    if (!groups[dateKey]) groups[dateKey] = [];
    groups[dateKey].push(convo);
    
    return groups;
  }, {} as Record<string, SavedConversation[]>);
};

// Used to compare whether two conversation arrays have the same order (based on ID)
const areConversationsSameOrder = (a: SavedConversation[], b: SavedConversation[]) => {
  if (a.length !== b.length) return false;
  return a.every((item, index) => item.id === b[index].id);
};

const ConversationList = memo(({ 
  conversations, onLoadConversation, onDeleteConversation, currentConversationId 
}: ConversationListProps) => {
  const theme = useTheme();
  const prevConversationsRef = useRef<SavedConversation[]>([]);
  
  // Use stable dialogue references and only update when the order actually changes
  const stableConversations = useMemo(() => {
    const prevConversations = prevConversationsRef.current;
    
    // If the order is the same, use the old array reference
    if (areConversationsSameOrder(conversations, prevConversations)) {
      return prevConversations;
    }
    
    // Otherwise use a new array
    prevConversationsRef.current = conversations;
    return conversations;
  }, [conversations]);

  // Keep track of the currently selected conversation ID to avoid reordering
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  // When the external conversation list changes, update the selected state
  useEffect(() => {
    const current = stableConversations.find(c => c.isCurrent);
    if (current) {
      setSelectedId(current.id);
    }
  }, [stableConversations]);

  const toggleGroup = useCallback((dateKey: string) => {
    setCollapsedGroups((prev) => ({
      ...prev,
      [dateKey]: !prev[dateKey],
    }));
  }, []);

  // Optimize click processing function
  const handleLoadConversation = useCallback(
    (conversation: SavedConversation) => {
      // Only update the selected ID, without triggering reordering
      setSelectedId(conversation.id);
      onLoadConversation(conversation);
    },
    [onLoadConversation]
  );

  const handleDeleteConversation = useCallback(
    (id: string) => {
      // Reset selection after deleting a conversation
      if (selectedId === id) {
        setSelectedId(null);
      }
      onDeleteConversation(id);
    },
    [onDeleteConversation, selectedId]
  );

  // Grouping + Date Sort
  const grouped = useMemo(() => groupConversationsByDate(stableConversations),[stableConversations]);
  const sortedDateKeys = useMemo(() => {
    return Object.keys(grouped).sort((a, b) => {
      const [yearA, monthA] = a.split('-').map(Number);
      const [yearB, monthB] = b.split('-').map(Number);
      return (yearB - yearA) || (monthB - monthA);
    });
  }, [grouped]);
  return (
    <List sx={{ p: 0, overflow: 'hidden' }}>
      {stableConversations.length === 0 ? (
        <ListItem>
          <ListItemText primary="No saved conversations" sx={{ color: theme.palette.text.secondary, opacity: 0.7 }}/>
        </ListItem>
      ) : (
        sortedDateKeys.map(dateKey => (
          <div key={dateKey}>

            {/* Group header row */}
            <ListItem sx={{ backgroundColor: '#dfdfdf', py: 0.25, px: 1, borderBottom: `1px solid ${theme.palette.divider}`, 
                display: 'flex', justifyContent: 'space-between', alignItems: 'center', }} >
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontWeight: 600, 
                    color: theme.palette.text.primary,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  {formatMessageTime(dateKey).toString()}
                </Typography>
                <IconButton size="small" onClick={() => toggleGroup(dateKey)}
                  sx={{ color: theme.palette.text.secondary, '&:hover': { color: theme.palette.primary.main } }} >
                  {collapsedGroups[dateKey] ? <ExpandMore /> : <ExpandLess />}
                </IconButton>
              </Box>
            </ListItem>

            {/* dialogue item */}
            {!collapsedGroups[dateKey] && grouped[dateKey]?.map(conversation => {
            {/* { conversationsToShow.map(conversation => { */}
              const isSelected = conversation.id === currentConversationId;
              const formattedItemTime = formatListItemTime(conversation.timestamp.toString());
              return (
                <ListItem 
                  key={conversation.id} 
                  component="div" 
                  sx={{ px: 1.5, py: 0.25, backgroundColor: isSelected ? alpha(theme.palette.primary.main, 0.08) : 'transparent',
                    color: '#13294B',
                    position: 'relative',
                    '&:hover': { 
                        backgroundColor: isSelected 
                        ? alpha(theme.palette.primary.main, 0.15)
                        : theme.palette.action.hover,
                    },
                    cursor: 'pointer',
                    transition: 'all 0.2s ease', // Smooth transition of all attributes
                  }} 
                  onClick={() => handleLoadConversation(conversation)} >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, pr: 4, width: '100%' }}>
                    <ListItemText primary={conversation.title} 
                      primaryTypographyProps={{
                        noWrap: true,
                        variant: 'body2',
                        fontWeight: isSelected ? 500 : 300,
                      }}/>
                  </Box>
                  {isSelected && (
                    <IconButton 
                      aria-label="delete" 
                      size="small" 
                      sx={{ position: 'absolute',  right: 8, top: '50%', transform: 'translateY(-50%)', color: theme.palette.text.disabled, '&:hover': { color: '#13294B', },}}
                      onClick={(e) => {
                        e.stopPropagation(); 
                        handleDeleteConversation(conversation.id);
                      }}>
                      <DeleteOutlineOutlinedIcon fontSize="small" />
                    </IconButton>
                  )}
                  {!isSelected && (
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontWeight: 400, 
                        color: '#b0b0b0',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                  {formattedItemTime}
                </Typography>
                  )}
                </ListItem>
              );
            })}
          </div>
        ))
      )}
    </List>
  );
});

export default ConversationList;