import { useEffect, useRef, useState, useCallback } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export function useSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const socketRef = useRef(null);

  const connect = useCallback((token) => {
    if (socketRef.current?.connected) {
      return;
    }

    socketRef.current = io(SOCKET_URL, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
    });

    socketRef.current.on('disconnect', () => {
      console.log('Socket disconnected');
      setIsConnected(false);
    });

    socketRef.current.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
      setIsConnected(false);
    });

    socketRef.current.on('connected', (data) => {
      console.log('Socket authenticated:', data);
    });
  }, []);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const joinThread = useCallback((threadId) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('join_thread', { thread_id: threadId });
    }
  }, []);

  const leaveThread = useCallback((threadId) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('leave_thread', { thread_id: threadId });
    }
  }, []);

  const sendTyping = useCallback((threadId, isTyping = true) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('typing', { thread_id: threadId, is_typing: isTyping });
    }
  }, []);

  // ---- Subscription helpers ----
  // Each on* registers a listener and returns an unsubscribe function so the
  // caller can pair it with React's effect cleanup. Without this, every
  // re-render stacked another listener and incoming messages fired N times.
  const _subscribe = (event, callback, withLastMessage = false) => {
    const s = socketRef.current;
    if (!s) return () => {};
    const wrapped = (data) => {
      if (withLastMessage) setLastMessage(data);
      callback(data);
    };
    s.on(event, wrapped);
    return () => s.off(event, wrapped);
  };

  const onNewMessage = useCallback(
    (callback) => _subscribe('new_message', callback, true),
    []
  );
  const onUserTyping = useCallback(
    (callback) => _subscribe('user_typing', callback),
    []
  );
  const onDatePlanUpdated = useCallback(
    (callback) => _subscribe('date_plan_updated', callback),
    []
  );
  const onNewMatch = useCallback(
    (callback) => _subscribe('new_match', callback),
    []
  );
  const onNotification = useCallback(
    (callback) => _subscribe('notification', callback),
    []
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  return {
    isConnected,
    lastMessage,
    connect,
    disconnect,
    joinThread,
    leaveThread,
    sendTyping,
    onNewMessage,
    onUserTyping,
    onDatePlanUpdated,
    onNewMatch,
    onNotification,
    socket: socketRef.current,
  };
}

export default useSocket;
