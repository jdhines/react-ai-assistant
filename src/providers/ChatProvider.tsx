import React from "react";
import type { ChatMessageProps } from "../types/ChatMessageProps";

type ChatContextType = {
	chatId: string;
	getNewChatId: () => string;
	resetChat: (id?: string) => void;
	messages: ChatMessageProps[];
	sendMessage: (userInput: string) => Promise<void>;
	isLoading: boolean;
};

type ChatMessageParams = {
	role: "user" | "bot";
	messageContent?: string;
	adaptiveContent?: object;
	type: "text" | "adaptiveCard";
};

export const ChatContext = React.createContext<ChatContextType | null>(null);

function ChatProvider({ children }: { children: React.ReactNode }) {
	const [chatId, setChatId] = React.useState("");
	const [messages, setMessages] = React.useState<ChatMessageProps[]>([]);
	const [isLoading, setIsLoading] = React.useState(false);
	const CHAT_ENDPOINT = import.meta.env.VITE_CHAT_ENDPOINT;

	const getNewChatId = () => {
		return crypto.randomUUID();
	};
	const resetChat = (id: string | undefined = crypto.randomUUID()) => {
		setChatId(id);
		setMessages([]);
	};

	const addMessage = ({
		role,
		messageContent = "",
		adaptiveContent = {},
		type,
	}: ChatMessageParams) => {
		const nextMessage: ChatMessageProps = {
			id: crypto.randomUUID(),
			role,
			messageContent,
			adaptiveContent,
			type,
			timestamp: new Date(),
		};
		setMessages((prev) => [...prev, nextMessage]);
	};

	// Helper to parse API response and extract text/adaptiveCard
	function parseApiResponse(data: any) {
		let responseObj = data;
		if (typeof responseObj === "string") {
			try {
				responseObj = JSON.parse(responseObj);
			} catch (e) {
				console.error("Failed to parse response string as JSON", e);
			}
		}
		if (responseObj.response) {
			if (typeof responseObj.response === "string") {
				try {
					responseObj = JSON.parse(responseObj.response);
				} catch (e) {
					console.error("Failed to parse nested response string as JSON", e);
				}
			} else {
				responseObj = responseObj.response;
			}
		}
		return {
			text: responseObj.text || null,
			adaptiveCard: responseObj.adaptiveCard || null,
			fallback:
				!responseObj.text && !responseObj.adaptiveCard ? responseObj : null,
		};
	}

	const sendMessage = async (userInput: string) => {
		setIsLoading(true);
		addMessage({
			role: "user",
			type: "text",
			messageContent: userInput.trim(),
		});

		// Helper to send the fetch request
		const fetchChatResponse = async (headers: Record<string, string>) => {
			try {
				const response = await fetch(CHAT_ENDPOINT, {
					method: "POST",
					headers,
					body: JSON.stringify({ input: userInput }),
				});

				if (response.ok) {
					const data = await response.json();
					const { text, adaptiveCard, fallback } = parseApiResponse(data);
					if (text) {
						console.log("Response data.text:", text);
						addMessage({
							role: "bot",
							type: "text",
							messageContent: text,
						});
					}
					if (adaptiveCard) {
						console.log("Response data.adaptiveCard:", adaptiveCard);
						addMessage({
							role: "bot",
							type: "adaptiveCard",
							adaptiveContent: adaptiveCard,
						});
					}
					if (!text && !adaptiveCard && fallback) {
						console.log("only response found");
						addMessage({
							role: "bot",
							type: "text",
							messageContent: JSON.stringify(fallback),
						});
					}
					console.log("Response from server:", data);
				} else {
					throw new Error("Failed to fetch response from server");
				}
			} catch (error) {
				console.error("Error while sending message:", error);
				addMessage({
					role: "bot",
					type: "text",
					messageContent: "Sorry, I encountered an error. Please try again.",
				});
			} finally {
				setIsLoading(false);
			}
		};

		await fetchChatResponse({
			"Content-Type": "application/json",
			channel: "custom",
		});
	};

	return (
		<ChatContext.Provider
			value={{
				chatId,
				getNewChatId,
				resetChat,
				messages,
				sendMessage,
				isLoading,
			}}
		>
			{children}
		</ChatContext.Provider>
	);
}

export default ChatProvider;
