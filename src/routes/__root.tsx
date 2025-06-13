import { createRootRoute } from "@tanstack/react-router";
import { App } from "~/components/App";
import { ChainlitAPI, ChainlitContext } from '@chainlit/react-client'
import { RecoilRoot } from 'recoil'

const CHAINLIT_SERVER = import.meta.env.VITE_CHAINLIT_ENDPOINT || 'http://localhost:8001';

const chainlitAPI = new ChainlitAPI(CHAINLIT_SERVER, 'webapp')

export const Route = createRootRoute({
	component: () => {
		return (
			<ChainlitContext.Provider value={chainlitAPI}>
				<RecoilRoot>
					<App />
				</RecoilRoot>
			</ChainlitContext.Provider>
		);
	},
});
