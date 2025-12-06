import React, { useState } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState('')
  const [transactions, setTransactions] = useState([])

  const register = async () => {
    await axios.post(`${API}/auth/register`, { email, password })
    alert('Registered; now log in.')
  }

  const login = async () => {
    const res = await axios.post(`${API}/auth/login`, { email, password })
    setToken(res.data.access_token)
  }

  const loadTxns = async () => {
    const res = await axios.get(`${API}/transactions`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    setTransactions(res.data)
  }

  return (
    <div style={{ maxWidth: 480, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <h1>Locksum Finance</h1>
      <p>Simple budgets + transactions with Plaid/Stripe-ready backend.</p>
      <div>
        <input placeholder="email" value={email} onChange={e => setEmail(e.target.value)} />
        <input placeholder="password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
        <button onClick={register}>Register</button>
        <button onClick={login}>Login</button>
      </div>
      {token && (
        <>
          <h2>Transactions</h2>
          <button onClick={loadTxns}>Load</button>
          <ul>
            {transactions.map(t => (
              <li key={t.id}>{t.date} - {t.name}: ${t.amount} [{t.category}]</li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
