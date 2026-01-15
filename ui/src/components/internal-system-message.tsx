import type { Message } from "@/api/chat";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import { Separator } from "./ui/separator";

type Props = {
  label: string;
  data: Message;
};

export const InternalSystemMessage = ({ label, data }: Props) => {
  return (
    <>
      <Accordion
        type="single"
        collapsible
        className="bg-secondary px-4 markdown text rounded-t-2xl border border-b-0"
      >
        <AccordionItem value="item-1">
          <AccordionTrigger>{label}</AccordionTrigger>
          <AccordionContent>
            <ReactMarkdown remarkPlugins={[remarkBreaks]}>
              {data.content as string}
            </ReactMarkdown>
          </AccordionContent>
          <Separator />
        </AccordionItem>
      </Accordion>
    </>
  );
};
