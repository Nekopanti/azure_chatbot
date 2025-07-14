// components/SnackbarNotification/index.tsx
import { Snackbar, Alert } from "@mui/material";

interface SnackbarNotificationProps {
  open: boolean;
  message: string;
  onClose: () => void;
}

const SnackbarNotification = ({ open, message, onClose }: SnackbarNotificationProps) => {
  return (
    <Snackbar open={open} autoHideDuration={3000} onClose={onClose} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
      <Alert onClose={onClose} severity="success" sx={{ backgroundColor: '#13294B', color: 'white', '& .MuiAlert-icon': { color: 'white' }, borderRadius: 20, boxShadow: '0 4px 12px rgba(0,0,0,0.2)' }}>
        {message}
      </Alert>
    </Snackbar>
  );
};

export default SnackbarNotification;
