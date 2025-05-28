import React from "react";
import { useNavigate } from "@tanstack/react-router";
import { ChatHeader } from "~/components/ChatHeader";
import { ChatInput } from "~/components/ChatInput";
import { ChatMessageList } from "~/components/ChatMessageList";
import { ChatContext } from "~/providers/ChatProvider";
import { useChatMessages } from "~/hooks/useChatMessage";

export function ChatPage() {
  const [userInput, setUserInput] = React.useState("");
  const { messages, sendMessage, clearMessages, isLoading } = useChatMessages();
  const { chatId, getNewChatId, resetChat } = React.useContext(ChatContext);
  const navigate = useNavigate();

  const handleSendMessage = async (message: string) => {
    setUserInput("");
    await sendMessage(message);
  };

  const handleNewChat = () => {
    clearMessages();
    setUserInput("");
    const nextChatId = getNewChatId();
    resetChat(nextChatId);
    navigate({
      to: `/chat/${nextChatId}`,
      replace: true,
    });
  };

  return (
    <div className="flex flex-col h-full min-h-96">
      <ChatHeader chatId={chatId} onNewChat={handleNewChat} />
      <ChatMessageList messages={messages} />
      <ChatInput
        userInput={userInput}
        onUserInputChange={setUserInput}
        onSubmit={handleSendMessage}
        disabled={isLoading}
      />
    </div>
  );
}