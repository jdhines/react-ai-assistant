import React from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ChatPage } from "~/pages/chat";
import { ChatContext } from "~/providers/ChatProvider";

export const Route = createFileRoute("/chat/$chatId")({
  head: () => ({
		meta: [{ title: "Chat" }],
	}),
  component: ChatRouteComponent,
});

function ChatRouteComponent() {
  const { chatId: urlChatId } = Route.useParams();
  const { chatId: contextChatId, resetChat } = React.useContext(ChatContext);

  React.useEffect(() => {
    // If the URL chatId is different from context chatId, update context
    if (urlChatId !== contextChatId) {
      resetChat(urlChatId);
    }
  }, [urlChatId, contextChatId, resetChat ]);

  return <ChatPage />;
}