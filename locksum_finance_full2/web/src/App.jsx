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
  const [linkToken, setLinkToken] = useState(null)

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {}

  const isSubscribed =
    user &&
    (user.subscription_status === 'active' || user.subscription_status === 'trialing')

  const isPlusOrPro = user && user.plan !== 'free' && isSubscribed

  const register = async () => {
    await axios.post(`${API}/auth/register`, { email, password })
    alert('Registered; now log in.')
  }

  const login = async () => {
    const res = await axios.post(`${API}/auth/login`, { email, password })
    setToken(res.data.access_token)
    const me = await axios.get(`${API}/auth/me`, {
      headers: { Authorization: `Bearer ${res.data.access_token}` },
    })
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
        alert(
          err.response.data.detail ||
            'Upgrade to Plus or Pro to unlock AI insights.'
        )
      } else {
        alert('Something went wrong loading insights.')
      }
    }
  }

  // NEW: Bank linking (Plaid) stub
  const connectBank = async () => {
    if (!token) {
      alert('Log in first.')
      return
    }
    try {
      const res = await axios.post(
        `${API}/plaid/link-token`,
        {},
        { headers: authHeaders }
      )
      setLinkToken(res.data.link_token)
      alert(
        'Bank link token created. In a real app, this would open Plaid Link.\n\nToken (sandbox/dev): ' +
          res.data.link_token
      )
    } catch (err) {
      if (err.response && err.response.status === 402) {
        alert(
          err.response.data.detail ||
            'Plus or Pro plan required to connect bank accounts.'
        )
      } else {
        alert('Something went wrong creating a bank link.')
      }
    }
  }

  return (
    <div style={{ maxWidth: 960, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <h1>Locksum Finance</h1>
      <p>Personal finance, bank sync, and AI insights with Plus & Pro memberships.</p>

      {/* UPGRADE BANNER */}
      {user && (!isSubscribed || user.plan === 'free') && (
        <div
          style={{
            margin: '1rem 0',
            padding: '0.75rem 1rem',
            borderRadius: '0.5rem',
            border: '1px solid #f59e0b',
            background: '#fffbeb',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>🔒</span>
          <div>
            <strong>Upgrade to Plus or Pro to unlock all features.</strong>
            <div style={{ fontSize: '0.9rem', color: '#92400e' }}>
              Bank sync (Plaid), AI coach, and advanced tools are available on paid plans.
            </div>
          </div>
        </div>
      )}

      {/* ACCOUNT SECTION */}
      <section style={{ marginBottom: '2rem' }}>
        <h2>Account</h2>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
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
        </div>

        {user && (
          <div style={{ marginTop: '1rem', fontSize: '0.95rem' }}>
            <strong>Logged in as:</strong> {user.email} <br />
            <strong>Plan:</strong> {user.plan} ({user.plan_interval}) <br />
            <strong>Status:</strong> {user.subscription_status}
          </div>
        )}
      </section>

      {/* PLANS SECTION */}
      <section style={{ marginBottom: '2rem' }}>
        <h2>Plans</h2>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <div
            style={{
              border: '1px solid #ddd',
              padding: '1rem',
              flex: 1,
              minWidth: 260,
            }}
          >
            <h3>Plus</h3>
            <p>
              <strong>$7 / month</strong> or <strong>$79 / year</strong>
            </p>
            <ul>
              <li>🔒 Bank connections (Plaid)</li>
              <li>🔒 AI spending insights</li>
              <li>🔒 Safe-to-spend &amp; debt planner</li>
              <li>Up to 3 accounts</li>
            </ul>
            <button
              onClick={() => {
                setPlan('plus')
                setInterval('monthly')
              }}
            >
              Choose Plus Monthly
            </button>
            <button
              onClick={() => {
                setPlan('plus')
                setInterval('yearly')
              }}
            >
              Choose Plus Yearly
            </button>
          </div>

          <div
            style={{
              border: '1px solid #ddd',
              padding: '1rem',
              flex: 1,
              minWidth: 260,
            }}
          >
            <h3>Pro</h3>
            <p>
              <strong>$15 / month</strong> or <strong>$159 / year</strong>
            </p>
            <ul>
              <li>🔒 Everything in Plus</li>
              <li>🔒 Up to 10 linked accounts</li>
              <li>🔒 Priority refresh &amp; support</li>
            </ul>
            <button
              onClick={() => {
                setPlan('pro')
                setInterval('monthly')
              }}
            >
              Choose Pro Monthly
            </button>
            <button
              onClick={() => {
                setPlan('pro')
                setInterval('yearly')
              }}
            >
              Choose Pro Yearly
            </button>
          </div>
        </div>

        {token && (
          <div style={{ marginTop: '1rem' }}>
            <button onClick={checkout}>Subscribe with Stripe Checkout</button>
          </div>
        )}
        {!token && (
          <p
            style={{
              fontSize: '0.9rem',
              color: '#4b5563',
              marginTop: '0.5rem',
            }}
          >
            Log in to upgrade your plan.
          </p>
        )}
      </section>

      {/* BANK ACCOUNTS SECTION (Plaid stub, locked) */}
      <section style={{ marginBottom: '2rem' }}>
        <h2>
          Bank Accounts <span style={{ fontSize: '1.2rem' }}>🔒</span>
        </h2>
        {token ? (
          <>
            {!isPlusOrPro && (
              <p style={{ fontSize: '0.9rem', color: '#6b7280' }}>
                Upgrade to Plus or Pro to connect your bank accounts securely via
                Plaid and automatically import your transactions.
              </p>
            )}
            <button onClick={connectBank} disabled={!isPlusOrPro}>
              {isPlusOrPro ? 'Connect Bank (Plaid)' : 'Upgrade to Unlock'}
            </button>
            {linkToken && isPlusOrPro && (
              <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#6b7280' }}>
                Sandbox link token created. In production, this button would open the Plaid
                Link flow using this token.
              </p>
            )}
          </>
        ) : (
          <p>Log in to connect bank accounts.</p>
        )}
      </section>

      {/* AI COACH SECTION */}
      <section>
        <h2>
          {isPlusOrPro ? (
            'AI Coach'
          ) : (
            <>
              AI Coach <span style={{ fontSize: '1.2rem' }}>🔒</span>
            </>
          )}
        </h2>
        {token ? (
          <>
            {!isPlusOrPro && (
              <p style={{ fontSize: '0.9rem', color: '#6b7280' }}>
                Upgrade to Plus or Pro to unlock AI insights tailored to your budgets and
                transactions.
              </p>
            )}
            <button onClick={loadInsights} disabled={!isPlusOrPro}>
              {isPlusOrPro ? 'Get Insights' : 'Upgrade to Unlock'}
            </button>
            {insights && isPlusOrPro && (
              <div style={{ marginTop: '1rem' }}>
                <h3>Summary</h3>
                <ul>
                  {insights.advice.summary.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
                <h3>Warnings</h3>
                <ul>
                  {insights.advice.warnings.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
                <h3>Suggested Actions</h3>
                <ul>
                  {insights.advice.suggested_actions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <p>Log in to see and unlock AI features.</p>
        )}
      </section>
    </div>
  )
}
