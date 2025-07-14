// components/Sidebar/index.tsx
import { useState, useRef, useEffect } from 'react'; 
import { Box, Typography, TextField, Tooltip  } from "@mui/material";
import { Search } from "@mui/icons-material";
import type { SavedConversation } from "../../types/chat";
import ConversationList from "./ConversationList";
import { Button } from "@mui/material";
import AddCircleIcon from '@mui/icons-material/AddCircle';

interface SidebarProps {
  onNewChat: () => void;
  savedConversations: SavedConversation[];
  searchText: string;
  setSearchText: React.Dispatch<React.SetStateAction<string>>;
  filteredConversations: SavedConversation[];
  onLoadConversation: (conversation: SavedConversation) => void;
  onDeleteConversation: (id: string) => void;
  currentConversationId: string | null;
}

const Sidebar = ({
  onNewChat,
  savedConversations,
  searchText,
  setSearchText,
  filteredConversations,
  onLoadConversation,
  onDeleteConversation,
  currentConversationId
}: SidebarProps) => {
  const sidebarRef = useRef<HTMLDivElement>(null);
  const [sidebarWidth, setSidebarWidth] = useState<number>(0);
  
  // Listen for changes in the sidebar width
  useEffect(() => {
    const handleResize = () => {
      if (sidebarRef.current) {
        setSidebarWidth(sidebarRef.current.offsetWidth);
      }
    };

    // Initialization width
    handleResize();
    
    // Listen for changes in window size (dealing with width changes caused by sidebar dragging)
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  return (
    <Box sx={{ width: '100%', flexShrink: 0, display: 'flex', boxShadow: '0 0 10px rgba(0,0,0,0.1)', position: 'sticky', flexDirection: 'column', height: '100vh',}}>
      {/* Fixed top area: New Chat button and separator line */}
      <Box sx={{ pt:2.5, pb: 3, pl:2.5, borderBottom: '0px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, fontSize: '1rem', color: '#1F2937', lineHeight: 1.5,  }}>Chat History</Typography>

        <Tooltip title="New Chat"  placement="bottom" arrow >
          <Button
              onClick={onNewChat}
              disableRipple
              sx={{
                border: 'none',
                borderRadius: 0,
                boxShadow: 'none',
                padding: 0,
                marginRight:2.5,
                minWidth: 0,
                backgroundColor: 'transparent',
                '& svg': {
                  width: 30,
                  height: 30,
                  color: '#1E3A5F',
                  transition: 'all 0.2s ease',
                  
                  '&:hover': {
                    color: '#13233A', 
                    transform: 'scale(1.08)',
                    filter: 'drop-shadow(0 1px 3px rgba(0,0,0,0.15))',
                  },
                  
                  '&:active': {
                    transform: 'scale(0.96)',
                  }
                },
                
                '&:hover': {
                  backgroundColor: 'transparent',
                },
                '&:focus': {
                  outline: 'none',
                },
                '&.Mui-focusVisible': {
                  outline: '2px solid rgba(30, 58, 95, 0.5)',
                  outlineOffset: 1,
                },
              }}
            >
            <AddCircleIcon fontSize="inherit" />
          </Button>
        </Tooltip>
      </Box>
      <Box sx={{ p: 1, pt: 3, borderBottom: '0px solid #eee', ml:1.5, mr:1 }}>
        <TextField
          variant="outlined"
          size="small"
          placeholder="Search"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          InputProps={{
            startAdornment: <Search sx={{ color: 'rgba(0,0,0,0.4)' }} />,
             style: {
              height: 45, 
              padding: '0 8px',
            },
          }}
          sx={{ backgroundColor: '#fff', 
            width: '100%',
            maxWidth: sidebarWidth > 0 ? `calc(${sidebarWidth}px - 16px)` : '100%',
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderWidth: '1px !important',
              },
              '&:hover fieldset': {
                borderColor: 'rgba(0,0,0,0.23)',
                borderWidth: '1px !important',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#1E3A5F',
                borderWidth: '0.8px !important', 
              },
            },
          }}
        />
      </Box>

      {/* Scrollable areas: History title, search bar, and conversation list */}
      <Box sx={{flex: 0.8, overflowY: 'auto', overflowX: 'hidden', p: 1,  
       // Custom scroll bar style
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: 'rgba(0,0,0,0.05)',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(0,0,0,0.1)',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            backgroundColor: 'rgba(0,0,0,0.2)',
          },
        }}>
        {filteredConversations.length > 0  ? (          
          <ConversationList conversations={filteredConversations.length > 0 ? filteredConversations : savedConversations} currentConversationId={currentConversationId} onLoadConversation={onLoadConversation} onDeleteConversation={onDeleteConversation}/>
        ) : (
          <Typography variant="body2" color="textSecondary" sx={{ mt: 2, pl:2 }}>
            {searchText ? "No conversations found." : "No conversation history."}
          </Typography>
        )}
    </Box>

  </Box>
  );
};

export default Sidebar;
