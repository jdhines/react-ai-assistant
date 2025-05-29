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
	const { messages, sendMessage, isLoading } = useChatMessages();
	const { chatId, getNewChatId, resetChat } = React.useContext(ChatContext);
	const navigate = useNavigate();

	const handleSendMessage = async (message: string) => {
		setUserInput("");
		await sendMessage(message);
	};

	const handleNewChat = () => {
		setUserInput("");
		const nextChatId = getNewChatId();
		resetChat(nextChatId);
		navigate({
			to: `/chat/${nextChatId}`,
			replace: true,
		});
	};

	return (
		<div className="flex-1 flex flex-col min-h-0">
			<ChatHeader chatId={chatId} onNewChat={handleNewChat} />
			<ChatMessageList messages={messages} />
			{isLoading && (
				<div className="flex items-center p-4">
					<LoadingGradientBar />
				</div>
			)}
			<ChatInput
				userInput={userInput}
				onUserInputChange={setUserInput}
				onSubmit={handleSendMessage}
				disabled={isLoading}
			/>
		</div>
	);
}
