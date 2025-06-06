import type { PublicClientApplication } from "@azure/msal-browser";
import {
	AuthenticatedTemplate,
	MsalProvider,
	UnauthenticatedTemplate,
	useMsal,
} from "@azure/msal-react";
import { Button } from "@mui/material";
import { Outlet } from "@tanstack/react-router";
import { loginRequest } from "~/auth/authConfig";
import { PageLayout } from "~/components/PageLayout";
import ChatProvider from "~/providers/ChatProvider";

type AppProps = {
	instance: PublicClientApplication;
};

function MainContent() {
	// Auth instance
	const { instance } = useMsal();
	const activeAccount = instance.getActiveAccount();

	const handleRedirect = () => {
		instance
			.loginRedirect({
				...loginRequest,
				prompt: "create",
			})
			.catch((error) => console.log(error));
	};
	return (
		<>
			<AuthenticatedTemplate>
				{activeAccount ? <Outlet /> : null}
			</AuthenticatedTemplate>
			<UnauthenticatedTemplate>
				<div className="text-center p-12">
					<h1 className="text-xl font-bold mb-4">
						Welcome to HQ Assistant. You must be signed in to your Microsoft
						account to use this app.
					</h1>
					<Button
						variant="contained"
						className="signInButton"
						onClick={handleRedirect}
						color="primary"
					>
						Sign in
					</Button>
				</div>
			</UnauthenticatedTemplate>
		</>
	);
}

export const App: React.FC<AppProps> = ({ instance }) => {
	return (
		<MsalProvider instance={instance}>
			<ChatProvider>
				<PageLayout>
					<MainContent />
				</PageLayout>
			</ChatProvider>
		</MsalProvider>
	);
};
