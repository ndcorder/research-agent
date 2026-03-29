/**
 * Browser-mode replacement for Tauri's invoke().
 * Routes all commands through the Vite dev backend at /__dev/invoke.
 */
export async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  const res = await fetch("/__dev/invoke", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cmd, args: args ?? {} }),
  });

  const json = await res.json();
  if (!json.ok) throw new Error(json.error ?? "Command failed");
  return json.data as T;
}
