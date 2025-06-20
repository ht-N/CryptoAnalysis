import React, { createContext, useContext, useState, useEffect } from 'react';

export interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

interface ChatContextType {
  chats: Chat[];
  activeChat: Chat | null;
  createNewChat: () => string;
  switchToChat: (chatId: string) => void;
  addMessageToChat: (chatId: string, message: Message) => void;
  updateChatTitle: (chatId: string, title: string) => void;
  deleteChat: (chatId: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function useChatContext() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}

// Helper function to generate chat title from first message
function generateChatTitle(firstMessage: string): string {
  const words = firstMessage.split(' ').slice(0, 4);
  return words.join(' ') + (words.length < firstMessage.split(' ').length ? '...' : '');
}

// Helper function to save to localStorage
function saveChatsToStorage(chats: Chat[]) {
  try {
    localStorage.setItem('crypto-chats', JSON.stringify(chats));
  } catch (error) {
    console.error('Failed to save chats to localStorage:', error);
  }
}

// Helper function to load from localStorage
function loadChatsFromStorage(): Chat[] {
  try {
    const saved = localStorage.getItem('crypto-chats');
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (error) {
    console.error('Failed to load chats from localStorage:', error);
  }
  return [];
}

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<Chat | null>(null);

  // Load chats from localStorage on mount
  useEffect(() => {
    const savedChats = loadChatsFromStorage();
    if (savedChats.length > 0) {
      setChats(savedChats);
      // Set the most recent chat as active
      const mostRecent = savedChats.sort((a, b) => 
        new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      )[0];
      setActiveChat(mostRecent);
    } else {
      // Create initial chat if no saved chats
      const initialChatId = createInitialChat();
      if (initialChatId) {
        const newChat = chats.find(c => c.id === initialChatId);
        if (newChat) setActiveChat(newChat);
      }
    }
  }, []);

  // Save to localStorage whenever chats change
  useEffect(() => {
    if (chats.length > 0) {
      saveChatsToStorage(chats);
    }
  }, [chats]);

  function createInitialChat(): string {
    const now = new Date().toISOString();
    const initialMessages: Message[] = [
      {
        id: "1",
        type: "user",
        content: "Chào bạn! Tôi muốn tìm hiểu về crypto.",
        timestamp: "9:12 PM",
      },
      {
        id: "2",
        type: "assistant",
        content: "Chào bạn! Tôi là trợ lý phân tích cryptocurrency. Tôi có thể giúp bạn:\n\n• Kiểm tra giá hiện tại và dự báo giá các đồng coin\n• Phân tích xu hướng và tỷ lệ tăng trưởng\n• Đưa ra khuyến nghị đầu tư dựa trên AI\n• So sánh các loại cryptocurrency\n\nHãy hỏi tôi bất kỳ câu hỏi nào về crypto!",
        timestamp: "9:12 PM",
      },
    ];

    const newChat: Chat = {
      id: `chat-${Date.now()}`,
      title: "🚀 Crypto Analysis Welcome",
      messages: initialMessages,
      createdAt: now,
      updatedAt: now,
    };

    setChats([newChat]);
    return newChat.id;
  }

  function createNewChat(): string {
    const now = new Date().toISOString();
    const newChat: Chat = {
      id: `chat-${Date.now()}`,
      title: "New Chat",
      messages: [],
      createdAt: now,
      updatedAt: now,
    };

    setChats(prev => [newChat, ...prev]);
    setActiveChat(newChat);
    return newChat.id;
  }

  function switchToChat(chatId: string) {
    const chat = chats.find(c => c.id === chatId);
    if (chat) {
      setActiveChat(chat);
    }
  }

  function addMessageToChat(chatId: string, message: Message) {
    setChats(prev => prev.map(chat => {
      if (chat.id === chatId) {
        const updatedChat = {
          ...chat,
          messages: [...chat.messages, message],
          updatedAt: new Date().toISOString(),
        };

        // Auto-update title based on first user message
        if (chat.title === "New Chat" && message.type === "user" && chat.messages.length === 0) {
          updatedChat.title = generateChatTitle(message.content);
        }

        // Update active chat if it's the current one
        if (activeChat?.id === chatId) {
          setActiveChat(updatedChat);
        }

        return updatedChat;
      }
      return chat;
    }));
  }

  function updateChatTitle(chatId: string, title: string) {
    setChats(prev => prev.map(chat => 
      chat.id === chatId 
        ? { ...chat, title, updatedAt: new Date().toISOString() }
        : chat
    ));

    if (activeChat?.id === chatId) {
      setActiveChat(prev => prev ? { ...prev, title } : null);
    }
  }

  function deleteChat(chatId: string) {
    setChats(prev => {
      const filtered = prev.filter(c => c.id !== chatId);
      
      // If deleting active chat, switch to most recent
      if (activeChat?.id === chatId) {
        if (filtered.length > 0) {
          const mostRecent = filtered.sort((a, b) => 
            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
          )[0];
          setActiveChat(mostRecent);
        } else {
          // Create new chat if all deleted
          const newChatId = createNewChat();
          return prev; // createNewChat will handle state update
        }
      }
      
      return filtered;
    });
  }

  return (
    <ChatContext.Provider value={{
      chats,
      activeChat,
      createNewChat,
      switchToChat,
      addMessageToChat,
      updateChatTitle,
      deleteChat,
    }}>
      {children}
    </ChatContext.Provider>
  );
}
