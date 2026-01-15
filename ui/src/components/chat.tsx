import { cn } from "@/lib/utils";
import { ChatMessage } from "./chat-message";
import { Button } from "./ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Input } from "./ui/input";
import { useEffect, useState } from "react";
import { isFinal, useChatAPI, type Message } from "@/ChatContext";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { ThinkMessage } from "./think-message";
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "./ui/empty";
import { BadgeX } from "lucide-react";

type Props = {
  className?: string;
};

export const Chat = ({ className }: Props) => {
  const { data, loading, error, sendPrompt } = useChatAPI();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [prompt, setPrompt] = useState("");

  const handleSubmit = () => {
    setHistory((prev) => [
      ...prev,
      { isUser: true, content: prompt, type: "chat" },
    ]);
    sendPrompt(prompt);
    setPrompt("");
  };

  useEffect(() => {
    if (!data.length) return;
    setHistory((prev) => {
      let newHistory = [...prev];
      if (newHistory.length && newHistory.slice(-1)[0].type === "thinking") {
        newHistory = newHistory.slice(0, -1);
      }

      let answer: HistoryItem[] = [];
      const lastDataMessage = data.slice(-1)[0];
      if (
        lastDataMessage.instruction === "final" &&
        isFinal(lastDataMessage.content, lastDataMessage.instruction)
      ) {
        answer.push({
          content: lastDataMessage.content.user_answer,
          type: "chat",
        });
      }
      return [
        ...newHistory,
        { content: "", data: structuredClone(data), type: "thinking" },
        ...answer,
      ];
    });
  }, [data, data.length]);

  useEffect(() => {
    if (!error) return;
    setHistory((prev) => [...prev, { content: error, type: "error" }]);
  }, [error]);

  return (
    <Card
      className={cn(
        "bg-card/80 backdrop-blur-sm h-full min-h-0 flex flex-col",
        "relative left-1/2 -translate-x-1/2 transition-all duration-500",
        className,
        (history.length >= 3 || data.length >= 5) && "left-0 translate-x-0"
      )}
    >
      <CardHeader>
        <CardTitle>FormaToG Chat</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col grow gap-4 overflow-auto">
        {history.map((item, index) => {
          if (item.type === "chat")
            return (
              <ChatMessage
                key={index}
                content={item.content}
                isUser={!!item.isUser}
              />
            );
          if (item.type === "error")
            return (
              <Alert
                key={index}
                className="bg-red-500/10 text-red-500"
                variant="destructive"
              >
                <BadgeX />
                <AlertTitle>{"An error occured."}</AlertTitle>
                <AlertDescription>{item.content}</AlertDescription>
              </Alert>
            );
          if (item.type === "thinking")
            return <ThinkMessage key={index} data={item.data || []} />;
          return null;
        })}
        {!history.length && (
          <Empty>
            <EmptyHeader>
              <EmptyTitle>Hello</EmptyTitle>
              <EmptyDescription>
                Write a message to make the AI think on a graph
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </CardContent>
      <CardFooter>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="flex gap-2 w-full"
        >
          <Input
            placeholder="Your question right here..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={loading}
          />
          <Button
            className="cursor-pointer"
            disabled={loading || !prompt}
            type="submit"
          >
            Send
          </Button>
        </form>
      </CardFooter>
    </Card>
  );
};

type HistoryItem = {
  isUser?: boolean;
  content: string;
  data?: Message[];
  type: "error" | "chat" | "thinking";
};
