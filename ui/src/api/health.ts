import { useEffect, useState } from "react";

export type Config = {
  agent_provider: "ollama" | "google";
  model: string;
  graph_db: "neo4j" | "wikidata";
  max_paths: number;
  max_depth: number;
  use_context: boolean;
  default_seed_entity_ids: string[];
};

export function useHealthCheckAPI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const get = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${import.meta.env.VITE_SERVER_URL}/`);
      if (!resp.ok) throw Error("Failure during server connection");
      setError(null);
    } catch (error) {
      console.error("Request failed", error);
      setError("Failure during server connection");
    }
    setLoading(false);
  };

  useEffect(() => {
    (async () => {
      await get();
    })();
  }, []);
  return { loading, error };
}
