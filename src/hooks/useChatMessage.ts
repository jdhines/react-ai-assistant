import React from "react";
import type { ChatMessageProps } from "../types/ChatMessageProps";

export function useChatMessages() {
  const [messages, setMessages] = React.useState<ChatMessageProps[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);

  const CHAT_ENDPOINT = import.meta.env.VITE_CHAT_ENDPOINT;

  const addMessage = (role: 'user' | 'bot', text: string) => {
    const nextMessage: ChatMessageProps = {
      id: crypto.randomUUID(),
      role,
      text,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, nextMessage]);
  };

  const sendMessage = async (userInput: string) => {
    setIsLoading(true);
    addMessage("user", userInput.trim());

    const bodyMessages = [...messages, {role: "user", content: userInput.trim()}];
    const bodyJson = JSON.stringify({"messages": bodyMessages});

    //TODO: remove this test for adaptive cards
    // if the userInput contains "adaptive card", simulate a response from utils/adaptive-sample.json
    if (userInput.toLowerCase().includes("adaptive")) {
      addMessage("bot", "Adaptive Card sample:");
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(
        CHAT_ENDPOINT,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ input: userInput }),
          // body: bodyJson,
        }
      );

      if (response.ok) {
        const data = await response.json();
        addMessage("bot", data.response);
      } else {
        throw new Error("Failed to fetch response from server");
      }
    } catch (error) {
      console.error("Error while sending message:", error);
      addMessage("bot", "Sorry, I encountered an error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const clearMessages = () => setMessages([]);

  return { messages, sendMessage, clearMessages, isLoading };
}