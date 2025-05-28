import { createFileRoute, useNavigate, useParams } from "@tanstack/react-router";
import React from "react";
import { ChatPage } from "~/pages/chat";
import { ChatContext } from "~/providers/ChatProvider";


export const Route = createFileRoute("/chat/")({
	head: () => ({
		meta: [{ title: "Chat" }],
	}),
	component: ChatIndexRoute,
});

function ChatIndexRoute() {
	const navigate = useNavigate();
	const { chatId, resetChat } = React.useContext(ChatContext);

	React.useEffect(() => {
		if (chatId) {
			navigate({
				to: `/chat/${chatId}`,
				params: { chatId },
				replace: true, // Avoid adding a new history entry
			});
		} else {
			resetChat();
		}
	}, [chatId, navigate, resetChat]);

	return <ChatPage />;
}