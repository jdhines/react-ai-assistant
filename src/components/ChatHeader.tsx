import { BackButton } from "~/components/BackButton";
import { ChatSettingsToggles } from "./ChatSettingsToggle";

interface ChatHeaderProps {
	onNewChat: () => void;
}

export function ChatHeader({ onNewChat }: ChatHeaderProps) {
	return (
		<div
			id="chat-header"
			className="sticky top-0 flex px-4 justify-between items-center border border-gray-100 bg-white"
		>
			<BackButton to="/" />
			<ChatSettingsToggles />
			<button
				type="button"
				onClick={onNewChat}
				className="text-blue-500 bg-none p-2"
			>
				+ New Chat
			</button>
		</div>
	);
}
