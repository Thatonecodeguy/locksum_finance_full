import React, { useState } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState('')
  const [user, setUser] = useState(null)
  const [plan, setPlan] = useState('plus')
  const [interval, setInterval] = useState('monthly')
  const [insights, setInsights] = useState(null)

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {}

  const register = async () => {
    await axios.post(`${API}/auth/register`, { email, password })
    alert('Registered; now log in.')
  }

  const login = async () => {
    const res = await axios.post(`${API}/auth/login`, { email, password })
    setToken(res.data.access_token)
    const me = await axios.get(`${API}/auth/me`, { headers: authHeaders })
    setUser(me.data)
  }

  const checkout = async () => {
    try {
      const res = await axios.post(
      `${API}/billing/checkout-session`,
      { plan, interval },
      { headers: authHeaders }
    )
    window.location.href = res.data.url
    } catch (err) {
      if (err.response && err.response.status === 402) {
        alert(err.response.data.detail || 'Upgrade required to use this feature.')
      } else {
        alert('Something went wrong starting checkout.')
      }
    }

  const loadInsights = async () => {
    try {
      const res = await axios.post(
      `${API}/ai/insights`,
      { monthly_savings_target: 300 },
      { headers: authHeaders }
    )
    setInsights(res.data)
    } catch (err) {
      if (err.response && err.response.status === 402) {
        alert(err.response.data.detail || 'Upgrade to Plus or Pro to unlock AI insights.')
      } else {
        alert('Something went wrong loading insights.')
      }
    }

  return (
    <div style={{ maxWidth: 800, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <h1>Locksum Finance</h1>
      <p>Personal finance, bank sync, and AI insights with Plus & Pro memberships.</p>

      <section style={{ marginBottom: '2rem' }}>
        <h2>Account</h2>
        <input
          placeholder="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
        />
        <input
          placeholder="password"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />
        <button onClick={register}>Register</button>
        <button onClick={login}>Login</button>

        {user && (
          <div style={{ marginTop: '1rem' }}>
            <strong>Logged in as:</strong> {user.email} <br />
            <strong>Plan:</strong> {user.plan} ({user.plan_interval}) <br />
            <strong>Status:</strong> {user.subscription_status}
          </div>
        )}
      </section>

      <section style={{ marginBottom: '2rem' }}>
        <h2>Plans</h2>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <div style={{ border: '1px solid #ddd', padding: '1rem', flex: 1 }}>
            <h3>Plus</h3>
            <p>$7 / month or $79 / year</p>
            <ul>
              <li>Bank connections (Plaid)</li>
              <li>AI spending insights</li>
              <li>Safe-to-spend & debt planner</li>
              <li>Up to 3 accounts</li>
            </ul>
            <button onClick={() => { setPlan('plus'); setInterval('monthly') }}>
              Choose Plus Monthly
            </button>
            <button onClick={() => { setPlan('plus'); setInterval('yearly') }}>
              Choose Plus Yearly
            </button>
          </div>
          <div style={{ border: '1px solid #ddd', padding: '1rem', flex: 1 }}>
            <h3>Pro</h3>
            <p>$15 / month or $159 / year</p>
            <ul>
              <li>Everything in Plus</li>
              <li>Up to 10 linked accounts</li>
              <li>Priority refresh & support</li>
            </ul>
            <button onClick={() => { setPlan('pro'); setInterval('monthly') }}>
              Choose Pro Monthly
            </button>
            <button onClick={() => { setPlan('pro'); setInterval('yearly') }}>
              Choose Pro Yearly
            </button>
          </div>
        </div>
        {token && (
          <div style={{ marginTop: '1rem' }}>
            <button onClick={checkout}>Subscribe with Stripe Checkout</button>
          </div>
        )}
      </section>

      <section>
        <h2>AI Coach</h2>
        {token ? (
          <>
            <button onClick={loadInsights}>Get Insights</button>
            {insights && (
              <div style={{ marginTop: '1rem' }}>
                <h3>Summary</h3>
                <ul>
                  {insights.advice.summary.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
                <h3>Warnings</h3>
                <ul>
                  {insights.advice.warnings.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
                <h3>Suggested Actions</h3>
                <ul>
                  {insights.advice.suggested_actions.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
          </>
        ) : (
          <p>Log in to see personalized AI insights.</p>
        )}
      </section>
    </div>
  )
}
