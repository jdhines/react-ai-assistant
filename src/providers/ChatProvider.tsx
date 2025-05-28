import React from 'react';

export const ChatContext = React.createContext();

function ChatProvider({ children }) {
  const [chatId, setChatId] = React.useState("");

  const getNewChatId = () => {
    return crypto.randomUUID();
  };
  const resetChat = (id = crypto.randomUUID()) => {
    setChatId(id);
  };

  return (
    <ChatContext.Provider value={{ chatId, getNewChatId, resetChat }}>
      {children}
    </ChatContext.Provider>
  );
}

export default ChatProvider;