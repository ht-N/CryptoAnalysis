import { useState } from "react";
import { Send, Paperclip, Mic, Loader2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import { askCryptoQuestion } from "@/services/cryptoAPI";
import { useChatContext } from "@/contexts/ChatContext";

export function ChatMain() {
  const { activeChat, addMessageToChat } = useChatContext();
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !activeChat) return;

    const newMessage = {
      id: Date.now().toString(),
      type: "user" as const,
      content: inputValue,
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    // Add user message to active chat
    addMessageToChat(activeChat.id, newMessage);
    const currentQuestion = inputValue;
    setInputValue("");
    setIsLoading(true);

    try {
      // Call real crypto API
      console.log(`[ChatMain] Sending question to API: ${currentQuestion}`);
      const answer = await askCryptoQuestion(currentQuestion);
      
      const aiResponse = {
        id: (Date.now() + 1).toString(),
        type: "assistant" as const,
        content: answer,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      
      // Add AI response to active chat
      addMessageToChat(activeChat.id, aiResponse);
      console.log(`[ChatMain] Received AI response successfully`);
      
    } catch (error) {
      console.error('[ChatMain] Error getting AI response:', error);
      
      // Error message for user
      const errorResponse = {
        id: (Date.now() + 2).toString(),
        type: "assistant" as const,
        content: `❌ **Lỗi kết nối**: ${error instanceof Error ? error.message : 'Không thể kết nối tới server'}\n\n*Vui lòng kiểm tra:*\n• Backend server đã chạy chưa?\n• Kết nối mạng ổn định không?\n• Thử lại sau vài giây`,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      
      addMessageToChat(activeChat.id, errorResponse);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // If no active chat, show loading state
  if (!activeChat) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#494949]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-teal-500 mx-auto mb-4" />
          <p className="text-gray-400">Loading chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-[#494949]">
      {/* Header */}
      <div className="bg-[#2d2d2d] px-6 py-4 border-b border-chat-border">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-white text-lg font-semibold">
            {activeChat.title}
          </h1>
          <div className="flex items-center space-x-2">
            {isLoading && (
              <div className="flex items-center text-blue-400 text-sm">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Analyzing...
              </div>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white hover:bg-gray-600"
            >
              <span className="text-sm">🔍</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white hover:bg-gray-600"
            >
              <span className="text-sm">⋯</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 chat-scrollbar">
        <div className="min-h-full">
          {activeChat.messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center p-8">
                <div className="w-16 h-16 bg-teal-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-white text-lg font-medium mb-2">Start a conversation</h3>
                <p className="text-gray-400 text-sm">Ask me anything about cryptocurrency analysis!</p>
              </div>
            </div>
          ) : (
            activeChat.messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}
          
          {/* Loading indicator in chat area */}
          {isLoading && (
            <div className="flex justify-start px-6 py-4">
              <div className="max-w-4xl w-full">
                <div className="flex items-center space-x-2 text-gray-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">AI đang phân tích câu hỏi của bạn...</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="bg-[#494949] px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <div className="relative bg-[#3a3a3a] rounded-2xl border border-chat-border">
            <Textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Hỏi về giá coin, dự báo, hoặc khuyến nghị đầu tư..."
              disabled={isLoading}
              className="min-h-[60px] bg-transparent border-0 resize-none text-white placeholder:text-gray-400 focus:ring-0 focus:ring-offset-0 text-sm leading-relaxed p-4 pr-16 disabled:opacity-50"
            />

            <div className="absolute bottom-3 right-3 flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white hover:bg-gray-600 h-8 w-8 p-0"
                disabled={isLoading}
              >
                <Paperclip className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white hover:bg-gray-600 h-8 w-8 p-0"
                disabled={isLoading}
              >
                <Mic className="w-4 h-4" />
              </Button>
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                size="sm"
                className="bg-white text-black hover:bg-gray-200 disabled:bg-gray-600 disabled:text-gray-400 h-8 w-8 p-0 rounded-lg"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
