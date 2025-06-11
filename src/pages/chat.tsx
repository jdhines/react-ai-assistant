import { useNavigate } from "@tanstack/react-router";
import React from "react";
import { ChatHeader } from "~/components/ChatHeader";
import { ChatInput } from "~/components/ChatInput";
import { ChatMessageList } from "~/components/ChatMessageList";
import { LoadingGradientBar } from "~/components/LoadingGradientBar";
import { useChatMessages } from "~/hooks/useChatMessage";
import { ChatContext } from "~/providers/ChatProvider";


export function ChatPage() {
	const [userInput, setUserInput] = React.useState("");

	const {
		chatId,
		getNewChatId,
		resetChat,
		messages,
		sendMessage,
		isLoading,
	} = useChatMessages();
	const chatContext = React.useContext(ChatContext);
	if (!chatContext) {
		throw new Error(
			"Error getting context. Make sure ChatProvider is in the component tree.",
		);
	}
	const navigate = useNavigate();

	const handleSendMessage = async () => {
		if (!userInput.trim()) return;
		setUserInput("");
		await sendMessage(userInput);
	};

	const handleNewChat = () => {
		if (!getNewChatId || !resetChat) return;
		setUserInput("");
		const nextChatId = getNewChatId();
		resetChat(nextChatId);
		navigate({
			to: `/chat/${nextChatId}`,
			replace: true,
		});
	};

	return (
		<div id="chat-page" className="flex flex-col flex-1 bg-white">
			<ChatHeader chatId={chatId} onNewChat={handleNewChat} />
			<ChatMessageList messages={messages} />
			{isLoading && <LoadingGradientBar />}
			<ChatInput
				userInput={userInput}
				onUserInputChange={setUserInput}
				onSubmit={(e) => {
					e.preventDefault();
					handleSendMessage();
				}}
				disabled={isLoading}
			/>
		</div>
	);
}
