import {
	type AuthenticationResult,
	EventType,
	PublicClientApplication,
} from "@azure/msal-browser";
import { createRootRoute } from "@tanstack/react-router";
import { msalConfig } from "~/auth/authConfig";
import { App } from "~/components/App";

const msalInstance = new PublicClientApplication(msalConfig);

if (
	!msalInstance.getActiveAccount() &&
	msalInstance.getAllAccounts().length > 0
) {
	// Default to using the first account if no account is active on page load
	// Account selection logic is app dependent. Adjust as needed for different use cases.
	const accounts = msalInstance.getAllAccounts();
	msalInstance.setActiveAccount(accounts[0]);
}

// Listen for sign-in event and set active account
msalInstance.addEventCallback((event) => {
	if (
		event.eventType === EventType.LOGIN_SUCCESS &&
		event.payload &&
		(event.payload as AuthenticationResult).account
	) {
		const account = (event.payload as AuthenticationResult).account;
		msalInstance.setActiveAccount(account);
	}
});

export const Route = createRootRoute({
	component: () => {
		return <App instance={msalInstance} />;
	},
});
