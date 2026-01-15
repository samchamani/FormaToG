import { isModelInput, type Message } from "@/ChatContext";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "./ui/accordion";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";

type Props = {
  data: Message;
};

export const InternalUserMessage = ({ data }: Props) => {
  if (!isModelInput(data.content, data.role)) return null;
  return (
    <Accordion
      type="single"
      collapsible
      className="bg-secondary px-4 markdown text border-x"
    >
      <AccordionItem value="item-1">
        <AccordionTrigger>{"Input data"}</AccordionTrigger>
        <AccordionContent>
          <ReactMarkdown remarkPlugins={[remarkBreaks]}>
            {data.content.pretext}
          </ReactMarkdown>
          {data.content.data.length > 1 && (
            <Table className="mt-4">
              <TableHeader>
                <TableRow>
                  {data.content.data[0].map((cell, index) => (
                    <TableHead className="font-bold" key={index}>
                      {cell.replace(":", "").toLowerCase()}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.content.data.slice(1).map((row, index) => (
                  <TableRow key={index}>
                    {row.map((cell, rowIndex) => (
                      <TableCell
                        title={cell}
                        className={`max-w-0 truncate`}
                        key={rowIndex}
                      >
                        {cell}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};
