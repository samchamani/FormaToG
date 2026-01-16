import { useMemo } from "react";

export const Logo = () => {
  const variant = useMemo(() => {
    return !!document.querySelector("html")?.classList.contains("dark")
      ? "dark"
      : "light";
  }, []);
  return (
    <div className="h-10 w-35 flex justify-center items-center overflow-hidden">
      <img className="object-contain" src={`./${variant}.svg`} />
    </div>
  );
};
