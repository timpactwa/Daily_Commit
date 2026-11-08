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
Run `node --test sites/worker.test.mjs sites/practice.test.mjs` to check proxy boundaries and saved guide
progress before publishing through the Sites source and deployment workflow.
The live Site is owner-private unless its audience is explicitly changed.

Daily practice mastery runs in the Sites Worker using `sites/practice.mjs` and the
`sites_practice_sessions` D1 table. A normal six-question practice requires four
correct answers. Questions with more than two choices or code lines allow two
tries; binary questions and ordering allow one. Retry responses withhold grading
keys until the question is settled. Only the first answer reaches the existing
Elo API; second tries and complete lesson retries never rate that question again.
Failed practice carries over to the next day until passed. Retrying restarts the
same question set so students can apply the explanations. Previously completed
lessons remain complete. Short demo or small-content lessons use the same
two-thirds pass rate. Copy all pending `sites/drizzle/` migrations into `drizzle/`
in the Site checkout before publication. The standalone Railway API remains the
legacy grading service; this mastery feature requires the Sites Worker.
