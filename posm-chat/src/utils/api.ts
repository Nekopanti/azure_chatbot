// src/utils/api.ts
import axios from "axios";

declare global {
  interface Window {
    VITE_API_BASE_URL: string;
  }
}

const getApiBaseUrl = (): string => {
  if (!window.VITE_API_BASE_URL) {
    throw new Error('VITE_API_BASE_URL is not defined in window object');
  }
  return window.VITE_API_BASE_URL;
};

// Create an instance of axios
const api = axios.create({
  baseURL: getApiBaseUrl(),
});

// A variable that stores the interceptor ID
let interceptorId: number | null = null;
// Export the function for setting the interceptor
export const setupApiInterceptors = (getAccessToken: () => string | null) => {
  // Remove the existing interceptor
  if (interceptorId !== null) {
    api.interceptors.request.eject(interceptorId);
    interceptorId = null;
  }
  
  // Add a new request interceptor and save the ID
  interceptorId = api.interceptors.request.use((config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  
  return api;
};

export const sendQuestion = async (question: string) => {
  try {
    
    // const response = await axios.get(`${getApiBaseUrl()}/ask_question`, {params: {question}});
    const response = await api.get('/ask_question', { params: { question } });
    // const response = await axios.get("http://localhost:3001/api/ask_question", {params: {question}});

    // Extract raw data
    const { natural_language_response, products, confidence } = response.data.result.answer;
    const result = [
      // Article 1: Summary
      {
        text_content: natural_language_response == undefined ? response.data.result.answer:natural_language_response,
        image_sas_url: "",
        match_score:"",
        confidence:confidence == undefined ? "" :confidence
      },
    ];
    // Dynamically traverse the products array to generate subsequent entries
    if(products != undefined && products != null){
      products.forEach((product : any) => {
        // Filter the image_sas_url field and concatenate other fields
        const textFields = Object.entries(product)
          .filter(([key]) => key == "product_summary")
          .map(([key, value]) => `${key}: ${value}`)
          .join("\n");
        
        result.push({
          text_content: textFields.toString(),
          image_sas_url: product.image_url,
          match_score:product.match_score,
          confidence:""
        });
      });
    }
    
    return result;
  } catch (error) {
    console.error("Error sending message:", error);
    throw error;
  }
};

export const getTitle = async (summary: string) => {
  try {
    // const response = await axios.get(`${getApiBaseUrl()}/generate_title`, {params: {summary}});
    const response = await api.get('/generate_title', { params: { summary } });
    // const response = await axios.get("http://localhost:3001/api/generate_title", {params: {summary}});

    return response.data.title;
  } catch (error) {
    console.error("Error sending message:", error);
    throw error;
  }
};