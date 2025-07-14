import { Box, TextField, Button, InputAdornment } from "@mui/material";
import { Send, Clear } from "@mui/icons-material";
import { CircularProgress } from "@mui/material";
import type { ThemeStyles } from "../../types/chat";

interface InputAreaProps {
  question: string;
  setQuestion: React.Dispatch<React.SetStateAction<string>>;
  onSend: () => void;
  isLoading: boolean;
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  theme: ThemeStyles;
}

const InputArea = ({ question, setQuestion, onSend, isLoading, onKeyDown }: InputAreaProps) => {
  const clearInput = () => {
    setQuestion('');
  };

  return (
    <Box sx={{ display: "flex", justifyContent: "start-left", width: "100%", p: 1.5}}>
      <Box sx={{ p: 1.5, display: 'flex', alignItems: 'center', gap: 1.5, maxWidth: "95%", width: "100%"}}>
        <TextField 
          fullWidth 
          placeholder="Write your message..." 
          value={question} 
          onChange={(e) => setQuestion(e.target.value)} 
          onKeyDown={onKeyDown} 
          variant="outlined"
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                {question.trim().length > 0 && !isLoading ? (
                  <Button
                    onClick={clearInput}
                    sx={{
                      p: 0.5,
                      borderRadius: '50%',
                      '&:hover': { backgroundColor: '#fff' },
                      minWidth: 0,
                    }}
                  >
                    <Clear fontSize="small" sx={{ color: 'rgba(136, 136, 136, 0.85)' }} />
                  </Button>
                ) : null} 
                <Button 
                    onClick={onSend} 
                    disabled={isLoading || !question.trim()} 
                    sx={{ 
                      p: 0.5,
                      width:50,
                      height:50,
                      borderRadius: '50%',
                      '&:hover': { backgroundColor: '#fff' },
                       minWidth: 0,
                    }}
                  >
                    
                    {isLoading ? <CircularProgress size={20} color="inherit" /> : <Send fontSize="small" />}
                  </Button>
              </InputAdornment>
            ),
            style: {
              height: '60px',
            }
          }}
          sx={{ 
            backgroundColor: '#fff', 
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
    </Box>
  );
};

export default InputArea;  