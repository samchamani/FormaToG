import { useEffect, useState } from "react";

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
