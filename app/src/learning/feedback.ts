import type { AnswerResult, PublicQuestion } from "../api";

interface Reading {
  title: string;
  publisher: string;
  url: string;
  purpose: string;
}

interface TeachingNote {
  concept: string;
  principle: string;
  example: string;
  check: string;
  reasoning: string;
}

interface TopicGuide extends TeachingNote {
  resources: Reading[];
}

// General study guidance, not question answers. Answer-specific explanations and
// corrected code still come from the server only after grading.
const topics: Record<string, TopicGuide> = {
  caching: {
    concept: "Cache freshness and reuse",
    principle:
      "A cache trades repeated work for a second copy of data. Ask what makes a cached value reusable and how that copy becomes fresh after a write.",
    example:
      "If 100 requests read the same unchanged product, one database read can populate a cache for the others. A price update makes that copy stale until it is refreshed or invalidated.",
    check:
      "A cached profile has a ten-minute TTL. Can a user see an old name immediately after changing it?",
    reasoning:
      "Yes. TTL controls expiry, not immediate consistency. Updating or invalidating the cached profile after the database write reduces that stale window; concurrent reads and cache fills also need care.",
    resources: [
      {
        title: "Cache-Aside pattern",
        publisher: "Microsoft Learn",
        url: "https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside",
        purpose:
          "Follow the read path, then study invalidation and consistency tradeoffs.",
      },
      {
        title: "Key eviction",
        publisher: "Redis",
        url: "https://redis.io/docs/latest/develop/reference/eviction/",
        purpose: "Compare LRU and LFU, and distinguish eviction from expiry.",
      },
    ],
  },
  scaling: {
    concept: "Capacity and bottlenecks",
    principle:
      "Adding capacity helps only at the component limiting throughput. Trace every request through shared dependencies before choosing what to scale.",
    example:
      "Ten API servers can each handle 1,000 requests per second, but a shared store capped at 2,000 operations per second still limits requests that all need that store.",
    check:
      "The API CPU is low while a shared database is saturated. Will doubling the API instances fix throughput?",
    reasoning:
      "No. The shared dependency remains the limit and may receive more concurrent work. Measure its workload, then reduce that work or add capacity at the constrained tier.",
    resources: [
      {
        title: "Autoscaling guidance",
        publisher: "Microsoft Learn",
        url: "https://learn.microsoft.com/en-us/azure/architecture/best-practices/auto-scaling",
        purpose:
          "Choose scaling signals and account for warm-up time and downstream limits.",
      },
      {
        title: "Sharding pattern",
        publisher: "Microsoft Learn",
        url: "https://learn.microsoft.com/en-us/azure/architecture/patterns/sharding",
        purpose:
          "Learn how partition keys distribute work and why hot shards still happen.",
      },
    ],
  },
  databases: {
    concept: "Access patterns and database cost",
    principle:
      "Start with the query and the work it causes: rows examined, round trips, writes, or connections. Optimize that work before replacing the database.",
    example:
      "A page with 50 posts can cause 51 queries if each author is fetched separately. Fetching the authors together removes repeated round trips even if the number of posts stays the same.",
    check: "Why not add an index to every column?",
    reasoning:
      "Indexes occupy storage and must be maintained on relevant writes. Choose indexes that support actual query filters, joins and ordering, and check the query plan rather than assuming every index helps.",
    resources: [
      {
        title: "Introduction to indexes",
        publisher: "PostgreSQL",
        url: "https://www.postgresql.org/docs/current/indexes-intro.html",
        purpose:
          "See how an index changes a lookup and what maintaining it costs.",
      },
      {
        title: "Hot standby",
        publisher: "PostgreSQL",
        url: "https://www.postgresql.org/docs/current/hot-standby.html",
        purpose:
          "Understand read replicas, replay delay and read-only query limitations.",
      },
    ],
  },
  "async-messaging": {
    concept: "Reliable asynchronous work",
    principle:
      "A queue separates accepting work from completing it. That helps absorb bursts, but you still need enough consumer capacity and a plan for retries and duplicates.",
    example:
      "If 200 jobs arrive each minute and workers finish 150, the backlog grows by 50 per minute. A larger queue delays overflow; it does not increase processing speed.",
    check:
      "A worker charges a card, then crashes before acknowledging the message. What happens on redelivery?",
    reasoning:
      "The charge may be attempted again. Use a stable payment idempotency key with the payment provider and durable deduplication; a separate unchecked read followed by a charge is not sufficient.",
    resources: [
      {
        title: "Competing Consumers pattern",
        publisher: "Microsoft Learn",
        url: "https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers",
        purpose:
          "Study worker scaling, duplicate delivery and message ordering.",
      },
      {
        title: "Publisher-Subscriber pattern",
        publisher: "Microsoft Learn",
        url: "https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber",
        purpose:
          "Compare distributing jobs with delivering events to independent subscribers.",
      },
    ],
  },
  reliability: {
    concept: "Containing failures",
    principle:
      "A dependency failure should consume a bounded amount of time and capacity. Decide which work is essential and where a safe fallback is possible.",
    example:
      "If recommendations hang, a product page can stop waiting after a deadline and omit that optional section. Checkout still needs to report a real payment result rather than pretending a charge succeeded.",
    check: "Why can retries make an outage worse?",
    reasoning:
      "Retries add load while a dependency has reduced capacity. Bound attempts and total time, use backoff with jitter, and retry side effects only when they are safe or idempotent.",
    resources: [
      {
        title: "Circuit Breaker pattern",
        publisher: "Microsoft Learn",
        url: "https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker",
        purpose:
          "Follow closed, open and half-open states and learn when to stop calling a dependency.",
      },
      {
        title: "Timeouts, retries, and backoff with jitter",
        publisher: "AWS Builders’ Library",
        url: "https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/",
        purpose:
          "Learn how deadlines, retry budgets and jitter prevent cascading overload.",
      },
    ],
  },
  "arrays-strings": {
    concept: "Index boundaries and pointer movement",
    principle:
      "Write down which elements each pointer represents. Every access must stay in bounds, and every iteration must advance toward the stopping condition.",
    example:
      "For a list of length 3, valid indices are 0, 1 and 2. A slice ending at 3 excludes that endpoint, but indexing element 3 raises an error.",
    check:
      "Which tiny inputs would you test before trusting a two-pointer loop?",
    reasoning:
      "Try empty and single-element inputs, then two elements that match and two that do not. These expose boundary errors before larger examples hide them.",
    resources: [
      {
        title: "Lists and data structures",
        publisher: "Python documentation",
        url: "https://docs.python.org/3/tutorial/datastructures.html",
        purpose: "Practice list operations and iteration with small examples.",
      },
      {
        title: "Sequence operations",
        publisher: "Python documentation",
        url: "https://docs.python.org/3/library/stdtypes.html#common-sequence-operations",
        purpose: "Review indexing, slicing and exclusive slice endpoints.",
      },
    ],
  },
  "binary-search": {
    concept: "Search interval invariants",
    principle:
      "Decide whether the upper bound is included or excluded. The loop condition and both bound updates must agree, preserve candidates, and shrink the search interval.",
    example:
      "An inclusive interval [0, 0] still contains one candidate. A half-open interval [0, 0) is empty. That distinction changes the stopping condition.",
    check:
      "For the failing input, list lo, hi and mid on each iteration. Which candidates remain after each update?",
    reasoning:
      "Use the interval convention of this function, not a memorized comparison. Check that no possible answer is discarded and that the interval shrinks; then verify the returned value.",
    resources: [
      {
        title: "Array bisection and insertion points",
        publisher: "Python documentation",
        url: "https://docs.python.org/3/library/bisect.html",
        purpose:
          "Compare left and right insertion boundaries, especially with duplicates.",
      },
      {
        title: "Searching sorted lists",
        publisher: "Python documentation",
        url: "https://docs.python.org/3.12/library/bisect.html#searching-sorted-lists",
        purpose:
          "See why finding an insertion point and finding an exact match need different checks.",
      },
    ],
  },
  recursion: {
    concept: "Base cases and smaller subproblems",
    principle:
      "A recursive function needs a correct stopping value and progress toward it. Then check how each waiting call combines the smaller result.",
    example:
      "factorial(3) waits for factorial(2), which waits for factorial(1), then factorial(0). The base result 1 lets multiplication unwind to 6.",
    check: "Why does factorial(0) return 1 rather than 0?",
    reasoning:
      "One is the identity for multiplication. Returning zero would make every positive factorial zero when the waiting calls multiply by the base result.",
    resources: [
      {
        title: "Recursion and dictionaries",
        publisher: "MIT OpenCourseWare",
        url: "https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/resources/lecture-6-recursion-and-dictionaries/",
        purpose:
          "Use the lecture, slides and examples to practice call stacks and base cases.",
      },
      {
        title: "Defining functions",
        publisher: "Python documentation",
        url: "https://docs.python.org/3.12/tutorial/controlflow.html#defining-functions",
        purpose:
          "Review local variables and returned values before tracing recursive calls.",
      },
    ],
  },
  sorting: {
    concept: "Preserving order and elements",
    principle:
      "A sort must produce the right order and keep every input element, including duplicates. Track the part that is already sorted while processing the rest.",
    example:
      "Sorting [3, 1, 1] should give [1, 1, 3]. Producing [1, 3] looks ordered but is wrong because one occurrence disappeared.",
    check:
      "Is checking that the output is increasing enough to prove a sort worked?",
    reasoning:
      "No. Also check the output has the same elements with the same counts. Empty lists, duplicates and already-sorted inputs reveal different classes of error.",
    resources: [
      {
        title: "Sorting techniques",
        publisher: "Python documentation",
        url: "https://docs.python.org/3/howto/sorting.html",
        purpose: "Compare sorted() and list.sort(), keys, and stable ordering.",
      },
      {
        title: "Merging sorted inputs",
        publisher: "Python documentation",
        url: "https://docs.python.org/3.12/library/heapq.html#heapq.merge",
        purpose:
          "Study the sorted-input precondition and compare with the merge exercise.",
      },
    ],
  },
  "hash-maps": {
    concept: "What each dictionary entry means",
    principle:
      "Define the meaning of a key and its value before following the loop. A count, an earlier index and a best-so-far result require different updates.",
    example:
      "Counting 'aba' starts with an empty dictionary. After 'a', 'b', 'a', the counts are a: 2 and b: 1. Increment from the previous count instead of overwriting it with 1.",
    check:
      "Why does two-sum check for a complement before inserting the current element?",
    reasoning:
      "The dictionary should contain earlier indices only. Looking up first prevents a single element from pairing with itself, while still allowing two equal values at different indices.",
    resources: [
      {
        title: "Dictionaries",
        publisher: "Python documentation",
        url: "https://docs.python.org/3/tutorial/datastructures.html#dictionaries",
        purpose: "Review keys, membership, lookup and updating stored values.",
      },
      {
        title: "Counter",
        publisher: "Python documentation",
        url: "https://docs.python.org/3/library/collections.html#collections.Counter",
        purpose:
          "Compare a manual counting loop with a standard frequency table.",
      },
    ],
  },
};

