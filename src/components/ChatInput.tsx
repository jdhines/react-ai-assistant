import { Send } from "lucide-react";
import type { FormEvent } from "react";
import { VisuallyHidden } from "./VisuallyHidden";
interface ChatInputProps {
	userInput: string;
	onUserInputChange: (value: string) => void;
	onSubmit: (e: FormEvent) => void;
	disabled?: boolean;
}

export function ChatInput({
	userInput,
	onUserInputChange,
	onSubmit,
	disabled,
}: ChatInputProps) {
	const handleSubmit = (e: FormEvent) => {
		e.preventDefault();
		if (userInput.trim()) {
			onSubmit(e);
		}
	};

	return (
		<div
			id="chat-input"
			className="sticky bottom-0 bg-white border-t border-gray-200 p-4"
		>
			<form onSubmit={handleSubmit} className="flex space-x-2">
				<input
					type="text"
					value={userInput}
					onChange={(e) => onUserInputChange(e.target.value)}
					placeholder="Type your message. Enter 'adaptive' for a sample adaptive card."
					className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					disabled={disabled}
				/>
				<button
					type="submit"
					className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-1"
					disabled={disabled}
				>
					<Send className="w-4 h-4" />
					<VisuallyHidden>Send</VisuallyHidden>
				</button>
			</form>
		</div>
	);
}
