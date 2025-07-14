import { Box, IconButton, SwipeableDrawer, Typography, Button, TextField } from "@mui/material";
import { ChevronLeft } from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import ConversationList from "../Sidebar/ConversationList";
import { Search } from "@mui/icons-material";
import type { SavedConversation } from "../../types/chat";
import AddCircleIcon from '@mui/icons-material/AddCircle';
import type { SetStateAction } from "react";

interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
  onNewChat: () => void;
  savedConversations: SavedConversation[];
  searchText: string;
  setSearchText: React.Dispatch<React.SetStateAction<string>>;
  filteredConversations: SavedConversation[];
  onLoadConversation: (conversation: SavedConversation) => void;
  onDeleteConversation: (id: string) => void;
  currentConversationId: string | null;
}

const MobileDrawer = ({
  open,
  onClose,
  onNewChat,
  savedConversations,
  searchText,
  setSearchText,
  filteredConversations,
  onLoadConversation,
  onDeleteConversation,
  currentConversationId,
}: MobileDrawerProps) => {
  const theme = useTheme();

  // Wrap the callback function and close the drawer after executing the original operation
  const wrappedOnLoadConversation = (conversation: SavedConversation) => {
    onLoadConversation(conversation);
    onClose();
  };

  const wrappedOnDeleteConversation = (id: string) => {
    onDeleteConversation(id);
    onClose();
  };

  return (
    <SwipeableDrawer
      open={open}
      onClose={onClose}
      onOpen={() => {}}
      sx={{
        "& .MuiDrawer-paper": {
          width: 280,
          boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
          background: theme.palette.background.paper,
        },
      }}>
      <Box sx={{ p: 3, display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: "bold", color: "#13294B"}}>Menu</Typography>
        <IconButton onClick={onClose}><ChevronLeft /></IconButton>
      </Box>
      {/* New Chat button fixed at the top */}
      <Box sx={{ pb: 1, pl:2.5, borderBottom: '0px solid #E5E7EB', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, fontSize: '1.25rem', color: '#1F2937', lineHeight: 1.2,  }}>Chat History</Typography>  
        <Button
            onClick={() => { onNewChat(); onClose(); }} 
            disableRipple
            sx={{
              border: 'none',
              borderRadius: 0,
              boxShadow: 'none',
              padding: 0,
              marginRight:3,
              minWidth: 0,
              backgroundColor: 'transparent',
              '& svg': {
                width: 32,
                height: 32,
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
      </Box>
      <Box sx={{ pt: 4 , pr: 1, pl: 1, borderBottom: '0px solid #eee',ml:1, mr:1.5 }}>
          <TextField
            variant="outlined"
            fullWidth
            size="small"
            placeholder="Search"
            value={searchText}
            onChange={(e: { target: { value: SetStateAction<string>; }; }) => setSearchText(e.target.value)}
            InputProps={{
              startAdornment: <Search sx={{ ml: 1, color: 'rgba(0,0,0,0.4)' }} />,
              style: {
                height: 45, 
                padding: '0 8px',
              },
            }}
            sx={{ backgroundColor: '#fff', 
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
      {/* Scrollable area containing the search bar and conversation list */}
      <Box sx={{ flex: 0.8, overflowY: 'auto', overflowX: 'hidden', p: 1, 
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
          <ConversationList 
            conversations={filteredConversations.length > 0 ? filteredConversations : savedConversations} 
            currentConversationId={currentConversationId} 
            onLoadConversation={wrappedOnLoadConversation} 
            onDeleteConversation={wrappedOnDeleteConversation}
          />
        ) : (
          <Typography variant="body2" color="textSecondary" sx={{ mt: 2, ml: 2 }}>
            {searchText ? "No conversations found." : "No conversation history."}
          </Typography>
        )}
      </Box>
    </SwipeableDrawer>
  );
};

export default MobileDrawer;    