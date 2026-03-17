const unauthorizedListeners = new Set();

export function onUnauthorized(listener) {
  if (typeof listener !== "function") {
    return () => {};
  }

  unauthorizedListeners.add(listener);

  return () => {
    unauthorizedListeners.delete(listener);
  };
}

export function emitUnauthorized(event = {}) {
  for (const listener of unauthorizedListeners) {
    try {
      listener(event);
    } catch {
      // Listener failures should not break request lifecycle.
    }
  }
}

