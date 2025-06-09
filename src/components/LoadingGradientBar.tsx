import "./LoadingGradientBar.css";
import { MessageCircleX } from "lucide-react";
import { useChatMessages } from "~/hooks/useChatMessage";

export function LoadingGradientBar() {
	const { cancel } = useChatMessages();
	return (
		<div className="p-4">
			<div className="w-1/2 max-w-full h-2 rounded-full overflow-hidden bg-gray-200">
				<div className="loading-gradient-bar h-full w-full animate-gradient-x" />
			</div>
			<button
				type="button"
				className="ml-2 bg-none text-gray-600 hover:text-blue-900 self-start"
				onClick={cancel}
			>
				<MessageCircleX size={16} className="inline" /> Stop generating
			</button>
		</div>
	);
}
