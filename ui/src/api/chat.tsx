import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import Papa from "papaparse";

interface ChatContextType {
  data: Message[];
  loading: boolean;
  error: string | null;
  sendPrompt: (prompt: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendPrompt = useCallback((prompt: string) => {
    setLoading(true);
    setError(null);
    setData([]);

    const source = new EventSource(
      `${import.meta.env.VITE_SERVER_URL}/chat?prompt=${encodeURIComponent(
        prompt
      )}`
    );

    source.onmessage = function (event) {
      if (event.data.includes("[DONE]")) {
        source.close();
        setLoading(false);
        return;
      }

      try {
        const parsed: Message = JSON.parse(event.data);
        if (parsed.role === "assistant" && typeof parsed.content === "string") {
          parsed.content = JSON.parse(parsed.content);
        }
        if (parsed.role === "user" && typeof parsed.content === "string") {
          parsed.content = parseUserMessage(parsed);
        }
        if (parsed.role === "system" && typeof parsed.content === "string") {
          parsed.content = parsed.content.replace("### Real Data ###", "");
        }

        setData((prev) => [...prev, parsed]);
      } catch (e) {
        console.warn("Parsing error:", event.data);
      }
    };

    source.onerror = function (err) {
      console.error("EventSource failed:", err);
      setError("data" in err ? `${err.data}` : "Connection failed");
      setLoading(false);
      source.close();
    };

    return () => {
      source.close();
    };
  }, []);

  const value = {
    data,
    loading,
    error,
    sendPrompt,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChatAPI() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}

function parseUserMessage(obj: Message): ModelInput {
  if (typeof obj.content !== "string")
    return { pretext: `${obj.content}`, data: [], posttext: "" };
  let dataHead = "";
  const dataEnd = "AGENT RESPONSE:";
  if (obj.instruction === "pick_seed_entities") dataHead = "ENTITIES:";
  if (obj.instruction === "pick_relationships")
    dataHead = "ENTITY,RELATIONSHIP";
  if (obj.instruction === "pick_triplets" || obj.instruction === "reflect")
    dataHead = "HEAD_ENTITY,RELATIONSHIP,TAIL_ENTITY";
  if (dataHead === "")
    return {
      pretext: obj.content.replace(dataEnd, "").trim(),
      data: [],
      posttext: "",
    };

  const start = obj.content.indexOf(dataHead);
  const end = obj.content.indexOf(dataEnd);
  const text = obj.content.substring(start, end).trim();

  return {
    pretext: obj.content.substring(0, start).trim(),
    data: Papa.parse(text).data as string[][],
    posttext: obj.content.substring(end).trim(),
  };
}

export type Message = {
  role: "user" | "assistant" | "system";
  content:
    | string
    | RetrieveQueries
    | PickSeedEntities
    | PickRelationship
    | PickTriplets
    | Reflect
    | Answer
    | Final
    | ModelInput;
  instruction:
    | "retrieve_queries"
    | "pick_seed_entities"
    | "pick_relationships"
    | "pick_triplets"
    | "reflect"
    | "answer"
    | "final";
};

type RetrieveQueries = {
  queries: string[];
};

type PickSeedEntities = {
  seed_entities: string[];
  reason: string;
};

type PickRelationship = {
  selection: { entity: string; relationship: string }[];
  reason: string;
};

type PickTriplets = {
  selection: { head: string; relationship: string; tail: string }[];
  reason: string;
};

type Reflect = {
  found_knowledge: boolean;
  machine_answer: string;
  user_answer: string;
  reason: string;
};

type Answer = {
  machine_answer: string;
  user_answer: string;
};

type Final = {
  machine_answer: string;
  user_answer: string;
  is_kg_based_answer: boolean;
  kg_calls: number;
  agent_calls: number;
  depth: number;
  has_err_instruction: boolean;
  has_err_format: boolean;
  has_err_graph: boolean;
  has_err_agent: boolean;
  has_err_other: boolean;
};

type ModelInput = {
  pretext: string;
  data: string[][];
  posttext: string;
};

export function isRetrieveQueries(
  _obj: Message["content"],
  instruction: Message["instruction"]
): _obj is RetrieveQueries {
  return instruction === "retrieve_queries";
}
export function isPickSeedEntities(
  _obj: Message["content"],
  instruction: Message["instruction"]
): _obj is PickSeedEntities {
  return instruction === "pick_seed_entities";
}
export function isPickRelationship(
  _obj: Message["content"],
  instruction: Message["instruction"]
): _obj is PickRelationship {
  return instruction === "pick_relationships";
}
export function isPickTriplets(
  _obj: Message["content"],
  instruction: Message["instruction"]
): _obj is PickTriplets {
  return instruction === "pick_triplets";
}
export function isReflect(
  _obj: Message["content"],
  instruction: Message["instruction"]
): _obj is Reflect {
  return instruction === "reflect";
}
export function isAnswer(
  _obj: Message["content"],
  instruction: Message["instruction"]
): _obj is Answer {
  return instruction === "answer";
}
export function isFinal(
  _obj: Message["content"],
  instruction: Message["instruction"]
): _obj is Final {
  return instruction === "final";
}
export function isModelInput(
  _obj: Message["content"],
  role: Message["role"]
): _obj is ModelInput {
  return role === "user";
}
