import { fetchEventSource } from "@microsoft/fetch-event-source";
import React from "react";
import type { ChatMessageProps } from "../types/ChatMessageProps";

type ChatContextType = {
	chatId: string;
	getNewChatId: () => string;
	resetChat: (id?: string) => void;
	messages: ChatMessageProps[];
	sendMessage: (userInput: string, streaming?: boolean) => Promise<void>;
	isLoading: boolean;
	cancel: () => void;
	isStreaming: boolean;
	isAdaptiveCard: boolean;
	setIsStreaming: (value: boolean) => void;
	setIsAdaptiveCard: (value: boolean) => void;
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
	const [isStreaming, setIsStreaming] = React.useState(false);
	const [isAdaptiveCard, setIsAdaptiveCard] = React.useState(false);
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
	const parseApiResponse = (data: any) => {
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
	};

	const cancel = React.useCallback(() => {
		if (abortController) {
			abortController.abort();
			setIsLoading(false);
		}
	}, [abortController]);

	// Extracted streaming handler
	const handleStreamingMessage = async (
		userInput: string,
		headers: Record<string, string>,
		controller: AbortController,
	) => {
		let accumulatedText = "";
		let lastMessageId: string | null = null;
		try {
			await fetchEventSource(`${CHAT_ENDPOINT}?streaming=true`, {
				method: "POST",
				headers,
				body: JSON.stringify({ input: userInput }),
				signal: controller.signal,
				onmessage(ev) {
					if (!ev.data) return;
					let parsed: string | { text: string };
					try {
						parsed = JSON.parse(ev.data);
					} catch {
						parsed = { text: ev.data };
					}

					const { text } = parseApiResponse({ response: parsed });
					if (text) {
						accumulatedText += text.replace(/\n/g, "<br />");
						if (lastMessageId) {
							setMessages((prev) =>
								prev.map((msg) =>
									msg.id === lastMessageId
										? { ...msg, messageContent: accumulatedText }
										: msg,
								),
							);
						} else {
							const newMsg: ChatMessageProps = {
								id: crypto.randomUUID(),
								role: "bot",
								type: "text",
								messageContent: accumulatedText,
								adaptiveContent: null,
								timestamp: new Date(),
							};
							setMessages((prev) => [...prev, newMsg]);
							lastMessageId = newMsg.id;
						}
					}
				},
				onerror(err) {
					console.error("Streaming error:", err);
					addMessage({
						role: "bot",
						type: "text",
						messageContent:
							"Sorry, I encountered a streaming error. Please try again.",
					});
					controller.abort();
				},
				openWhenHidden: true,
			});
		} catch (error) {
			if ((error as any).name === "AbortError") {
				console.error("Streaming request was aborted");
			} else {
				console.error("Error while streaming message:", error);
				addMessage({
					role: "bot",
					type: "text",
					messageContent: "Sorry, I encountered an error. Please try again.",
				});
			}
		} finally {
			console.log("setting loading to false");
			setIsLoading(false);
			setAbortController(null);
		}
	};

	// Extracted non-streaming handler
	const handleNonStreamingMessage = async (
		userInput: string,
		headers: Record<string, string>,
		controller: AbortController,
	) => {
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
				console.log("Parsed response:", { text, adaptiveCard });

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

	const sendMessage = async (userInput: string) => {
		setIsLoading(true);
		const controller = new AbortController();
		setAbortController(controller);
		addMessage({
			role: "user",
			type: "text",
			messageContent: userInput.trim(),
		});

		const headers = {
			"Content-Type": "application/json",
			Channel: isAdaptiveCard ? "custom" : "default",
			"Session-Id": chatId,
		};

		if (isStreaming) {
			await handleStreamingMessage(userInput, headers, controller);
		} else {
			await handleNonStreamingMessage(userInput, headers, controller);
		}
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
				cancel,
				isStreaming,
				setIsStreaming,
				isAdaptiveCard,
				setIsAdaptiveCard,
			}}
		>
			{children}
		</ChatContext.Provider>
	);
}

export default ChatProvider;
