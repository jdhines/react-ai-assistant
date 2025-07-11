# Live Agent Handoff Implementation Guide for CopilotKit

This document provides a complete implementation for adding live agent handoff functionality to your CopilotKit chat application.

## Overview

This implementation allows users to seamlessly transition from AI chat to live agent chat and back, using CopilotKit's tool system to trigger handoffs.

## 1. Add Handoff State Management

Create or update your ChatProvider to handle handoff states:

```typescript
// filepath: c:\Users\jesshines\dev\HQ-Assistant\client\src\providers\ChatProvider.tsx
import React from "react";
import { useCopilotChat } from "@copilotkit/react-core";
import type { Message } from "@copilotkit/runtime-client-gql";

type HandoffStatus = 'ai' | 'requesting' | 'live' | 'transferring';

type ChatContextType = {
    visibleMessages: Message[];
    isLoading: boolean;
    handoffStatus: HandoffStatus;
    requestHandoff: () => void;
    endHandoff: () => void;
};

export const ChatContext = React.createContext<ChatContextType | null>(null);

function ChatProvider({ children }: { children: React.ReactNode }) {
    const [handoffStatus, setHandoffStatus] = React.useState<HandoffStatus>('ai');

    // Use CopilotKit's chat management
    const {
        visibleMessages,
        isLoading,
    } = useCopilotChat();

    const requestHandoff = React.useCallback(() => {
        setHandoffStatus('requesting');
        // Add system message to indicate handoff request
        // This will be handled by your backend
    }, []);

    const endHandoff = React.useCallback(() => {
        setHandoffStatus('transferring');
        // Add system message to indicate return to AI
        setTimeout(() => setHandoffStatus('ai'), 1000);
    }, []);

    return (
        <ChatContext.Provider
            value={{
                visibleMessages,
                isLoading,
                handoffStatus,
                requestHandoff,
                endHandoff
            }}
        >
            {children}
        </ChatContext.Provider>
    );
}

export default ChatProvider;
```

## 2. Update the Chat Hook

```typescript
// filepath: c:\Users\jesshines\dev\HQ-Assistant\client\src\hooks\useChatMessage.ts
import React from "react";
import { ChatContext } from "../providers/ChatProvider";

export function useChatMessages() {
    const context = React.useContext(ChatContext);
    if (!context) {
        throw new Error("useChatMessages must be used within a ChatProvider");
    }
    const {
        visibleMessages,
        isLoading,
        handoffStatus,
        requestHandoff,
        endHandoff,
    } = context;
    return {
        visibleMessages,
        isLoading,
        handoffStatus,
        requestHandoff,
        endHandoff,
    };
}
```

## 3. Add Handoff Tool to LangGraph Agent

```python
# filepath: c:\Users\jesshines\dev\HQ-Assistant\backend\lang-graph-service\sample_agent\agent.py
# ...existing code...

@tool
def request_live_agent(reason: str = "User requested human assistance"):
    """
    Request to handoff the conversation to a live human agent.

    Args:
        reason: The reason for requesting human assistance
    """
    print(f"Live agent requested: {reason}")
    return {
        "type": "handoff_request",
        "reason": reason,
        "status": "pending"
    }

# ...existing code...

tools = [
    get_weather,
    request_live_agent
    # your_tool_here
]

# ...existing code...

async def chat_node(state: AgentState, config: RunnableConfig) -> Command[Literal["tool_node", "__end__"]]:
    # ...existing code...

    model_with_tools = model.bind_tools(
        [
            *state["copilotkit"]["actions"],
            get_weather,
            request_live_agent,
            # your_tool_here
        ],
        parallel_tool_calls=False,
    )

    # 3. Define the system message by which the chat model will be run
    system_message = SystemMessage(
        content=f"""You are a helpful assistant. Talk in {state.get('language', 'english')}.

        If a user asks to speak with a human, live agent, or human representative,
        use the request_live_agent tool to initiate the handoff process.

        Be helpful and try to resolve issues yourself first, but respect user preferences
        for human assistance."""
    )

    # ...existing code...
```

## 4. Create Live Chat Component

