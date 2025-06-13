import React from "react";
import { Outlet } from "@tanstack/react-router";
import { ChainlitContext, useChatSession, sessionState } from "@chainlit/react-client";
import { useRecoilValue } from 'recoil';
import { PageLayout } from "~/components/PageLayout";
import ChatProvider from "~/providers/ChatProvider";



export const App = () => {
	const { connect, disconnect } = useChatSession();
	const session = useRecoilValue(sessionState);
	const chainlitAPI = React.useContext(ChainlitContext)
  // const connectionStatus = sessionState..value.status;
	// const isConnected = connectionStatus === 'connected';

  React.useEffect(() => {
    if (session?.socket.connected) {
      return;
    }

		connect(chainlitAPI);

		return () => {
			disconnect();
		};
  }, []);

	return (
		<ChatProvider>
			<PageLayout>
				<Outlet />
			</PageLayout>
		</ChatProvider>
	);
};
