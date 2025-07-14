// AudioButtonWithPulse.tsx
import { useState } from 'react';
import { Box, IconButton, Tooltip, styled } from '@mui/material';
import { Stop, VolumeUp } from '@mui/icons-material';

// Creating an animated pulse component
const PulseAnimation = styled(Box)(({  }) => ({
  position: 'absolute',
  top: 0,
  left: 0,
  width: '100%',
  height: '100%',
  borderRadius: '50%',
  backgroundColor: 'currentColor',
  opacity: 0.3,
  animation: '$pulse 2s infinite',
  zIndex: 0
}));

// Define animation
const PulseButton = styled(IconButton)({
  '&:hover': {
    transform: 'scale(1.1)',
  },
  position: 'relative',
  overflow: 'hidden',
  
  // Define pulse animation
  '@keyframes pulse': {
    '0%': {
      transform: 'scale(0.8)',
      opacity: 0.3,
    },
    '70%': {
      transform: 'scale(1.5)',
      opacity: 0,
    },
    '100%': {
      transform: 'scale(0.8)',
      opacity: 0,
    },
  }
});

interface AudioButtonWithPulseProps {
  text: string;
  color: string;
}

const AudioButtonWithPulse = ({ text, color }: AudioButtonWithPulseProps) => {
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Speech synthesis function
  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'en-US';
      
      // Set sound properties
      utterance.rate = 0.95; // speaking speed
      utterance.pitch = 1.1;  // tone
      
      // Get a list of available sounds
      const voices = window.speechSynthesis.getVoices();

      // Test sound list
      console.log('List of available voices：');
      voices.forEach((voice, index) => {
        console.log(`[${index}] Name: ${voice.name}, language: ${voice.lang}`);
      });
      
      // Find a specific sound（eg：Microsoft Zira Desktop - English (United States)）
      const desiredVoice = voices.find(voice => 
        voice.name === 'Microsoft Zira - English (United States)'
      );
      
      // If you find the sound you want, set it
      if (desiredVoice) {
        utterance.voice = desiredVoice;
      }

      // Start playing
      window.speechSynthesis.speak(utterance);
      setIsPlaying(true);
      
      // Listen for speech end events
      utterance.onend = () => {
        setIsPlaying(false);
      };
      
      utterance.onerror = (error) => {
        console.error('Speech synthesis error:', error);
        setIsPlaying(false);
      };
      
      return utterance;
    } else {
      console.error('Speech synthesis is not supported in this browser.');
      return null;
    }
  };
  
  // Stop speech synthesis
  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    }
  };
  
  // Switch playback status
  const togglePlay = () => {
    if (isPlaying) {
      stopSpeaking();
    } else {
      speakText(text);
      setIsPlaying(true);
    }
  };
  
  return (
    <Tooltip title={isPlaying ? 'Stop playing' : 'Listen to response'} placement="top">
      <PulseButton size="small" color="primary" onClick={togglePlay}
        sx={{ width: 32, height: 32, borderRadius: '50%', backgroundColor: isPlaying ? color : 'transparent', color: isPlaying ? 'white' : color, transition: 'all 0.3s ease','&:hover': { backgroundColor: isPlaying ? `${color}cc` : 'rgba(255, 101, 0, 0.1)' }, }} >
        {isPlaying ? (
          <Stop fontSize="small" />
        ) : (
          <VolumeUp fontSize="small" />
        )}
        
        {/* Pulse animation effect */}
        {isPlaying && <PulseAnimation />}
      </PulseButton>
    </Tooltip>
  );
};

export default AudioButtonWithPulse;