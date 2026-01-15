import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion";
import { cn } from "@/lib/utils";

import { InternalSystemMessage } from "./internal-system-message";
import {
  InternalAssistantMessage,
  InternalAssistantMessagePlaceholder,
} from "./internal-assistant-message";
import { InternalUserMessage } from "./internal-user-message";
import type { Message } from "@/api/chat";

type Props = {
  data: Message[];
  stopLoading?: boolean;
};

const InstructionMap: Record<Message["instruction"], string> = {
  answer: "Failed using graph - using only LLM to answer",
  reflect: "Reasoning over paths",
  final: "Finished thinking process",
  pick_relationships: "Exploring relationships",
  pick_seed_entities: "Choosing initial exploration items",
  pick_triplets: "Exploring graph triplets",
  retrieve_queries: "Initiating thinking process",
};

export const ThinkMessage = ({ data, stopLoading = false }: Props) => {
  if (!data.length) return null;

  const lastItem = data.slice(-1)[0];
  const depth =
    data.filter(
      (d) => d.instruction === "pick_relationships" && d.role === "system"
    ).length || 1;
  const depthText = ["pick_relationships", "pick_triplets", "reflect"].some(
    (i) => i === lastItem.instruction
  )
    ? ` at depth ${depth}`
    : "";

  return (
    <Accordion type="single" collapsible className="px-2">
      <AccordionItem value="thinking-process">
        <AccordionTrigger
          className={cn(
            "flex-row-reverse justify-end text-foreground/30 cursor-pointer",
            lastItem.instruction !== "final" && !stopLoading && "animate-pulse"
          )}
        >
          {InstructionMap[lastItem.instruction] + depthText}
        </AccordionTrigger>
        <AccordionContent className="overflow-auto">
          {data.map((item, index) => (
            <div key={index} className="px-8">
              {item.instruction === "final" && (
                <h2 className="font-bold mt-4 mb-2 pl-4">Final Output</h2>
              )}
              {item.role === "system" && (
                <InternalSystemMessage
                  key={index}
                  label={InstructionMap[item.instruction]}
                  data={item}
                />
              )}
              {item.role === "user" && (
                <InternalUserMessage key={index} data={item} />
              )}
              {item.role === "assistant" && (
                <InternalAssistantMessage key={index} data={data} at={index} />
              )}
            </div>
          ))}
          {lastItem.role === "user" && (
            <InternalAssistantMessagePlaceholder isLoading={!stopLoading} />
          )}
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};
