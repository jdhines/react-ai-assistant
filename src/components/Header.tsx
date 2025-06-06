import { Expand, Shrink } from "lucide-react";
import { LogInOutButton } from "./LogInOutButton";

interface HeaderProps {
	expanded: boolean;
	toggleExpand: () => void;
}

export function Header({ expanded, toggleExpand }: HeaderProps) {
	return (
		<header className="flex gap-9 p-4 bg-blue-800 justify-between items-center">
			<div className="max-w-[100vw]">
				<img
					src="/HQ-icon.svg"
					alt="HQ Icon"
					className="h-8 w-8 inline-block"
				/>
				<span className="text-white">HQ Assistant</span>
			</div>

			<div id="header-actions" className="flex gap-4">
				<LogInOutButton />
				<button
					className="hover:bg-blue-700 p-1 rounded"
					onClick={toggleExpand}
					title={expanded ? "Collapse" : "Expand"}
					type="button"
				>
					<span className="text-white cursor-pointer">
						{expanded ? <Shrink /> : <Expand />}
					</span>
				</button>
			</div>
		</header>
	);
}
