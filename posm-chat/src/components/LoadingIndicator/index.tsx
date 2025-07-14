// components/LoadingIndicator/index.tsx
import { Box, Typography, CircularProgress } from "@mui/material";
import type { ThemeStyles } from "../../types/chat";
import { CheckCircle } from "@mui/icons-material";

interface LoadingIndicatorProps {
  theme: ThemeStyles;
  status: "loading" | "success" | "error" | "empty"; // status attribute
  errorMessage?: string; // error message
}

const LoadingIndicator = ({theme, status}: LoadingIndicatorProps) => {
  // Display different content according to different status
  if (status === "loading") {
    return (
      <Box display="flex" justifyContent="flex-start" mt={3}>
        <Box bgcolor={theme.secondaryBg} px={3} py={2} borderRadius={16} maxWidth="70%" 
             sx={{ boxShadow: "0 4px 12px rgba(0,0,0,0.05)", display: "flex", alignItems: "center", gap: 2 }}>
          <CircularProgress size={20} color="inherit" />
          <Typography variant="body2" color={theme.textColor}>Thinking...</Typography>
        </Box>
      </Box>
    );
  }

  if (status === "empty") {
     return (
      <Box display="flex" justifyContent="flex-start" mt={3}>
        <Box bgcolor={theme.secondaryBg} px={3} py={2} borderRadius={16} maxWidth="70%" 
             sx={{ boxShadow: "0 4px 12px rgba(0,0,0,0.05)", display: "flex", alignItems: "center", gap: 2 }}>
          <CheckCircle color="success" fontSize="small" />
          <Typography variant="body2" color={theme.textColor}>Success!</Typography>
        </Box>
      </Box>
    );
  }

  // Other status (success/error)
  return null;
};

export default LoadingIndicator;