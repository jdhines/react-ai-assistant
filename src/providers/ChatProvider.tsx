import {
	ChainlitContext,
	type IStep,
	useChatData,
	useChatInteract,
	useChatMessages,
	useChatSession,
} from "@chainlit/react-client";
import React from "react";
import type { ChatMessageProps } from "../types/ChatMessageProps";

type ChatContextType = {
	chatId: string;
	getNewChatId: () => string;
	resetChat: (id?: string) => void;
	messages: ChatMessageProps[];
	sendMessage: (userInput: string) => Promise<void>;
	isLoading: boolean;
	cancel: () => void;
	setIsAdaptiveCard: (value: boolean) => void;
	isAdaptiveCard: boolean;
};

type ChatMessageParams = {
	role: "user" | "bot";
	messageContent?: string;
	adaptiveContent?: object;
	type: "text" | "adaptiveCard";
};

export const ChatContext = React.createContext<ChatContextType | null>(null);

// Utility function to flatten nested messages (from Chainlit)
function flattenMessages(
	messages: IStep[],
	condition: (node: IStep) => boolean,
): IStep[] {
	return messages.reduce((acc: IStep[], node) => {
		if (condition(node)) {
			acc.push(node);
		}

		if (node.steps?.length) {
			acc.push(...flattenMessages(node.steps, condition));
		}

		return acc;
	}, []);
}

// Convert Chainlit IStep messages to your ChatMessageProps format
function convertChainlitMessages(
	chainlitMessages: IStep[],
): ChatMessageProps[] {
	const flatMessages = flattenMessages(
		chainlitMessages,
		(m) => m.type.includes("message") || m.type === "user_message",
	);

	return flatMessages.map((msg): ChatMessageProps => {
		const isUser = msg.type === "user_message" || msg.name === "user";

		return {
			id: msg.id,
			role: isUser ? "user" : "bot",
			messageContent: msg.output || "",
			adaptiveContent: {}, // Chainlit doesn't use adaptive cards in the same way
			type: "text", // Default to text for Chainlit messages
			timestamp: new Date(msg.createdAt),
		};
	});
}

function ChatProvider({ children }: { children: React.ReactNode }) {
	// Chainlit hooks
	const {
		sendMessage: sendChainlitMessage,
		clear,
		stopTask,
	} = useChatInteract();
	const chainlitAPI = React.useContext(ChainlitContext);
	const { connect, disconnect, session } = useChatSession();
	const { loading: isLoading } = useChatData();
	const { messages: chainlitMessages } = useChatMessages();

	// Local state for compatibility with existing interface
	const [chatId, setChatId] = React.useState("");
	const [isAdaptiveCard, setIsAdaptiveCard] = React.useState(false);
	const [isAdaptiveLoading, setIsAdaptiveLoading] = React.useState(false);
	const [localMessages, setLocalMessages] = React.useState<ChatMessageProps[]>(
		[],
	);
	const [abortController, setAbortController] =
		React.useState<AbortController | null>(null);

	// Derived state from Chainlit
	const isConnected = !!session?.socket?.connected;

	// Convert Chainlit messages to your format
	const chainlitConvertedMessages = React.useMemo(() => {
		return convertChainlitMessages(chainlitMessages);
	}, [chainlitMessages]);

	// Merge Chainlit messages into localMessages (avoid duplicates by id)
	React.useEffect(() => {
		setLocalMessages((prev) => {
			// Remove any old chainlit messages
			const nonChainlit = prev.filter(
				(m) => !chainlitConvertedMessages.some((c) => c.id === m.id),
			);
			const merged = [...nonChainlit, ...chainlitConvertedMessages];
			return merged.sort((a, b) => {
				const ta = a.timestamp ? new Date(a.timestamp).getTime() : 0;
				const tb = b.timestamp ? new Date(b.timestamp).getTime() : 0;
				return ta - tb;
			});
		});
	}, [chainlitConvertedMessages]);

	const getNewChatId = () => {
		return crypto.randomUUID();
	};

	const resetChat = (id: string | undefined = crypto.randomUUID()) => {
		setChatId(id);
		setLocalMessages([]); // Clear all messages
		disconnect();
		setTimeout(() => {
			clear();
			connect(chainlitAPI);
		}, 100);
	};

	const cancel = () => {
		stopTask();
		if (abortController) {
			abortController.abort();
			setIsAdaptiveLoading(false);
		}
	};

	const sendMessage = async (userInput: string) => {
		if (isAdaptiveCard) {
			// Add user message
			requestAdaptiveCard(userInput);
			return;
		}
		// Chainlit normal message
		if (!isConnected) {
			console.error("Not connected to Chainlit server");
			return;
		}
		try {
			const message = {
				name: "user",
				type: "user_message" as const,
				output: userInput.trim(),
			};
			sendChainlitMessage(message);
		} catch (error) {
			console.error("Error sending message:", error);
		}
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
		setLocalMessages((prev) => [...prev, nextMessage]);
	};

	const requestAdaptiveCard = async (userInput: string) => {
		const CHAT_ENDPOINT = import.meta.env.VITE_CHAT_ENDPOINT;
		setIsAdaptiveLoading(true);
		const controller = new AbortController();
		setAbortController(controller);

		addMessage({
			role: "user",
			type: "text",
			messageContent: userInput,
		});

		try {
			const response = await fetch(`${CHAT_ENDPOINT}?streaming=false`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					Channel: isAdaptiveCard ? "custom" : "default",
					"Session-Id": chatId,
				},
				body: JSON.stringify({ input: userInput }),
				signal: controller.signal,
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
			setIsAdaptiveLoading(false);
			setAbortController(null);
		}
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

	return (
		<ChatContext.Provider
			value={{
				chatId,
				getNewChatId,
				resetChat,
				messages: localMessages,
				sendMessage,
				isLoading: isLoading || isAdaptiveLoading,
				cancel,
				isAdaptiveCard,
				setIsAdaptiveCard,
			}}
		>
			{children}
		</ChatContext.Provider>
	);
}

export default ChatProvider;
