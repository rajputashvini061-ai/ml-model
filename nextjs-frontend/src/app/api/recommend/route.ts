import { NextRequest, NextResponse } from "next/server";

const RENDER_API_URL = (process.env.RENDER_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const RENDER_API_KEY = (process.env.RENDER_API_KEY || "").trim();

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (RENDER_API_KEY) {
      headers["x-api-key"] = RENDER_API_KEY;
    }

    const res = await fetch(`${RENDER_API_URL}/api/recommend`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      cache: "no-store",
      signal: AbortSignal.timeout(55000),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json(
      { error: "Render ML API is waking up or unreachable. Please retry in a few seconds." },
      { status: 502 }
    );
  }
}
