/**
 * Next.js parchea console.error DESPUÉS de instrumentation-client.
 * Re-envolvemos en el siguiente tick para que el overlay no trague
 * mismatches causados por extensiones (bis_skin_checked, etc.).
 */

type FilteredConsole = ((...args: unknown[]) => void) & { __apiDeskExtFilter?: boolean };

const EXTENSION_NOISE = [
  "bis_skin_checked",
  "bis_register",
  "data-atm-ext-installed",
  "__processed_",
  "chrome-extension://",
];

function isExtensionNoise(args: unknown[]): boolean {
  try {
    const text = args
      .map((value) => {
        if (typeof value === "string") return value;
        if (value instanceof Error) return `${value.message}\n${value.stack ?? ""}`;
        try {
          return JSON.stringify(value);
        } catch {
          return String(value);
        }
      })
      .join(" ");
    return EXTENSION_NOISE.some((token) => text.includes(token));
  } catch {
    return false;
  }
}

function wrapConsoleError() {
  const current = console.error as FilteredConsole;
  if (current.__apiDeskExtFilter) return;

  const filtered: FilteredConsole = (...args: unknown[]) => {
    if (isExtensionNoise(args)) return;
    current.apply(console, args);
  };
  filtered.__apiDeskExtFilter = true;
  console.error = filtered;
}

wrapConsoleError();
queueMicrotask(wrapConsoleError);
setTimeout(wrapConsoleError, 0);
setTimeout(wrapConsoleError, 50);
setTimeout(wrapConsoleError, 200);

window.addEventListener(
  "error",
  (event) => {
    const fromExtension =
      event.filename?.startsWith("chrome-extension://") ||
      (event.error instanceof Error && event.error.stack?.includes("chrome-extension://"));
    if (fromExtension) event.preventDefault();
  },
  true,
);
