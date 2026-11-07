# Learning-centered feedback

F1 (#65) adds teaching after lesson answers. The feedback begins with the reasoning rather than the rating delta. Incorrect or partly ordered answers retain the learner's selected answer beside the expected answer.

The system-design bank's 50 explanations now discuss mechanisms, tradeoffs and common misconceptions. They retain the existing 500-character contract; answers and difficulty ratings do not change.

General study guidance in `app/src/learning/feedback.ts` adds a principle, a small worked example and a retrieval question with optional reasoning. All ten topics have two curated reading links, publisher names and a description of what to study. Algorithm-specific notes cover all eleven current corpus functions, including different interval conventions for exact binary search and lower bound. Unknown functions use topic guidance; unknown topics still show the server's explanation.

Debugging feedback can expand the observed failing cases and compare the faulty line with the corrected line from the grading response. It does not execute submitted code or infer a patch in the browser. Question-specific explanations, answers and provenance remain server-provided after grading. No API or schema change is required, and generated debugging content is not hand-edited.

Reading links were checked on 7 November 2026 against Microsoft Learn, Redis, PostgreSQL, AWS Builders' Library, Python documentation and MIT OpenCourseWare. Resources open in a new tab to preserve the lesson. Reading and reasoning sections are optional, so the learner can continue without visiting external sites.

For future content, write explanations that connect the scenario to the mechanism and identify a useful limitation or tempting alternative. Avoid merely restating the answer. When adding an algorithm, distinguish its actual invariant from superficially similar implementations before adding a worked example.
