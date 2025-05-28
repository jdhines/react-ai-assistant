import React from "react";

export function useChatMessages() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);

  const CHAT_ENDPOINT = import.meta.env.CHAT_ENDPOINT;

  const addMessage = (sender: 'user' | 'bot', text: string) => {
    const nextMessage = {
      id: crypto.randomUUID(),
      sender,
      text,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, nextMessage]);
  };

  const sendMessage = async (userInput: string) => {
    setIsLoading(true);
    addMessage("user", userInput);

    //TODO: remove this test for adaptive cards
    // if the userInput contains "adaptive card", simulate a response from utils/adaptive-sample.json
    if (userInput.toLowerCase().includes("adaptive")) {
      addMessage("bot", "Adaptive Card sample:");
      return;
    }

    try {
      const response = await fetch(
        CHAT_ENDPOINT,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ input: userInput }),
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