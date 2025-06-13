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
	const { messages: chainlitMessages } = useChatMessages();
	const { connect, disconnect, session } = useChatSession();
	const { loading: isLoading } = useChatData();
	const chainlitAPI = React.useContext(ChainlitContext);
	// Local state for compatibility with existing interface
	const [chatId, setChatId] = React.useState("");
	const [isAdaptiveCard, setIsAdaptiveCard] = React.useState(false);

	// Derived state from Chainlit
	const isConnected = !!session?.socket?.connected;

	// Convert Chainlit messages to your format
	const messages = React.useMemo(() => {
		return convertChainlitMessages(chainlitMessages);
	}, [chainlitMessages]);

	const getNewChatId = () => {
		return crypto.randomUUID();
	};

	const resetChat = (id: string | undefined = crypto.randomUUID()) => {
		// For Chainlit, we disconnect and reconnect to start a new session
		setChatId(id);
		disconnect();
		setTimeout(() => {
			clear();
			connect(chainlitAPI);
		}, 100);
	};

	const cancel = () => {
		stopTask();
	};

	const sendMessage = async (userInput: string) => {
		if (!isConnected) {
			console.error("Not connected to Chainlit server");
			return;
		}

		try {
			const message = {
				name: "user",
				type: "user_message" as const,
				output: `#Adaptive#${userInput.trim()}`,
			};

			sendChainlitMessage(message);
		} catch (error) {
			console.error("Error sending message:", error);
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
				isAdaptiveCard,
				setIsAdaptiveCard,
			}}
		>
			{children}
		</ChatContext.Provider>
	);
}

export default ChatProvider;
