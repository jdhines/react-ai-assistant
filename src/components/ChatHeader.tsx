import { BackButton } from "~/components/BackButton";

interface ChatHeaderProps {
  chatId?: string;
  onNewChat: () => void;
}

export function ChatHeader({ chatId, onNewChat }: ChatHeaderProps) {
  console.log("ChatHeader rendered with chatId:", chatId);
  return (
    <div className="flex px-4 justify-between items-center">
      <BackButton to="/" />
      <button type="button" onClick={onNewChat} className="text-blue-500 bg-none p-2">
        + New Chat
      </button>
    </div>
  );
}