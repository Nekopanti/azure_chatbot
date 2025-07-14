// types/chat.d.ts
export interface Message {
  id: string;
  question: string;
  answer: string;
  imageUrls: string;
  timestamp: Date;
  role: 'user' | 'assistant'; 
  match_score: string;
  confidence: string;
  likes?: number;
  dislikes?: number;
  liked?: boolean;
  disliked?: boolean;
}

export interface SavedConversation {
  lastSaved: Date;
  id: string;
  title: string;
  messages: Message[];
  timestamp: Date;
  isCurrent?: boolean;
}

export interface ThemeStyles {
  bgColor: string;
  cardBg: string;
  textColor: string;
  primaryColor: string;
  secondaryBg: string;
  sidebarBg: string;
  sidebarText: string;
  borderColor: string;
  palette: {
    primary: {
      main: string;
    };
    text: {
      primary: string;
      secondary: string;
    };
    background: {
      default: string;
      paper: string;
    };
  };
};