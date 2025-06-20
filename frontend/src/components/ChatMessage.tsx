import {
  User,
  Bot,
  Copy,
  ThumbsUp,
  ThumbsDown,
  MoreHorizontal,
  TrendingUp,
  TrendingDown,
  DollarSign,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ChatMessageProps {
  message: {
    id: string;
    type: "user" | "assistant";
    content: string;
    timestamp?: string;
  };
}

// Helper function to format crypto content with better styling
function formatCryptoContent(content: string): JSX.Element {
  // Check if content contains crypto analysis patterns
  const isCryptoAnalysis = content.includes("**Estimated Price:**") || 
                          content.includes("**Prediction Score:**") ||
                          content.includes("**Sentiment Score:**");

  if (!isCryptoAnalysis) {
    return <div className="text-white text-sm leading-relaxed whitespace-pre-wrap">{content}</div>;
  }

  // Split content into sections
  const sections = content.split('\n\n');
  
  return (
    <div className="space-y-4">
      {sections.map((section, index) => {
        // Handle crypto coin headers
        if (section.startsWith('**') && section.endsWith('**') && section.includes('(')) {
          const coinName = section.replace(/\*\*/g, '');
          return (
            <div key={index} className="flex items-center gap-2 pb-2 border-b border-gray-600">
              <DollarSign className="w-5 h-5 text-yellow-400" />
              <h3 className="text-lg font-semibold text-white">{coinName}</h3>
            </div>
          );
        }

        // Handle price information
        if (section.includes('**Estimated Price:**')) {
          const priceMatch = section.match(/\*\*Estimated Price:\*\* ([\d.]+)/);
          const price = priceMatch ? priceMatch[1] : '';
          return (
            <div key={index} className="bg-green-900/30 p-3 rounded-lg border border-green-700">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-400" />
                <span className="text-green-400 font-medium">Estimated Price</span>
              </div>
              <div className="text-2xl font-bold text-white mt-1">${price}</div>
            </div>
          );
        }

        // Handle scores with color coding
        if (section.includes('**Prediction Score:**') || 
            section.includes('**Sentiment Score:**') || 
            section.includes('**Total Score:**')) {
          
          const lines = section.split('\n');
          return (
            <div key={index} className="space-y-2">
              {lines.map((line, lineIndex) => {
                if (line.includes('**') && line.includes('Score:**')) {
                  const scoreMatch = line.match(/\*\*(.+?):\*\* (.+)/);
                  if (scoreMatch) {
                    const [, label, value] = scoreMatch;
                    const numericScore = parseFloat(value);
                    
                    let badgeColor = "bg-gray-600";
                    let textColor = "text-gray-300";
                    
                    if (!isNaN(numericScore)) {
                      if (numericScore >= 7) {
                        badgeColor = "bg-green-600";
                        textColor = "text-green-400";
                      } else if (numericScore >= 4) {
                        badgeColor = "bg-yellow-600";
                        textColor = "text-yellow-400";
                      } else {
                        badgeColor = "bg-red-600";
                        textColor = "text-red-400";
                      }
                    }

                    return (
                      <div key={lineIndex} className="flex items-center justify-between py-2">
                        <span className="text-gray-300">{label}</span>
                        <Badge className={`${badgeColor} ${textColor}`}>
                          {value}
                        </Badge>
                      </div>
                    );
                  }
                }
                return null;
              })}
            </div>
          );
        }

        // Handle comparison sections
        if (section.includes('**Comparison:**')) {
          return (
            <div key={index} className="bg-blue-900/30 p-3 rounded-lg border border-blue-700">
              <h4 className="text-blue-400 font-medium mb-2 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Comparison Analysis
              </h4>
              <div className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                {section.replace('**Comparison:**\n', '')}
              </div>
            </div>
          );
        }

        // Handle regular text sections
        if (section.trim()) {
          return (
            <div key={index} className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
              {section.replace(/\*\*(.+?)\*\*/g, '<strong class="text-white">$1</strong>')
                     .split('<strong class="text-white">').map((part, i) => {
                       if (i === 0) return part;
                       const [bold, rest] = part.split('</strong>');
                       return (
                         <span key={i}>
                           <strong className="text-white">{bold}</strong>
                           {rest}
                         </span>
                       );
                     })}
            </div>
          );
        }

        return null;
      })}
    </div>
  );
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.type === "user";

  return (
    <div
      className={`group relative px-6 py-6 ${isUser ? "bg-transparent" : "bg-[#2d2d2d]"}`}
    >
      <div className="max-w-4xl mx-auto flex gap-4">
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser ? "bg-blue-600" : "bg-gradient-to-r from-green-500 to-blue-500"
          }`}
        >
          {isUser ? (
            <User className="w-4 h-4 text-white" />
          ) : (
            <Bot className="w-4 h-4 text-white" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-3">
            <span className="text-white font-medium text-sm">
              {isUser ? "You" : "🚀 Crypto Assistant"}
            </span>
            {message.timestamp && (
              <span className="text-gray-500 text-xs">{message.timestamp}</span>
            )}
          </div>

          {/* Enhanced content formatting */}
          {isUser ? (
            <div className="text-white text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </div>
          ) : (
            formatCryptoContent(message.content)
          )}

          {/* Action buttons for assistant messages */}
          {!isUser && (
            <div className="flex items-center gap-2 mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white hover:bg-gray-600"
                onClick={() => navigator.clipboard.writeText(message.content)}
              >
                <Copy className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white hover:bg-gray-600"
              >
                <ThumbsUp className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white hover:bg-gray-600"
              >
                <ThumbsDown className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white hover:bg-gray-600"
              >
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