```typescript
// filepath: c:\Users\jesshines\dev\HQ-Assistant\client\src\components\LiveChatInterface.tsx
import React from 'react';

interface LiveChatInterfaceProps {
  onEndHandoff: () => void;
  messages: any[];
}

export function LiveChatInterface({ onEndHandoff, messages }: LiveChatInterfaceProps) {
  const [liveMessages, setLiveMessages] = React.useState<string[]>([]);
  const [currentMessage, setCurrentMessage] = React.useState('');

  // Simulate live agent connection (replace with actual WebSocket/service)
  React.useEffect(() => {
    // Add initial agent message
    setLiveMessages(['Hi! I\'m a live agent. How can I help you today?']);
  }, []);

  const sendMessage = () => {
    if (!currentMessage.trim()) return;

    setLiveMessages(prev => [...prev, `You: ${currentMessage}`]);

    // Simulate agent response (replace with actual live chat service)
    setTimeout(() => {
      setLiveMessages(prev => [...prev, `Agent: Thanks for your message. I'm looking into this for you.`]);
    }, 1000);

    setCurrentMessage('');
  };

  return (
    <div className="flex flex-col h-full">
      <div className="bg-green-100 p-3 border-b">
        <div className="flex justify-between items-center">
          <span className="text-green-800 font-medium">🟢 Connected to Live Agent</span>
          <button
            onClick={onEndHandoff}
            className="text-red-600 hover:text-red-800 px-3 py-1 border border-red-300 rounded"
          >
            End Live Chat
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {liveMessages.map((msg, idx) => (
          <div key={idx} className="p-2 bg-gray-100 rounded">
            {msg}
          </div>
        ))}
      </div>

      <div className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type your message..."
            className="flex-1 p-2 border rounded"
          />
          <button
            onClick={sendMessage}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
```

## 5. Update Chat Page with Handoff Logic

```typescript
// filepath: c:\Users\jesshines\dev\HQ-Assistant\client\src\pages\chat.tsx
import { ChatHeader } from "~/components/ChatHeader";
import { CopilotChat } from '@copilotkit/react-ui'
import { useCopilotChat } from "@copilotkit/react-core";
import { useChatMessages } from "~/hooks/useChatMessage";
import { LiveChatInterface } from "~/components/LiveChatInterface";
import { isAdaptiveCardMessage } from "~/types/ChatMessageProps";
import { renderTextMessage } from "~/utils/renderTextMessage";
import React from "react";

export function ChatPage() {
    const { reset, visibleMessages } = useCopilotChat();
    const { handoffStatus, requestHandoff, endHandoff } = useChatMessages();

    //TODO: remove this logging when no longer needed
    React.useEffect(() => {
        console.log("Visible messages:", visibleMessages);
        console.log("Handoff status:", handoffStatus);
    }, [visibleMessages, handoffStatus]);

    // Check for handoff requests in messages
    React.useEffect(() => {
        const lastMessage = visibleMessages[visibleMessages.length - 1];
        if (lastMessage?.content && typeof lastMessage.content === 'string') {
            if (lastMessage.content.includes('"type": "handoff_request"')) {
                requestHandoff();
            }
        }
    }, [visibleMessages, requestHandoff]);

    const hasAdaptiveCards = visibleMessages.some((msg: any) => isAdaptiveCardMessage(msg.content))

    // Render live chat interface when in live mode
    if (handoffStatus === 'live') {
        return (
            <div id="chat-page" className="h-[100vh] overflow-hidden flex flex-col flex-1 bg-white">
                <ChatHeader onNewChat={reset} />
                <LiveChatInterface onEndHandoff={endHandoff} messages={visibleMessages} />
            </div>
        );
    }

    // Show transition states
    if (handoffStatus === 'requesting') {
        return (
            <div id="chat-page" className="h-[100vh] overflow-hidden flex flex-col flex-1 bg-white">
                <ChatHeader onNewChat={reset} />
                <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                        <p>Connecting you to a live agent...</p>
                        <button
                            onClick={() => window.location.reload()}
                            className="mt-4 text-blue-500 underline"
                        >
                            Cancel and return to AI
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div id="chat-page" className="h-[100vh] overflow-hidden flex flex-col flex-1 bg-white">
            <ChatHeader onNewChat={reset} />

            {handoffStatus === 'transferring' && (
                <div className="bg-blue-100 p-3 text-blue-800 text-center">
                    Transferring back to AI assistant...
                </div>
            )}

            <CopilotChat
                instructions={"You are assisting the user as best as you can. Answer in the best way possible given the data you have. If the user asks to speak with a human or live agent, use the request_live_agent tool."}
                labels={{
                    title: "Sidebar Assistant",
                    initial: "How can I help you today?",
                    // ...existing labels...
                }}
                // ...existing props...
            />
        </div>
    );
}
```

## Key Features

1. **Seamless Transition**: The handoff is triggered by the AI agent using the `request_live_agent` tool
2. **State Management**: Clear states for AI, requesting, live, and transferring back
3. **User Control**: Users can end the live chat and return to AI
4. **Extensible**: Easy to integrate with actual live chat services (Zendesk, Intercom, etc.)

## Implementation States

- `ai`: Normal AI chat mode
- `requesting`: User requested handoff, showing loading state
- `live`: Connected to live agent
- `transferring`: Transitioning back to AI

## Next Steps

1. **Integrate Real Live Chat Service**: Replace the simulated `LiveChatInterface` with actual WebSocket connections to your live chat provider
2. **Add Agent Availability**: Check if live agents are available before handoff
3. **Conversation History**: Ensure conversation context is passed to live agents
4. **Analytics**: Track handoff rates and reasons for continuous improvement

## Usage

Users can trigger handoff by saying things like:
- "I want to speak with a human"
- "Can I talk to a live agent?"
- "Transfer me to a person"

The AI will automatically use the `request_live_agent` tool to initiate the handoff process.