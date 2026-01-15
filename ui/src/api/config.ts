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

export function useConfigAPI() {
  const [config, setConfig] = useState<Config>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const config_url = `${import.meta.env.VITE_SERVER_URL}/config`;

  const getConfig = async () => {
    setLoading(true);
    try {
      const fetched = await fetch(config_url);
      const data: Config = await fetched.json();
      setConfig(data);
    } catch (error) {
      console.error("Fetching config failed:", error);
      setError("Fetching configuration has failed");
    }
    setLoading(false);
  };

  const updateConfig = async (updated: Config) => {
    setLoading(true);
    try {
      const fetched = await fetch(config_url, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updated),
      });
      const data: Config = await fetched.json();
      setConfig(data);
    } catch (error) {
      console.error("Fetching config failed:", error);
      setError("Fetching configuration has failed");
    }
    setLoading(false);
  };

  useEffect(() => {
    (async () => {
      await getConfig();
    })();
  }, []);
  return { config, loading, error, updateConfig };
}
