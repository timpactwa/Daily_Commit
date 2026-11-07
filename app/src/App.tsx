import { useState, type FormEvent } from 'react';
import { Link, Navigate, NavLink, Route, Routes, useNavigate } from 'react-router-dom';
import { api, getUserId } from './api';
import { Lesson } from './screens/Lesson';
import { ErrorNotice } from './ui';
function Onboarding() {
  const [name, setName] = useState(''); const [busy, setBusy] = useState(false); const [error, setError] = useState<unknown>(); const navigate = useNavigate();
  async function submit(event?: FormEvent) { event?.preventDefault(); if (!name.trim() || busy) return; setBusy(true); setError(undefined); try { await api.createUser(name.trim()); navigate('/placement'); } catch (err) { setError(err); } finally { setBusy(false); } }
  return <div className="onboarding"><p className="eyebrow">FIVE MINUTES. FOR YOUR FUTURE.</p><h1>Small commits.<br/>Real progress<span className="green">.</span></h1><p>Build your interview instincts, one day at a time. System design and debugging practice that grows with you.</p><div className="card"><h2>Make your first commit.</h2><p>A quick placement finds your starting point. No prep needed.</p><form onSubmit={submit}><label htmlFor="name">What should we call you?</label><input id="name" autoComplete="given-name" maxLength={60} required value={name} onChange={e => setName(e.target.value)} placeholder="Your first name"/><button className="primary full" disabled={busy || !name.trim()}>{busy ? 'Setting up…' : 'Find my starting point →'}</button></form>{error && <ErrorNotice error={error} retry={submit}/>}</div></div>;
}
function HomePlaceholder() { return getUserId() ? <div className="card"><h1>Your daily commit.</h1><Link className="primary" to="/lesson">Start today’s lesson →</Link></div> : <Navigate to="/onboarding" replace/>; }
export function App() {
  return <div className="app"><header><NavLink className="brand" to="/">[d<span>c</span>] <strong>daily commit<span className="brand-dot">.</span></strong></NavLink><span className="eyebrow">A LITTLE, EVERY DAY</span></header><main><Routes><Route path="/" element={<HomePlaceholder/>}/><Route path="/onboarding" element={<Onboarding/>}/><Route path="/lesson" element={<Lesson/>}/>{['/placement', '/placement/result', '/lesson/done', '/progress', '/tomorrow'].map(path => <Route key={path} path={path} element={<div className="card"><h2>Your next step is on its way.</h2><Link to="/">Back to today →</Link></div>}/>)}<Route path="*" element={<div className="card"><h1>Wrong turn.</h1><Link to="/">Back to today →</Link></div>}/></Routes></main><nav aria-label="Main navigation"><NavLink to="/" end>⌂ <span>Today</span></NavLink><NavLink to="/progress">↗ <span>Progress</span></NavLink></nav></div>;
}
