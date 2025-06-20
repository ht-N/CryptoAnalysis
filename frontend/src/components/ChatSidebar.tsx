import { MessageSquare, Plus, Settings, User, MoreHorizontal, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChatContext } from "@/contexts/ChatContext";
import { useState } from "react";

export function ChatSidebar() {
  const { 
    chats, 
    activeChat, 
    createNewChat, 
    switchToChat, 
    deleteChat 
  } = useChatContext();
  
  const [hoveredChatId, setHoveredChatId] = useState<string | null>(null);

  const handleNewChat = () => {
    createNewChat();
  };

  const handleDeleteChat = (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent chat selection
    if (chats.length > 1) { // Prevent deleting last chat
      deleteChat(chatId);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const getPreviewText = (messages: any[]) => {
    const lastUserMessage = messages.filter(m => m.type === 'user').pop();
    if (lastUserMessage) {
      return lastUserMessage.content.slice(0, 50) + (lastUserMessage.content.length > 50 ? '...' : '');
    }
    return 'No messages yet...';
  };

  return (
    <div className="w-80 bg-[#1a1a1a] h-full flex flex-col border-r border-chat-border">
      {/* Header */}
      <div className="p-4 border-b border-chat-border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-teal-500 rounded-lg flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-white" />
            </div>
            <span className="text-white font-medium">My Chats</span>
          </div>
          <div className="flex space-x-1">
            <Button
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white hover:bg-gray-700"
              onClick={handleNewChat}
            >
              <Plus className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white hover:bg-gray-700"
            >
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <Button 
          className="w-full bg-teal-500 hover:bg-teal-600 text-white rounded-lg"
          onClick={handleNewChat}
        >
          <Plus className="w-4 h-4 mr-2" />
          New Chat
        </Button>
      </div>

      {/* Chat History */}
      <ScrollArea className="flex-1 p-4 chat-scrollbar">
        <div className="space-y-2">
          {chats.length === 0 ? (
            <div className="text-gray-400 text-sm text-center py-8">
              No chats yet. Create your first chat!
            </div>
          ) : (
            chats.map((chat) => (
              <div
                key={chat.id}
                className={`group p-3 rounded-lg hover:bg-gray-700 cursor-pointer transition-colors relative ${
                  activeChat?.id === chat.id ? 'bg-gray-700 border border-teal-500' : ''
                }`}
                onClick={() => switchToChat(chat.id)}
                onMouseEnter={() => setHoveredChatId(chat.id)}
                onMouseLeave={() => setHoveredChatId(null)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 pr-2">
                    <h3 className="text-white text-sm font-medium mb-1 truncate">
                      {chat.title}
                    </h3>
                    <p className="text-gray-400 text-xs line-clamp-2">
                      {getPreviewText(chat.messages)}
                    </p>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      {formatTimestamp(chat.updatedAt)}
                    </span>
                    {(hoveredChatId === chat.id || activeChat?.id === chat.id) && chats.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-gray-400 hover:text-red-400 h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                        onClick={(e) => handleDeleteChat(chat.id, e)}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* User Profile */}
      <div className="p-4 border-t border-chat-border">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1">
            <div className="text-white text-sm font-medium">You</div>
            <div className="text-gray-400 text-xs">Crypto Trader</div>
          </div>
        </div>
      </div>
    </div>
  );
}
