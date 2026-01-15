import { Minus, Plus } from "lucide-react";
import { Button } from "./ui/button";

type Props = {
  value: number;
  min?: number;
  max?: number;
  onChange: (newVal: number) => void;
};
export const NumberField = ({ value, onChange, min, max }: Props) => {
  const maxDisabled = max !== undefined && max <= value;
  const minDisabled = min !== undefined && min >= value;
  return (
    <div className="flex gap-2 items-center">
      <span className="min-w-10 text-center">{value}</span>
      <div className="outline rounded-lg overflow-hidden">
        <Button
          className="rounded-r-none"
          variant="secondary"
          size="icon-sm"
          onClick={() =>
            !maxDisabled &&
            onChange(max !== undefined ? Math.min(value + 1, max) : value + 1)
          }
          disabled={maxDisabled}
        >
          <Plus />
        </Button>
        <Button
          className="rounded-l-none"
          variant="secondary"
          size="icon-sm"
          onClick={() =>
            !minDisabled &&
            onChange(min !== undefined ? Math.max(value - 1, min) : value - 1)
          }
          disabled={minDisabled}
        >
          <Minus />
        </Button>
      </div>
    </div>
  );
};
