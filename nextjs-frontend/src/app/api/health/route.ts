import { NextResponse } from "next/server";

const RENDER_API_URL = (process.env.RENDER_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export async function GET() {
  try {
    const res = await fetch(`${RENDER_API_URL}/api/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(45000),
    });
    const data = await res.json();
    return NextResponse.json({ ok: res.ok, backend: data }, { status: res.ok ? 200 : 502 });
  } catch {
    return NextResponse.json(
      { ok: false, error: "Render ML API is waking up or unreachable." },
      { status: 502 }
    );
  }
}
