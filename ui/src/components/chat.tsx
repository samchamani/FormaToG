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
import { useEffect, useRef, useState } from "react";
import { isFinal, useChatAPI, type Message } from "@/api/chat";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { ThinkMessage } from "./think-message";
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "./ui/empty";
import { BadgeX, MoreVertical, X } from "lucide-react";
import { Settings } from "./settings";

type Props = {
  className?: string;
};

export const Chat = ({ className }: Props) => {
  const { data, loading, error, sendPrompt } = useChatAPI();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [prompt, setPrompt] = useState("");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const scrollAnchor = useRef<HTMLDivElement>(null);

  const hasError = (index: number) =>
    history.some((h, i) => index >= i && h.type === "error");

  const handleSubmit = () => {
    setHistory((prev) => [
      ...prev,
      { isUser: true, content: prompt, type: "chat" },
    ]);
    sendPrompt(prompt);
    setPrompt("");
  };

  const handleSettings = () => {
    setIsSettingsOpen((prev) => !prev);
    setHistory([]);
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

  useEffect(() => {
    if (!scrollAnchor.current) return;
    scrollAnchor.current.scrollIntoView({ behavior: "smooth" });
  }, [history, scrollAnchor.current]);

  return (
    <Card
      className={cn(
        "bg-card/80 backdrop-blur-sm h-full min-h-0 flex flex-col drop-shadow-lg",
        "relative left-1/2 -translate-x-1/2 transition-all duration-500",
        className,
        (history.length >= 3 || data.length >= 5) && "left-0 translate-x-0"
      )}
    >
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          FormaToG
          <Button variant="ghost" size="icon-sm" onClick={handleSettings}>
            {isSettingsOpen ? <X /> : <MoreVertical />}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col grow gap-4 overflow-auto">
        {isSettingsOpen ? (
          <Settings />
        ) : (
          <>
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
                    className="bg-destructive/10 text-destructive"
                    variant="destructive"
                  >
                    <BadgeX />
                    <AlertTitle>{"An error occured."}</AlertTitle>
                    <AlertDescription>{item.content}</AlertDescription>
                  </Alert>
                );
              if (item.type === "thinking")
                return (
                  <ThinkMessage
                    key={index}
                    data={item.data || []}
                    stopLoading={hasError(index)}
                  />
                );
              return null;
            })}
            <div ref={scrollAnchor} />
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
          </>
        )}
      </CardContent>
      {!isSettingsOpen && (
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
      )}
    </Card>
  );
};

type HistoryItem = {
  isUser?: boolean;
  content: string;
  data?: Message[];
  type: "error" | "chat" | "thinking";
};
