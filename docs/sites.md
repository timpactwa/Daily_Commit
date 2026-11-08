# Sites deployment

The Site serves the existing React app as a Worker. Accounts, daily lessons, ratings,
and ranked attempts use the production Railway API over HTTPS. Only the app's API
headers are forwarded; Sites identity and cookies stay on Sites.

Expanded guides are bundled server-side, with checkpoint answers withheld until
graded. Sites provisions D1 using the `DB` binding. Copy `sites/drizzle/` to the Site
checkout's `drizzle/` before packaging. Guide completion is stored separately from
Railway, scoped to both the signed-in Site visitor and verified app user. Daily
practice and ranked ratings continue to use the existing account.

The dedicated Sites checkout contains the source from this repository and a
`.openai/hosting.json` with the registered project ID, `"d1": "DB"`, and `"r2": null`.
Keep that returned ID unchanged. Do not include `static` for this Worker build.

Build `app/` normally, then run `node sites/build.mjs` from the repository root.
Run `node --test sites/worker.test.mjs` to check proxy boundaries and saved guide
progress before publishing through the Sites source and deployment workflow.
The live Site is owner-private unless its audience is explicitly changed.
