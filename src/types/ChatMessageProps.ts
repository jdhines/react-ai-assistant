export interface ChatMessageProps {
	id: string;
	role: "user" | "bot";
	type: "text" | "adaptiveCard";
	messageContent: string | null; // Can be string for text or object for adaptive card
	adaptiveContent: object | null; // For adaptive card content
	timestamp?: Date;
}
