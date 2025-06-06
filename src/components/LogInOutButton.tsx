import {
	AuthenticatedTemplate,
	UnauthenticatedTemplate,
	useMsal,
} from "@azure/msal-react";
import { Button } from "@mui/material";
import Avatar from "@mui/material/Avatar";
import { loginRequest } from "~/auth/authConfig";

export function LogInOutButton() {
	const { instance } = useMsal();

	/*
  Currently not working without the right setup for Microsoft Graph, but
  would fetch the user's profile photo from Microsoft Graph AP
     Add the following after the button within the AuthenticatedTemplate:
     {avatarUrl && (
      <Avatar
        src={avatarUrl}
        alt="User Avatar"
        sx={{ width: 32, height: 32 }}
      />
    )}
  */
	/*
  const [avatarUrl, setAvatarUrl] = React.useState<string | null>(null);
	React.useEffect(() => {
		async function fetchProfilePhoto() {
			if (accounts?.[0]) {
				try {
					const response = await instance
						.acquireTokenSilent({ ...loginRequest, account: accounts[0] })
						.catch((e) => null);
					if (response) {
						const graphResponse = await fetch(
							"https://graph.microsoft.com/v1.0/me/photo/$value",
							{
								headers: { Authorization: `Bearer ${response.accessToken}` },
							},
						);
						if (graphResponse.ok) {
							const blob = await graphResponse.blob();
							setAvatarUrl(URL.createObjectURL(blob));
						} else {
							setAvatarUrl(null);
						}
					}
				} catch {
					setAvatarUrl(null);
				}
			}
		}
		fetchProfilePhoto();
	}, [instance, accounts]);
  */

	const handleLoginRedirect = () => {
		instance.loginRedirect(loginRequest).catch((error) => console.log(error));
	};

	const handleLogoutRedirect = () => {
		instance.logoutRedirect().catch((error) => console.log(error));
	};

	return (
		<>
			<AuthenticatedTemplate>
				<Button
					variant="text"
					sx={{ color: "primary.light" }}
					onClick={handleLogoutRedirect}
				>
					Sign out
				</Button>
				<Avatar alt="Alice User">AU</Avatar>
			</AuthenticatedTemplate>
			<UnauthenticatedTemplate>
				{/* <Button onClick={handleLoginRedirect}>Sign in</Button> */}
			</UnauthenticatedTemplate>
		</>
	);
}
