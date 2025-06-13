import { Bot, User } from "lucide-react";
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
		<div
			id="chat-message-list"
			className="flex-1 min-h-96 h-full flex flex-col gap-4 overflow-y-auto p-4 scroll-smooth"
		>
			{messages.length === 0 ? (
				<div className="flex-1" />
			) : (
				messages.map((msg) => <ChatMessage key={msg.id} {...msg} />)
			)}
			<div ref={bottomRef} />
		</div>
	);
}

function ChatMessage(props: ChatMessageProps) {
	const { role, messageContent, adaptiveContent, type, timestamp } = props;
	const handleError = (error: Error) => {
		console.error("Adaptive Card error:", error);
	};
	const hostConfig = {
		fontFamily: "Segoe UI, Helvetica Neue, sans-serif",
	};
	return (
		<div id="chat-messages" className="mb-4">
			<div
				className={`max-w-2xl ${role === "user" ? "flex items-start flex-row-reverse space-x-2 space-x-reverse" : ""}`}
			>
				{/* Avatar */}
				<div
					className={`${
						role === "user"
							? "bg-blue-600 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
							: ""
					}`}
				>
					{role === "user" ? (
						<User className="w-4 h-4 text-white" />
					) : (
						<p>
							<img
								className="inline-block"
								src="/public/favicon-32x32.png"
								alt="assistant"
							/>
							<span className="font-bold">HQ Assistant</span>
						</p>
					)}
				</div>

				{/* Message Content */}
				<div
					className={`flex flex-col space-y-2 ${role === "user" ? "items-end" : "items-start"}`}
				>
					<div
						className={`rounded-lg px-8 py-2 ${
							role === "user"
								? "bg-blue-600 text-white"
								: "bg-white text-gray-800"
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

					<span
						className={`text-xs text-gray-500 ${role === "bot" ? "pl-8" : ""}`}
					>
						{timestamp ? timestamp.toLocaleTimeString() : ""}
					</span>
				</div>
			</div>
		</div>
	);
}
