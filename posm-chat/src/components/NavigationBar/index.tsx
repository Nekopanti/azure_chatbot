// components/NavigationBar/index.tsx
import { useAuth } from 'react-oidc-context';
import { AppBar, Toolbar, IconButton, Button, Avatar, Tooltip, Box } from "@mui/material";
import { Menu } from "@mui/icons-material";
import LogoutIcon from '@mui/icons-material/Logout';
import myStoreIcon from "../../assets/MyStore_Header.png";

interface NavigationBarProps {
  onMenuClick: () => void;
  title?: string;
}

declare global {
  interface Window {
    VITE_REDIRECT_URI: string;
  }
}

const NavigationBar = ({ onMenuClick }: NavigationBarProps) => {
  // const theme = useTheme();
  const { signoutRedirect, user } = useAuth();

  // Handle the logout logic
  const handleLogout = () => {
    // Build the logout configuration (if a custom return URL is required)
    const logoutConfig = {
      post_logout_redirect_uri: window.VITE_REDIRECT_URI || window.location.origin,
    };
    
    // Call the signoutRedirect method
    signoutRedirect(logoutConfig);
  };

  // The abbreviation of the name is used as the profile picture
  const getInitials = () => {
    if (!user?.profile?.name) return '?';
    const nameParts = user.profile.name.split(' ');
    return nameParts.length > 1 
      ? nameParts[0][0] + nameParts[1][0] 
      : nameParts[0][0];
  };

  return (
    <AppBar position="sticky"  elevation={2} sx={{ background: '#13294B', zIndex: 100 ,  borderBottom: '1px solid rgba(255, 255, 255, 0.1)', height: '64px', transition: 'background-color 0.3s ease', overflow: 'hidden'}}>
      <Toolbar sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',  height: '64px', margin: '0 auto', width: '100%'}}>
        {/* <Typography variant="h5" sx={{ color: '#fff', fontWeight: 'bold' }}>{title || "Campari Virtual Assistant"}</Typography> */}
        <img  src={myStoreIcon}  alt="My Store Logo"  style={{ height: '55px', transition: 'transform 0.3s ease' }} />
        <IconButton color="inherit" onClick={onMenuClick} sx={{ display: { md: 'none', xs: 'block' } }}><Menu /></IconButton>

         {/* Logout */}
        {user?.profile?.name && (
          <Box display="flex" alignItems="center" >
            <Tooltip title={user.profile.name}>
              <Avatar sx={{ bgcolor: '#fff', color: '#13294B',  fontWeight: 'bold', transition: 'all 0.2s ease'}}>
                {getInitials()}
              </Avatar>
            </Tooltip>
            
            <Button color="inherit"  startIcon={<LogoutIcon />} onClick={handleLogout} sx={{ textTransform: 'none', fontWeight: 500, fontSize: '0.9rem', 
              borderRadius: '8px', transition: 'all 0.2s ease',}} />
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default NavigationBar;
