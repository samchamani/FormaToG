import {
  isAnswer,
  isFinal,
  isModelInput,
  isPickRelationship,
  isPickSeedEntities,
  isPickTriplets,
  isReflect,
  isRetrieveQueries,
  type Message,
} from "@/api/chat";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { cn } from "@/lib/utils";
import { useMemo } from "react";
import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";

type Props = {
  data: Message[];
  at: number;
};

const HEADER_MAP: Record<Message["instruction"], string[]> = {
  answer: ["key", "value"],
  final: ["key", "value"],
  pick_relationships: ["entity", "relationship"],
  pick_seed_entities: ["entity"],
  pick_triplets: ["head", "relationship", "entity"],
  reflect: ["key", "value"],
  retrieve_queries: ["queries"],
};

export const InternalAssistantMessage = ({ data, at }: Props) => {
  const current = data[at];
  const reason =
    isPickSeedEntities(current.content, current.instruction) ||
    isPickRelationship(current.content, current.instruction) ||
    isPickTriplets(current.content, current.instruction) ||
    isReflect(current.content, current.instruction)
      ? current.content.reason
      : "";

  const list = useMemo(() => {
    if (isRetrieveQueries(current.content, current.instruction))
      return current.content.queries.map((q) => [q]);
    if (isPickSeedEntities(current.content, current.instruction))
      return current.content.seed_entities.map((e) => [e]);
    if (isPickRelationship(current.content, current.instruction))
      return current.content.selection.map((e) => [e.entity, e.relationship]);
    if (isPickTriplets(current.content, current.instruction))
      return current.content.selection.map((e) => [
        e.head,
        e.relationship,
        e.tail,
      ]);
    if (
      isReflect(current.content, current.instruction) ||
      isAnswer(current.content, current.instruction) ||
      isFinal(current.content, current.instruction)
    )
      return Object.keys(current.content).map((k) => [
        k,
        formatResultData((current.content as any)[k]),
      ]);
    return [];
  }, [current]);

  const invalidIndices: Set<number> = useMemo(() => {
    const set = new Set<number>();
    if (
      isPickSeedEntities(current.content, current.instruction) ||
      isPickRelationship(current.content, current.instruction) ||
      isPickTriplets(current.content, current.instruction)
    ) {
      const prev = data[at - 1];
      if (isModelInput(prev.content, prev.role)) {
        for (let index = 0; index < list.length; index++) {
          const isPresentInData = prev.content.data.some((pd) => {
            if (pd.length !== list[index].length) return false;
            for (let i = 0; i < pd.length; i++) {
              if (pd[i] !== list[index][i]) return false;
            }
            return true;
          });
          if (!isPresentInData) set.add(index);
        }
      }
    }
    return set;
  }, [list]);

  return (
    <div className="mb-8">
      <div
        className={cn(
          "bg-neutral-950/80 p-4 rounded-b-2xl font-mono text-xs border text-white",
          isFinal(current.content, current.instruction) && "rounded-t-2xl"
        )}
      >
        <h3 className="markdown font-sans text-sm font-medium">Model output</h3>
        <Table className="text-xs">
          <TableHeader>
            <TableRow>
              {HEADER_MAP[current.instruction].map((head, index) => (
                <TableHead key={index} className="font-bold text-white">
                  {head}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {list.map((row, index) => (
              <TableRow
                className={cn(
                  invalidIndices.has(index) && "text-yellow-500/70"
                )}
                key={index}
              >
                {row.map((cell, cellIndex) => (
                  <TableCell title={cell} key={cellIndex}>
                    <span
                      className={cn(
                        "flex gap-2",
                        row.length === 3 && "w-27.5",
                        row.length === 2 && "w-39",
                        row.length === 1 && "w-82"
                      )}
                    >
                      {cellIndex === 0 && invalidIndices.has(index) && (
                        <AlertTriangle className="size-4 shrink-0" />
                      )}
                      <span className="self-stretch truncate">{cell}</span>
                    </span>
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      {!!invalidIndices.size && (
        <Alert className="bg-yellow-500/10 mt-4">
          <AlertTriangle />
          <AlertTitle>{"Warning"}</AlertTitle>
          <AlertDescription>
            The agent picked non-existent values.
            <br />
            This might have been caused by hallucination and can lead to a
            failure of knowledge graph based answering if all values are
            invalid.
          </AlertDescription>
        </Alert>
      )}
      {!!reason && (
        <div className="px-4 pt-4 hyphens-auto wrap-break-words">{reason}</div>
      )}
    </div>
  );
};

export const InternalAssistantMessagePlaceholder = () => {
  return (
    <div
      className={
        "bg-neutral-950/80 border p-4 rounded-b-2xl font-mono text-xs mb-8 mx-8 text-white"
      }
    >
      <h3 className="markdown font-sans text-sm font-medium animate-pulse">
        Model output
      </h3>
    </div>
  );
};

function formatResultData(obj: any): string {
  if (typeof obj === "boolean") {
    return obj ? "Yes" : "No";
  }
  return obj;
}
