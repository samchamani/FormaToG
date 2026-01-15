import {
  isModelInput,
  isPickTriplets,
  useChatAPI,
  type Message,
} from "@/api/chat";
import { useEffect, useState } from "react";
import {
  darkTheme,
  GraphCanvas,
  type GraphNode,
  type GraphEdge,
  Sphere,
  Label,
  type InternalGraphNode,
  type InternalGraphEdge,
} from "reagraph";
import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import { Component, Link, X } from "lucide-react";

type Props = {
  selectedColor?: string;
};

export const Graph = ({ selectedColor = "seagreen" }: Props) => {
  const { data } = useChatAPI();
  const { nodes, edges } = getGraphObjects(data, selectedColor);
  const [focused, setFocused] = useState<
    InternalGraphNode | InternalGraphEdge
  >();
  const [keepInfo, setKeepInfo] = useState(false);
  const [useDarkMode, setUseDarkMode] = useState(false);

  const handleClose = () => {
    setFocused(undefined), setKeepInfo(false);
  };

  useEffect(() => {
    setUseDarkMode(
      !!document.querySelector("html")?.classList.contains("dark")
    );
  }, []);

  return (
    <div className="fixed top-0 left-0 h-full w-full">
      <GraphCanvas
        theme={useDarkMode ? darkTheme : undefined}
        nodes={nodes}
        edges={edges}
        edgeLabelPosition="natural"
        labelType="none"
        onEdgePointerOver={(edge) => !keepInfo && setFocused(edge)}
        onNodePointerOver={(node) => !keepInfo && setFocused(node)}
        onEdgePointerOut={() => !keepInfo && setFocused(undefined)}
        onNodePointerOut={() => !keepInfo && setFocused(undefined)}
        onEdgeClick={(edge) => (setFocused(edge), setKeepInfo(true))}
        onNodeClick={(node) => (setFocused(node), setKeepInfo(true))}
        onCanvasClick={handleClose}
        renderNode={({ node, ...rest }) => (
          <group>
            <Sphere {...rest} node={node} />
            <group position={[-1, 0, 0]}>
              <Label
                text={node.label || ""}
                fontSize={4}
                color={"white"}
                ellipsis={5}
              />
            </group>
          </group>
        )}
        draggable
      />
      <Card
        className={cn(
          "absolute top-8 right-8 w-80 max-h-60 bg-card/80 backdrop-blur-sm opacity-0 transition-opacity",
          focused ? "opacity-100" : "pointer-events-none"
        )}
      >
        <CardHeader className="h-8">
          <CardTitle className="flex gap-2 items-center">
            {focused && "position" in focused && (
              <>
                <Component />
                Entity
              </>
            )}
            {focused && "source" in focused && (
              <>
                <Link />
                Relationship
              </>
            )}
          </CardTitle>
          <CardAction>
            <Button
              className="relative -top-2.5 left-1"
              variant="ghost"
              size={"icon-sm"}
              onClick={handleClose}
            >
              {keepInfo && <X />}
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent className="wrap-break-word overflow-y-scroll text-sm">
          {focused?.label}
        </CardContent>
      </Card>
    </div>
  );
};

const getGraphObjects = (data: Message[], selectedColor: string) => {
  const nodeMap: Record<string, boolean> = {};
  const nodes: GraphNode[] = [];
  const edgeSet = new Set<string>();
  const edges: GraphEdge[] = [];

  const nodeRelevantUserMessages = data.filter(
    (d) =>
      d.role === "user" &&
      [
        "pick_seed_entities",
        "pick_relationships",
        "pick_triplets",
        "reflect",
      ].some((i) => i === d.instruction)
  );
  for (const message of nodeRelevantUserMessages) {
    if (!isModelInput(message.content, message.role)) continue;
    for (const entry of message.content.data.slice(1)) {
      for (const index of [0, 2]) {
        if (!entry[index]) continue;
        if (entry[index] in nodeMap) {
          if (message.instruction === "reflect" && !nodeMap[entry[index]]) {
            const node = nodes.find((n) => n.id === entry[index]);
            if (node) node.fill = selectedColor;
          }
        } else {
          nodeMap[entry[index]] = message.instruction === "reflect";
          nodes.push({
            id: entry[index],
            label: entry[index],
            fill: message.instruction === "reflect" ? selectedColor : undefined,
          });
        }
      }
    }
  }

  const edgeRelevantUserMessages = data.filter(
    (d) =>
      d.role === "user" &&
      ["pick_triplets", "reflect"].some((i) => i === d.instruction)
  );
  for (const message of edgeRelevantUserMessages) {
    if (!isModelInput(message.content, message.role)) continue;
    for (const entry of message.content.data.slice(1)) {
      const edgeId = `${entry[0]}-${entry[1]}->${entry[2]}`;
      if (edgeSet.has(edgeId)) continue;
      edgeSet.add(edgeId);
      edges.push({
        id: edgeId,
        label: entry[1],
        source: entry[0],
        target: entry[2],
        size: 1.5,
        fill: message.instruction === "reflect" ? selectedColor : undefined,
      });
    }
  }

  const assistantMessages = data.filter(
    (d) =>
      d.role === "assistant" &&
      ["pick_seed_entities", "pick_relationships", "pick_triplets"].some(
        (i) => i === d.instruction
      )
  );

  for (const message of assistantMessages) {
    if (isPickTriplets(message.content, message.instruction)) {
      for (const entry of message.content.selection) {
        const edge = edges.find(
          (e) =>
            e.source === entry.head &&
            e.target === entry.tail &&
            e.label === entry.relationship
        );
        if (edge) {
          const head = nodes.find((n) => n.id === edge.source);
          const tail = nodes.find((n) => n.id === edge.target);
          if (head && tail) {
            head.fill = selectedColor;
            tail.fill = selectedColor;
            edge.fill = selectedColor;
          }
        }
      }
    }
  }
  return { nodes, edges };
};
