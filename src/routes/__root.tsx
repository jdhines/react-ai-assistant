import '@copilotkit/react-ui/styles.css'
import { createRootRoute } from "@tanstack/react-router";
import { CopilotKit } from '@copilotkit/react-core'
import { App } from "~/components/App";


const COPILOTKIT_URL = "http://localhost:4000/copilotkit";

/*
  Optional: create a .env file in the root of your project with the following content:
	VITE_COPILOTKIT_URL=http://localhost:4000/copilotkit
	Then use this line to import it:
	const COPILOTKIT_URL = import.meta.env.VITE_COPILOTKIT_URL;
*/

export const Route = createRootRoute({
	component: () => {
		return (
			<CopilotKit
				runtimeUrl={COPILOTKIT_URL}
				agent="sample_agent"
			>
				<App />
			</CopilotKit>
		);
	},
});
