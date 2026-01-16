import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { User } from "lucide-react";

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
      <Avatar className="h-9 w-9">
        {!isUser ? (
          <AvatarImage className="bg-secondary p-1" src="./logo.svg" />
        ) : (
          <AvatarFallback className="p-2">
            <User />
          </AvatarFallback>
        )}
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
