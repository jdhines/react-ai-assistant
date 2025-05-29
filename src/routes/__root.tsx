import { Outlet, createRootRoute } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import ChatProvider from "~/providers/ChatProvider";
import { Header } from "../components/Header";

export const Route = createRootRoute({
	component: () => (
		<main className="mt-16 max-w-screen-md flex flex-col m-auto max-w-1/3 rounded-md shadow-md">
			<Header />
			<div>
				<ChatProvider>
					<Outlet />
				</ChatProvider>
			</div>
			<TanStackRouterDevtools />
		</main>
	),
});
