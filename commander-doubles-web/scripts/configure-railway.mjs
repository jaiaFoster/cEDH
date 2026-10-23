// Stores deploy settings directly in Railway, without depending on deprecated railway.json.
// Does not create, delete, or replace services/databases; secrets stay in Railway Variables.
const token = process.env.RAILWAY_TOKEN,
  serviceId = process.env.RAILWAY_SERVICE_ID,
  environmentId = process.env.RAILWAY_ENVIRONMENT_ID;
if (!token || !serviceId || !environmentId)
  throw Error(
    "RAILWAY_TOKEN, RAILWAY_SERVICE_ID and RAILWAY_ENVIRONMENT_ID are required",
  );
const r = await fetch("https://backboard.railway.com/graphql/v2", {
  method: "POST",
  headers: {
    "Project-Access-Token": token,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 CommanderDoublesLeague/1.0",
  },
  body: JSON.stringify({
    query:
      "mutation($s:String!,$e:String!,$input:ServiceInstanceUpdateInput!){serviceInstanceUpdate(serviceId:$s,environmentId:$e,input:$input)}",
    variables: {
      s: serviceId,
      e: environmentId,
      input: {
        rootDirectory: "/commander-doubles-web",
        startCommand: "npm start",
        healthcheckPath: "/health",
        healthcheckTimeout: 120,
        restartPolicyType: "ON_FAILURE",
        restartPolicyMaxRetries: 5,
        watchPatterns: ["/commander-doubles-web/**"],
      },
    },
  }),
});
const result = await r.json();
if (!r.ok || result.errors)
  throw Error(
    "Railway deploy settings update failed: " +
      (result.errors?.map((e) => e.message).join("; ") || r.status),
  );
console.log("Railway deploy settings configured");
