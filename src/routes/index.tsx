import { createFileRoute } from "@tanstack/react-router";
import React from "react";
import HomeLink from "~/components/HomeLink";
import { ChatContext } from "~/providers/ChatProvider";

export const Route = createFileRoute("/")({
	head: () => ({
		meta: [{ title: "Chat" }],
	}),
	component: Welcome,
});

function Welcome() {
	const { chatId } = React.useContext(ChatContext);
	const chatLink = chatId ? `/chat/${chatId}` : "/chat";
	return (
		<nav className="grid grid-cols-2 gap-4 items-stretch p-6 ">
			<HomeLink className="row-span-2" to={chatLink} type="primary">
				Ask a question
			</HomeLink>
			<HomeLink to="/new-request" type="secondary">
				Make a request
			</HomeLink>
			<HomeLink to="/track-request" type="default">
				Track a request
			</HomeLink>
		</nav>
	);
}
