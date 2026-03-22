export interface ApiErrorPayload {
  code?: string;
  message?: string;
}

export class HttpError extends Error {
  status: number;
  code: string;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message ?? "Request failed");
    this.status = status;
    this.code = payload.code ?? "REQUEST_FAILED";
  }
}

export async function requestJson<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(input, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? ((await response.json()) as unknown)
    : { message: await response.text() };

  if (!response.ok) {
    throw new HttpError(response.status, payload as ApiErrorPayload);
  }

  return payload as T;
}
