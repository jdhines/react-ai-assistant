import React from "react";
import { useChatMessages } from "~/hooks/useChatMessage";

export function ChatSettingsToggles() {
	const { isStreaming, setIsStreaming, isAdaptiveCard, setIsAdaptiveCard } =
		useChatMessages();
	return (
		<div className="flex gap-4 items-center">
			<label className="flex items-center gap-2">
				<input
					type="checkbox"
					checked={isStreaming}
					onChange={(e) => setIsStreaming(e.target.checked)}
				/>
				Streaming
			</label>
			<label className="flex items-center gap-2">
				<input
					type="checkbox"
					checked={isAdaptiveCard}
					onChange={(e) => setIsAdaptiveCard(e.target.checked)}
				/>
				AdaptiveCard
			</label>
		</div>
	);
}
