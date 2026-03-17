type UnauthorizedPayload = {
  status: number;
  code: string;
  message: string;
  method: string;
  path: string;
};

type UnauthorizedHandler = (payload: UnauthorizedPayload) => void;

const listeners = new Set<UnauthorizedHandler>();

export function onUnauthorized(handler: UnauthorizedHandler): () => void {
  listeners.add(handler);
  return () => listeners.delete(handler);
}

export function emitUnauthorized(payload: UnauthorizedPayload): void {
  for (const listener of listeners) {
    listener(payload);
  }
}