const functions: Record<string, TeachingNote> = {
  binary_search: {
    ...topics["binary-search"],
    concept: "Inclusive binary search",
    principle:
      "Here lo and hi are both valid candidate indices. Keep checking while one candidate remains, then exclude mid when its value cannot match.",
    example:
      "Searching [4] for 4 starts with lo = hi = mid = 0. The comparison at index 0 must run before declaring the target absent.",
  },
  lower_bound: {
    ...topics["binary-search"],
    concept: "The first valid insertion point",
    principle:
      "This search uses a half-open interval. Keep the first index whose value is at least the target as a possible answer; the result may equal len(nums).",
    example:
      "For [2, 4, 4, 7], the first position at least 4 is index 1. For target 8, the insertion point is 4, just past the list.",
  },
  factorial: {
    ...topics.recursion,
    concept: "Multiplication while the stack unwinds",
    principle:
      "For nonnegative integers, n! equals n times (n - 1)!, with 0! = 1. The recursive step must reduce n and preserve multiplication.",
  },
  power: {
    ...topics.recursion,
    concept: "Exponentiation by squaring",
    principle:
      "For a nonnegative integer exponent, compute the half power once and square it. An odd exponent needs one additional factor of x; exponent zero returns 1.",
    example:
      "2^5 uses half = 2^2 = 4, then 4 × 4 × 2 = 32. 2^4 uses 4 × 4 = 16.",
    check:
      "For power(3, 3), what is half, and which operation accounts for the odd exponent?",
    reasoning:
      "half is power(3, 1) = 3. Squaring gives 9, then multiplying once more by 3 gives 27. Without the extra factor, the result would represent exponent 2.",
  },
  palindrome: {
    ...topics["arrays-strings"],
    concept: "Comparing mirrored characters",
    principle:
      "Compare the outer characters, then move both pointers inward. One mismatch proves the string is not a palindrome. A middle character needs no partner.",
    example:
      "For 'abba', compare indices 0 and 3, then 1 and 2. For 'abca', the second pair differs, so the result is False.",
    check:
      "Why do empty and one-character strings return True in this function?",
    reasoning:
      "There are no unequal mirrored pairs to find, so the loop can finish without rejecting the string.",
  },
  two_sum_sorted: {
    ...topics["arrays-strings"],
    concept: "Using sorted order to move pointers",
    principle:
      "For sorted ascending values, moving the left pointer right can increase the sum; moving the right pointer left can decrease it. Use distinct indices.",
    example:
      "In [1, 3, 5, 7], target 10 starts at 1 + 7 = 8. Move left to 3, then 3 + 7 = 10 gives indices [1, 3].",
    check: "Would these pointer moves still be valid on an unsorted list?",
    reasoning:
      "No. The reasoning depends on sorted order. An unsorted list needs a different strategy or sorting with careful preservation of original indices.",
  },
  two_sum: {
    ...topics["hash-maps"],
    concept: "Remembering earlier complements",
    principle:
      "Before processing index i, seen maps earlier values to their indices. Look for target minus the current value before recording the current index.",
    example:
      "For [3, 3] and target 6, the first 3 is recorded at index 0. The second 3 finds it, giving [0, 1] without reusing one element.",
  },
  first_unique: {
    ...topics["hash-maps"],
    concept: "Counting first, then preserving original order",
    principle:
      "The first pass counts every character. The second pass scans the original string and returns the earliest index whose final count is exactly one.",
    example:
      "In 'swiss', s occurs three times, while w and i each occur once. Scanning from the start returns index 1 for w.",
    check: "Why not return a character as soon as its count first becomes one?",
    reasoning:
      "A later occurrence could make it repeated. Complete the frequency table first, then decide which character remains unique.",
  },
  most_common: {
    ...topics["hash-maps"],
    concept: "Counts and a best-so-far value",
    principle:
      "Increment the current value's count, then compare it with best_count. When the count becomes strictly larger, update both the best value and its count.",
    example:
      "In [2, 1, 1], the final 1 raises its count from 1 to 2. That exceeds the best count of 1, so both best and best_count must change.",
    check:
      "Why does changing best without changing best_count break later decisions?",
    reasoning:
      "The comparison would use an outdated threshold. The value and its count describe one fact and must stay in sync.",
  },
  insertion_sort: {
    ...topics.sorting,
    concept: "Growing a sorted prefix",
    principle:
      "Before each insertion, the earlier prefix is sorted. Save the key, shift larger values one place right, then put the key in the gap.",
    example:
      "For [3, 1, 2], insert 1 before 3 to get [1, 3, 2]. Then shift 3 right and insert 2 to get [1, 2, 3].",
    check: "Why save key before shifting the earlier elements?",
    reasoning:
      "A shift can overwrite the key's original slot. Saving it keeps the value available for insertion into the final gap.",
  },
  merge: {
    ...topics.sorting,
    concept: "Merging two sorted sequences",
    principle:
      "The smallest remaining value must be at the front of one input. Append the smaller front and advance only its pointer; append the remaining tail when one side runs out.",
    example:
      "Merge [1, 4] with [2, 3]: take 1, then 2, then 3. The second input is empty, so append the remaining 4.",
    check:
      "Why append the leftover tail instead of stopping when either input ends?",
    reasoning:
      "Those values still belong in the result. They are already sorted and at least as large as the values emitted so far, so the whole tail can be appended.",
  },
};

export function learningFor(question: PublicQuestion, result: AnswerResult) {
  const topic = Object.hasOwn(topics, question.topic)
    ? topics[question.topic]
    : undefined;
  if (!topic) return undefined;
  const name =
    result.provenance?.source_function.match(/\/([a-z_]+)\.py::/)?.[1];
  const note = name && Object.hasOwn(functions, name) ? functions[name] : topic;
  return { ...note, resources: topic.resources };
}
