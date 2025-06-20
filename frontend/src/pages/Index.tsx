import { ChatSidebar } from "@/components/ChatSidebar";
import { ChatMain } from "@/components/ChatMain";

const Index = () => {
  return (
    <div className="h-screen bg-chat-bg overflow-hidden">
      <div className="flex h-full">
        <ChatSidebar />
        <ChatMain />
      </div>
    </div>
  );
};

export default Index;
