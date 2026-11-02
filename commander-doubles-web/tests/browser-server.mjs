// Local-only browser fixture. The app, database and persistence are real;
// upstream refusal is deterministic here, never evidence of a live Moxfield import.
import { createApp } from "../app.mjs";
import { migrate } from "../db.mjs";
if (process.env.APP_ENV !== "local")
  throw Error("Browser fixture requires APP_ENV=local");
await migrate();
createApp({
  moxfieldOptions: { fetcher: async () => ({ ok: false, status: 403 }) },
}).listen(Number(process.env.PORT || 3342), "127.0.0.1", () =>
  console.log("Local browser fixture ready"),
);
