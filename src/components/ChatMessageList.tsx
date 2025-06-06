import { Bot, Send, User } from "lucide-react";
import React from "react";
import ReactMarkdown from "react-markdown";
import { AdaptiveCard } from "~/components/adaptivecards-react/adaptive-card";
import type { ChatMessageProps } from "../types/ChatMessageProps";

interface ChatMessageListProps {
	messages: ChatMessageProps[];
}

export function ChatMessageList({ messages }: ChatMessageListProps) {
	const bottomRef = React.useRef<HTMLDivElement>(null);

	React.useEffect(() => {
		if (messages.length > 0) {
			// Scroll to the bottom when messages change
			bottomRef.current?.scrollIntoView({ behavior: "smooth" });
		}
	}, [messages]);

	return (
		<div className="flex-1 flex flex-col gap-4 overflow-y-auto p-4 scroll-smooth">
			{messages.map((msg) => (
				<ChatMessage key={msg.id} {...msg} />
			))}
			<div ref={bottomRef} />
		</div>
	);
}

function ChatMessage(props: ChatMessageProps) {
	const { role, messageContent, adaptiveContent, type, timestamp } = props;
	//TODO: Remove example of adaptive card
	const handleError = (error: Error) => {
		console.error("Adaptive Card error:", error);
	};
	const hostConfig = {
		fontFamily: "Segoe UI, Helvetica Neue, sans-serif",
	};
	return (
		<div className={role === "user" ? "justify-end" : "justify-start"}>
			<div
				className={`flex items-start space-x-2 max-w-2xl ${role === "user" ? "flex-row-reverse space-x-reverse" : ""}`}
			>
				{/* Avatar */}
				<div
					className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
						role === "user" ? "bg-blue-600" : "bg-gray-600"
					}`}
				>
					{role === "user" ? (
						<User className="w-4 h-4 text-white" />
					) : (
						<Bot className="w-4 h-4 text-white" />
					)}
				</div>

				{/* Message Content */}
				<div
					className={`flex flex-col space-y-2 ${role === "user" ? "items-end" : "items-start"}`}
				>
					<div
						className={`rounded-lg px-4 py-2 ${
							role === "user"
								? "bg-blue-600 text-white"
								: "bg-white text-gray-800 border border-gray-200"
						}`}
					>
						{type === "adaptiveCard" ? (
							<AdaptiveCard
								payload={adaptiveContent ?? {}}
								onError={handleError}
								hostConfig={hostConfig}
							/>
						) : (
							<div className="markdown-body">
								<ReactMarkdown>{messageContent}</ReactMarkdown>
							</div>
						)}
					</div>

					<span className="text-xs text-gray-500">
						{timestamp ? timestamp.toLocaleTimeString() : ""}
					</span>
				</div>
			</div>
		</div>
	);
}
