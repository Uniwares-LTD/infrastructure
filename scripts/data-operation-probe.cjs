"use strict";
// Installed Infrastructure code, streamed to Node in the currently approved image.
const { createRequire } = require("node:module");
const { MongoClient } = createRequire("/app/package.json")("mongodb");
async function probe(request) {
  if (!["ledger", "report", "metadata"].includes(request.action)) throw Error("unsupported");
  const client = new MongoClient(process.env.MONGODB_URI, { serverSelectionTimeoutMS: 10000 });
  try {
    if (process.env.MONGODB_DATABASE !== request.database) throw Error("identity");
    const db = client.db(request.database);
    if (request.action === "ledger") {
      const rows = await db.collection("migrations").find({}, { timeoutMS: 15000 }).toArray();
      return rows.map(row => ({ id: row._id, checksum: row.checksum, appliedAt: row.appliedAt.toISOString(), durationMs: row.durationMs })).sort((a,b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
    }
    if (request.action === "metadata") {
      const lease = await db.collection("control").findOne({ _id: "migrations-lock" }, { timeoutMS: 15000 });
      return { lease: lease ? { owner: lease.owner, expiresAt: lease.expiresAt.toISOString() } : null };
    }
    const report = request.report;
    if (!report || report.version !== 1 || report.project !== request.project || report.environment !== request.environment || report.database !== request.database || !/^[a-f0-9]{64}$/.test(report.operationId)) throw Error("identity");
    // Report copies carry no approval/lease authority. No periodic synchronization.
    await db.collection("deploymentOperations").createIndex({ project: 1, environment: 1, observedAt: -1 });
    const result = await db.collection("deploymentOperations").findOneAndUpdate(
      { _id: report.operationId, project: request.project, environment: request.environment },
      { $setOnInsert: report }, { upsert: true, returnDocument: "after", timeoutMS: 15000 });
    if (request.resolution) await db.collection("deploymentOperations").updateOne({ _id: report.operationId, project: request.project, environment: request.environment }, { $set: { resolution: request.resolution } }, { timeoutMS: 15000 });
    return { recorded: !!result };
  } finally { await client.close(); }
}
