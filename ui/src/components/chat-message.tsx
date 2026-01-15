import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { Bot, User } from "lucide-react";

type Props = {
  content: string;
  isUser: boolean;
};

export const ChatMessage = ({ content, isUser }: Props) => {
  return (
    <div
      className={cn(
        "flex gap-2 max-w-3/4",
        isUser && "self-end flex-row-reverse"
      )}
    >
      <Avatar>
        <AvatarFallback className="p-1.5">
          {isUser ? <User /> : <Bot />}
        </AvatarFallback>
      </Avatar>
      <div
        className={cn(
          "relative py-2 px-4 bg-secondary w-max rounded-2xl hyphens-auto wrap-break-words",
          isUser ? "rounded-tr-none text-right" : "rounded-tl-none text-left"
        )}
      >
        {content}
      </div>
    </div>
  );
};
