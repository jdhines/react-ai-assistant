import React from "react";
import type { ChatMessageProps } from "../types/ChatMessageProps";

type ChatContextType = {
	chatId: string;
	getNewChatId: () => string;
	resetChat: (id?: string) => void;
	messages: ChatMessageProps[];
	sendMessage: (userInput: string) => Promise<void>;
	isLoading: boolean;
	cancel: () => void; // Add this line
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
	const [abortController, setAbortController] =
		React.useState<AbortController | null>(null);
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
		let responseObj = data.response;

		// If response is a string, try to parse as JSON, otherwise treat as text
		if (typeof responseObj === "string") {
			try {
				const parsed = JSON.parse(responseObj);
				responseObj = parsed;
			} catch {
				// Not JSON, treat as plain text
				return {
					text: responseObj,
					adaptiveCard: null,
				};
			}
		}

		// If responseObj is now an object, extract fields
		return {
			text: responseObj.text || null,
			adaptiveCard: responseObj.adaptiveCard || null,
		};
	}

	const cancel = React.useCallback(() => {
		if (abortController) {
			abortController.abort();
			setIsLoading(false);
		}
	}, [abortController]);

	const sendMessage = async (userInput: string) => {
		setIsLoading(true);
		const controller = new AbortController();
		setAbortController(controller);
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
					signal: controller.signal, // Pass the signal
				});

				if (response.ok) {
					const data = await response.json();
					const { text, adaptiveCard } = parseApiResponse(data);

					//prioritize adaptiveCard over text
					if (adaptiveCard) {
						console.log("Response data.adaptiveCard:", adaptiveCard);
						addMessage({
							role: "bot",
							type: "adaptiveCard",
							adaptiveContent: adaptiveCard,
							messageContent: text,
						});
					} else {
						console.log("Response data.text:", text);
						addMessage({
							role: "bot",
							type: "text",
							messageContent: text,
						});
					}
				} else {
					throw new Error("Failed to fetch response from server");
				}
			} catch (error) {
				if ((error as any).name === "AbortError") {
					console.error("Request was aborted");
				} else {
					console.error("Error while sending message:", error);
					addMessage({
						role: "bot",
						type: "text",
						messageContent: "Sorry, I encountered an error. Please try again.",
					});
				}
			} finally {
				setIsLoading(false);
				setAbortController(null);
			}
		};

		await fetchChatResponse({
			"Content-Type": "application/json",
			Channel: "copilot",
			"Session-Id": chatId,
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
				cancel, // Add this line
			}}
		>
			{children}
		</ChatContext.Provider>
	);
}

export default ChatProvider;
