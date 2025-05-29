// ChatMessageProps type for chat messages
export interface ChatMessageProps {
  id: string;
  role: "user" | "bot";
  text: string;
  timestamp?: Date;
}
