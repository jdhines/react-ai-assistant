import React from "react";
import SampleData from "~/utils/adaptive-sample";
import ReactMarkdown from "react-markdown";
import { Send, Bot, User } from 'lucide-react';
import { AdaptiveCard } from '~/components/adaptivecards-react/adaptive-card';

interface ChatMessageProps {
  id: string;
  sender: "user" | "bot";
  text: string;
  timestamp?: Date;
}

interface ChatMessageListProps {
  messages: ChatMessageProps[];
}

export function ChatMessageList({ messages }: ChatMessageListProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4">
      {messages.map((msg) => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
    </div>
  );
}

function ChatMessage({ message }: ChatMessageProps) {
  const { sender, text, timestamp } = message;
  //TODO: Remove example of adaptive card
  const handleError = (error: Error) => {
    console.error("Adaptive Card error:", error);
  };
  const hostConfig = {
    fontFamily: "Segoe UI, Helvetica Neue, sans-serif"
  };
  return (
    <div
      className={`sender === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`flex items-start space-x-2 max-w-2xl ${sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          sender === 'user' ? 'bg-blue-600' : 'bg-gray-600'
        }`}>
          {sender === 'user' ? (
            <User className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-white" />
          )}
        </div>

        {/* Message Content */}
        <div className={`flex flex-col space-y-2 ${sender === 'user' ? 'items-end' : 'items-start'}`}>
          <div className={`rounded-lg px-4 py-2 ${
            sender === 'user'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-800 border border-gray-200'
          }`}>
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>

          {/* Adaptive Card */}
          {(text.includes("Adaptive")) && (
            <div className="w-full">
              <AdaptiveCard payload={SampleData}
                style={{color: 'green'}}
                onError={handleError}
                hostConfig={hostConfig}
                />
            </div>
          )}

          <span className="text-xs text-gray-500">
            {timestamp.toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
}