import { Outlet, createRootRoute } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import ChatProvider from "~/providers/ChatProvider";
import { Header } from "../components/Header";

export const Route = createRootRoute({
	component: () => (
		<main className="fixed bottom-6 right-6 max-h-[90vh] max-w-[420px] w-full sm:w-[420px] flex flex-col bg-white rounded-lg shadow-lg border border-gray-200">
			<Header />
			<div className="flex-1 flex flex-col min-h-0 overflow-y-auto">
				<ChatProvider>
					<Outlet />
				</ChatProvider>
			</div>
			<TanStackRouterDevtools />
		</main>
	),
});
