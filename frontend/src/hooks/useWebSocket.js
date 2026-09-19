import { useEffect, useRef, useState, useCallback } from 'react'

export function useWebSocket(url = 'ws://localhost:8000/ws/simulation') {
  const [snapshot, setSnapshot] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)

  const connect = useCallback(() => {
    try {
      // Connect to simulation WebSocket
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setError(null)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'simulation_state') {
            setSnapshot(data)
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onerror = (err) => {
        setError('WebSocket error')
      }

      ws.onclose = () => {
        setIsConnected(false)
        // Automatic reconnection attempt
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, 1500)
      }
    } catch (err) {
      setError(err.message)
      reconnectTimeoutRef.current = setTimeout(() => {
        connect()
      }, 2000)
    }
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  const send = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof message === 'string' ? message : JSON.stringify(message))
    }
  }, [])

  return { snapshot, isConnected, error, send }
}
