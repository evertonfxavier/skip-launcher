import { useLanguage, useSkipLauncher } from "../hooks";
import { SkipPanel } from "./SkipPanel";

export function Panel() {
  useLanguage(); // re-renders the panel once Steam's language is known
  const model = useSkipLauncher();
  return <SkipPanel model={model} />;
}
