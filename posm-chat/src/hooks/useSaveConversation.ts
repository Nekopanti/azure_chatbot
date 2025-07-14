// hooks/useSaveConversation.ts
import { useCallback } from "react";
import type { Message, SavedConversation } from "../types/chat";

interface UseSaveConversationProps {
  chatHistory: Message[];
  currentConversationId: string | null;
  savedConversations: SavedConversation[];
  setSavedConversations: React.Dispatch<React.SetStateAction<SavedConversation[]>>;
  setCurrentConversationId: React.Dispatch<React.SetStateAction<string | null>>;
  showSnackbar: (message: string) => void;
  currentTitle: string;
}

export const useSaveConversation = ({
  chatHistory,
  currentConversationId,
  savedConversations,
  setSavedConversations,
  setCurrentConversationId,
  showSnackbar,
  currentTitle
}: UseSaveConversationProps) => {
  return useCallback(async () => {
    if (chatHistory.length === 0) return;

    const newOrUpdatedConversation: SavedConversation = {
      id: currentConversationId || Date.now().toString(),
      title: currentTitle,
      messages: [...chatHistory],
      timestamp: new Date(),
      lastSaved: new Date()
    };
    
    // If it is a new conversation, add it to the list
    if (!currentConversationId) {
      setSavedConversations([newOrUpdatedConversation, ...savedConversations]);
    } else {
      const updated = savedConversations.map(convo =>
        convo.id === newOrUpdatedConversation.id ? newOrUpdatedConversation : convo
      );
      setSavedConversations(updated);
    }
    
    // Set current conversation ID
    setCurrentConversationId(newOrUpdatedConversation.id);
    
    // showSnackbar("Conversation saved successfully");
  }, [chatHistory, currentConversationId, savedConversations, setSavedConversations, setCurrentConversationId, showSnackbar]);
};