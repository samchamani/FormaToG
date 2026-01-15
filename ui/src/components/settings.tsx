import { type Config, useConfigAPI } from "@/api/config";
import { useEffect, useState } from "react";
import { Button } from "./ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Label } from "./ui/label";
import { Input } from "./ui/input";
import { NumberField } from "./number-field";
import { Switch } from "./ui/switch";
import { Textarea } from "./ui/textarea";
import { cn } from "@/lib/utils";

const labelStyle = "w-50 text-right mr-4 shrink-0";
const pseudoLabelStyle =
  "flex items-center gap-2 text-sm leading-none font-medium select-none group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50 peer-disabled:cursor-not-allowed peer-disabled:opacity-50";

type AdjustedConfig = Omit<Config, "default_seed_entity_ids"> & {
  default_seed_entity_ids: string;
};

export const Settings = () => {
  const { config, loading, error, updateConfig } = useConfigAPI();
  const [current, setCurrent] = useState<AdjustedConfig>();
  const [message, setMessage] = useState("");

  const handleApply = async () => {
    if (!current) return;
    const normalizedConfig: Config = {
      ...current,
      default_seed_entity_ids: current.default_seed_entity_ids
        .trim()
        .split("\n")
        .filter((v) => v),
    };
    await updateConfig(normalizedConfig);
    setMessage("Saved!");
  };

  useEffect(() => {
    if (!config) return;
    const adjustedConfig: AdjustedConfig = {
      ...config,
      default_seed_entity_ids: config.default_seed_entity_ids.join("\n"),
    };
    setCurrent(adjustedConfig);
  }, [config]);

  if (!config || !current) return null;
  if (error) setMessage("Failed");
  return (
    <div className="flex flex-col gap-4 items-center justify-center h-full">
      <h2 className="font-bold text-center">Settings</h2>
      <div className="flex flex-col gap-4 p-8 w-full">
        <Label>
          <span className={labelStyle}>Knowledge graph database:</span>
          <Select
            value={current.graph_db}
            onValueChange={(v) =>
              setCurrent((prev) => ({ ...prev, graph_db: v } as AdjustedConfig))
            }
            required
          >
            <SelectTrigger className="grow">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="neo4j">Neo4j</SelectItem>
              <SelectItem value="wikidata">Wikidata</SelectItem>
            </SelectContent>
          </Select>
        </Label>
        <Label>
          <span className={labelStyle}>Agent provider:</span>
          <Select
            value={current.agent_provider}
            onValueChange={(v) =>
              setCurrent(
                (prev) => ({ ...prev, agent_provider: v } as AdjustedConfig)
              )
            }
            required
          >
            <SelectTrigger className="grow">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ollama">Ollama</SelectItem>
              <SelectItem value="google">Google</SelectItem>
            </SelectContent>
          </Select>
        </Label>
        <Label>
          <span className={labelStyle}>Language model:</span>
          <Input
            value={current.model}
            required
            onChange={(e) =>
              setCurrent(
                (prev) => ({ ...prev, model: e.target.value } as AdjustedConfig)
              )
            }
          />
        </Label>
        <div className={pseudoLabelStyle}>
          <span className={labelStyle}>Maximum search depth:</span>
          <NumberField
            value={current.max_depth}
            onChange={(v) =>
              setCurrent(
                (prev) => ({ ...prev, max_depth: v } as AdjustedConfig)
              )
            }
            min={1}
            max={6}
          />
        </div>
        <div className={pseudoLabelStyle}>
          <span className={labelStyle}>Maximum paths:</span>
          <NumberField
            value={current.max_paths}
            onChange={(v) =>
              setCurrent(
                (prev) => ({ ...prev, max_paths: v } as AdjustedConfig)
              )
            }
            min={1}
            max={6}
          />
        </div>
        <div className={pseudoLabelStyle}>
          <span className={labelStyle}>Use context:</span>
          <Switch
            checked={current.use_context}
            onClick={() =>
              setCurrent(
                (prev) =>
                  ({
                    ...prev,
                    use_context: !current.use_context,
                  } as AdjustedConfig)
              )
            }
          />
        </div>
        <Label className="items-start">
          <span className={labelStyle}>Default seed entity IDs:</span>
          <Textarea
            className="h-20 resize-none whitespace-pre wrap-normal overflow-x-scroll"
            value={current.default_seed_entity_ids}
            onChange={(e) =>
              setCurrent(
                (prev) =>
                  ({
                    ...prev,
                    default_seed_entity_ids: e.target.value,
                  } as AdjustedConfig)
              )
            }
          />
        </Label>
      </div>
      <div className="relative">
        <Button
          className="w-min"
          disabled={loading || !current}
          onClick={handleApply}
        >
          Apply
        </Button>
        <div
          className={cn(
            "absolute bottom-1/2 translate-y-1/2 left-full pl-4 text-sm select-none opacity-0 transition-opacity",
            message && "opacity-100",
            message === "Saved!" && "text-green-600",
            error && "text-destructive"
          )}
        >
          {message}
        </div>
      </div>
    </div>
  );
};
