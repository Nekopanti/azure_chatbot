// components/SearchBar/index.tsx
import { TextField, InputAdornment, IconButton } from "@mui/material";
import { Search } from "@mui/icons-material";

interface SearchBarProps {
  searchText: string;
  setSearchText: React.Dispatch<React.SetStateAction<string>>;
}

const SearchBar = ({ searchText, setSearchText }: SearchBarProps) => {
  return (
    <TextField
      fullWidth
      variant="outlined"
      size="small"
      placeholder="Search conversation"
      value={searchText}
      onChange={(e) => setSearchText(e.target.value)}
      onKeyDown={(e) => e.key === "Enter"}
      InputProps={{
        endAdornment: (
          <InputAdornment position="end">
            <IconButton aria-label="search" color="primary"><Search /></IconButton>
          </InputAdornment>
        ),
        style: {
          fontSize: '12px', 
        },
      }}
     sx={{
        ".MuiOutlinedInput-root": {
          borderColor: '#000',
          borderWidth: 1,
          "&:hover": {
            borderColor: '#000',
          },
          "&.Mui-focused": {
            borderColor: '#555',
            // boxShadow: '0 0 0 2px rgba(0, 0, 0, 0.1)',
          },
        },
        ".MuiInputLabel-outlined": {
          color: '#999',
        },
      }}
    />
  );
};

export default SearchBar;