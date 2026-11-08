// Server-side practice mastery. Elo is recorded by the existing API on the first answer only.
export function practiceAttemptLimit(q) {
  if (q.format === 'reorder') return 1;
  const choices = q.format === 'tap_line' ? q.code.split('\n').filter(s => s.trim()).length
    : q.options?.length ?? q.diagram?.nodes.length ?? 0;
  return choices > 2 ? 2 : 1;
}
export function practiceMastery(state) {
  const results = state.lesson.items.map(i => state.results[i.question.id]);
  const total = results.length, required = Math.ceil(total * 2 / 3);
  const answered = results.filter(r => r?.settled).length;
  const correct = results.filter(r => r?.settled && r.correct).length;
  return { total, required, answered, correct, can_complete: answered === total && correct >= required, round: state.round };
}
export function practiceView(state) {
  return { ...state.lesson, status: state.completed ? 'completed' : 'in_progress', mastery: practiceMastery(state),
    items: state.lesson.items.map(i => {
      const r = state.results[i.question.id];
      return { ...i, answered: !!r?.settled, correct: r?.settled ? r.correct : null,
        attempts_used: r?.choices.length ?? 0, attempt_limit: practiceAttemptLimit(i.question),
        tried_responses: r && !r.settled ? r.choices : [] };
    }) };
}
function validatePracticeResponse(q, response, ApiError) {
  const invalid = () => { throw new ApiError(422, 'invalid_response', 'Choose a valid answer'); };
  if (q.format === 'tap_line') {
    if (!Number.isInteger(response) || response < 1 || response > q.code.split('\n').length) invalid();
  } else if (q.format === 'reorder') {
    const ids = q.options.map(o => o.id);
    if (!Array.isArray(response) || response.length !== ids.length || new Set(response).size !== ids.length || response.some(id => !ids.includes(id))) invalid();
  } else if (typeof response !== 'string' || !(q.options ?? q.diagram?.nodes ?? []).some(o => o.id === response)) invalid();
}
function practiceScore(response, answer) {
  if (!Array.isArray(answer)) return response === answer ? 1 : 0;
  let pairs = 0;
  for (let i = 0; i < answer.length; i++) for (let j = i + 1; j < answer.length; j++) {
    if (response.indexOf(answer[i]) < response.indexOf(answer[j])) pairs++;
  }
  return pairs / (answer.length * (answer.length - 1) / 2);
}
export function createPracticeHandler({ upstream, bank, json, ApiError }) {
  const rows = async (DB, sql, ...values) => (await DB.prepare(sql).bind(...values).all()).results;
  async function remote(request, path, method = 'GET', body) {
    const r = await upstream(request, path, method, body);
    const data = await r.json();
    if (!r.ok) throw new ApiError(r.status, data.error?.code ?? 'server', data.error?.message ?? 'Practice is temporarily unavailable');
    return data;
  }
  async function identify(request) {
    const siteUser = request.headers.get('oai-authenticated-user-id');
    if (!siteUser) throw new ApiError(401, 'session_expired', 'Sign in to this Site to save practice progress');
    const me = await remote(request, '/v1/me');
    return JSON.stringify([siteUser, me.user_id]);
  }
  async function current(request, DB, owner) {
    const pending = await rows(DB, 'SELECT * FROM sites_practice_sessions WHERE owner_id = ? AND completed = 0 ORDER BY day LIMIT 1', owner);
    if (pending.length) return pending[0];
    const lesson = await remote(request, '/v1/lessons/today');
    const results = Object.fromEntries(lesson.items.filter(i => i.answered).map(i => [i.question.id, { choices: [], settled: true, correct: i.correct }]));
    // Previously completed lessons remain complete; the gate applies to new practice.
    const state = { lesson, results, round: 1, grading: {}, completed: lesson.status === 'completed' };
    await DB.prepare('INSERT OR IGNORE INTO sites_practice_sessions (owner_id, lesson_id, day, data, completed) VALUES (?, ?, ?, ?, ?)')
      .bind(owner, lesson.lesson_id, lesson.date, JSON.stringify(state), Number(state.completed)).run();
    return (await rows(DB, 'SELECT * FROM sites_practice_sessions WHERE owner_id = ? AND lesson_id = ?', owner, lesson.lesson_id))[0];
  }
  async function save(DB, owner, id, state, token) {
    await DB.prepare('UPDATE sites_practice_sessions SET data = ?, completed = ?, locked_until = 0, lock_token = NULL WHERE owner_id = ? AND lesson_id = ? AND lock_token = ?')
      .bind(JSON.stringify(state), Number(state.completed), owner, id, token).run();
  }
  function reply(state, item, r) {
    const mastery = practiceMastery(state), limit = practiceAttemptLimit(item.question);
    const progress = { answered: mastery.answered, total: mastery.total };
    if (!r.settled) return { correct: false, retry_available: true, attempts_used: r.choices.length,
      attempt_limit: limit, lesson_progress: progress };
    return { ...r.feedback, correct: r.correct, retry_available: false,
      practice_retry: state.round > 1, attempts_used: r.choices.length, attempt_limit: limit, lesson_progress: progress };
  }
  return async function practice(request, env, path) {
    const owner = await identify(request), DB = env.DB;
    if (request.method === 'GET' && path === '/v1/lessons/today') return json(practiceView(JSON.parse((await current(request, DB, owner)).data)));
    let body = {};
    if (path === '/v1/answers') {
      const raw = await request.text();
      if (raw.length > 8192) throw new ApiError(413, 'invalid_response', 'Practice request is too large');
      try { body = JSON.parse(raw); } catch { throw new ApiError(422, 'invalid_response', 'Invalid JSON'); }
      if (!body || typeof body !== 'object' || typeof body.lesson_id !== 'string' || typeof body.question_id !== 'string') throw new ApiError(422, 'invalid_response', 'Invalid answer request');
    }
    const action = /^\/v1\/lessons\/([^/]+)\/(complete|retry)$/.exec(path);
    const id = action?.[1] ?? body.lesson_id;
    const row = (await rows(DB, 'SELECT * FROM sites_practice_sessions WHERE owner_id = ? AND lesson_id = ?', owner, id))[0];
    if (!row) throw new ApiError(404, 'not_found', 'Open this practice lesson first');
    const now = Date.now(), lease = now + 60000, token = crypto.randomUUID();
    const claimed = await rows(DB, 'UPDATE sites_practice_sessions SET locked_until = ?, lock_token = ? WHERE owner_id = ? AND lesson_id = ? AND locked_until <= ? RETURNING data', lease, token, owner, id, now);
    if (!claimed.length) throw new ApiError(409, 'practice_busy', 'Your last answer is still saving. Try again.');
    const state = JSON.parse(claimed[0].data);
    try {
      if (action?.[2] === 'complete') {
        if (state.completed && state.completion) return json(state.completion);
        const mastery = practiceMastery(state);
        if (state.completed) {
          const progress = await remote(request, '/v1/progress');
          state.completion = { summary: { correct: mastery.correct, total: mastery.total }, rating_changes: [],
            streak: { ...progress.streak, extended: false }, mastery };
          await save(DB, owner, id, state, token);
          return json(state.completion);
        }
        if (!state.completed && !mastery.can_complete) throw new ApiError(409, 'not_passed', `Get at least ${mastery.required} of ${mastery.total} correct within the allowed tries before finishing.`);
        const result = await remote(request, `/v1/lessons/${encodeURIComponent(id)}/complete`, 'POST');
        state.completed = true;
        state.completion = { ...result, summary: { correct: mastery.correct, total: mastery.total }, mastery };
        await save(DB, owner, id, state, token);
        return json(state.completion);
      }
      if (action?.[2] === 'retry') {
        const mastery = practiceMastery(state);
        if (state.completed || mastery.answered !== mastery.total || mastery.can_complete) throw new ApiError(409, 'invalid_response', 'Finish this practice before retrying it');
        state.round++;
        state.results = {};
        await save(DB, owner, id, state, token);
        return json(practiceView(state));
      }
      if (state.completed) throw new ApiError(409, 'already_answered', 'This practice is already complete');
      const item = state.lesson.items.find(i => i.question.id === body.question_id);
      if (!item) throw new ApiError(404, 'not_found', 'Question not in this lesson');
      validatePracticeResponse(item.question, body.response, ApiError);
      const previous = state.results[body.question_id];
      if (previous?.choices.some(c => JSON.stringify(c) === JSON.stringify(body.response))) return json(reply(state, item, previous));
      if (previous?.settled) throw new ApiError(409, 'already_answered', 'This question is already settled');
      let feedback;
      if (!state.grading[body.question_id] && !item.answered) {
        try {
          feedback = await remote(request, '/v1/answers', 'POST', body);
          state.grading[body.question_id] = feedback;
        } catch (error) {
          if (error.code !== 'already_answered') throw error;
          // Recover an upstream response lost after its Elo update, without rating twice.
          item.answered = true;
        }
      }
      if (!feedback) {
        const q = state.grading[body.question_id] ?? bank[body.question_id];
        if (!q) throw new ApiError(503, 'server', 'This question is unavailable. Please try again later.');
        const answer = q.correct_answer ?? q.answer;
        const score = practiceScore(body.response, answer);
        const cached = state.grading[body.question_id];
        const rating = (await remote(request, '/v1/progress')).topics.find(t => t.topic === item.question.topic)?.rating ?? cached?.rating.after ?? 1200;
        feedback = { correct: score === 1, score, correct_answer: answer, explanation: q.explanation,
          rating: { topic: item.question.topic, before: rating, after: rating, delta: 0 },
          question_rating: { before: item.question.difficulty_rating, after: item.question.difficulty_rating },
          ...(q.provenance ? { provenance: q.provenance } : {}) };
        state.grading[body.question_id] ??= feedback;
      }
      item.answered = true;
      const choices = [...(previous?.choices ?? []), body.response];
      const correct = feedback.correct;
      const r = { choices, correct, settled: correct || choices.length >= practiceAttemptLimit(item.question), feedback };
      state.results[body.question_id] = r;
      await save(DB, owner, id, state, token);
      return json(reply(state, item, r));
    } finally {
      await DB.prepare('UPDATE sites_practice_sessions SET locked_until = 0, lock_token = NULL WHERE owner_id = ? AND lesson_id = ? AND lock_token = ?').bind(owner, id, token).run();
    }
  };
}
