import { Outlet, createRootRoute } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import React from "react";
import { Footer } from "~/components/Footer";
import ChatProvider from "~/providers/ChatProvider";
import { Header } from "../components/Header";

export const Route = createRootRoute({
	component: () => {
		const [expanded, setExpanded] = React.useState(false);
		const toggleExpand = () => setExpanded((e) => !e);
		return (
			<ChatProvider>
				<main
					className={`fixed bottom-6 right-6 min-h-[50vh] ${expanded ? "max-w-[840px] w-[840px] max-h-[95vh] h-[95vh]" : "w-[560px] max-h-[95vh]"} flex flex-col bg-white rounded-lg shadow-lg border border-gray-200`}
					style={{ zIndex: 50 }}
				>
					<Header expanded={expanded} toggleExpand={toggleExpand} />
					<div className="flex-1 flex flex-col min-h-0 bg-gradient-to-br from-cyan-200 to-blue-200 ">
						<Outlet />
					</div>
					<TanStackRouterDevtools />
					<Footer />
				</main>
			</ChatProvider>
		);
	},
});
