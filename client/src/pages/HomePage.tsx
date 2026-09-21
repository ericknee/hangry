import { useState } from "react";
import { createSession } from "../api/sessions";

export default function HomePage() {
  const [query, setQuery] = useState("");

  async function start(mode: "solo" | "group") {
    const session = await createSession(mode, query);
    window.location.href = `/session/${session.session_id}`;
  }

  return (
    <main className="mx-auto flex max-w-md flex-col gap-4 p-8">
      <h1 className="text-2xl font-bold">TableTalk</h1>
      <input
        className="rounded border px-3 py-2"
        placeholder="What are you in the mood for?"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="flex gap-2">
        <button className="rounded bg-black px-4 py-2 text-white" onClick={() => start("solo")}>
          Just me
        </button>
        <button className="rounded border px-4 py-2" onClick={() => start("group")}>
          Start a group
        </button>
      </div>
    </main>
  );
}
