import React from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import Dashboard from './components/Dashboard'

export default function App() {
  const { snapshot, isConnected } = useWebSocket()

  return <Dashboard snapshot={snapshot} isConnected={isConnected} />
}
