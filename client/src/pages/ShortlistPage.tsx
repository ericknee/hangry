import { useParams } from "react-router-dom";

export default function ShortlistPage() {
  const { sessionId } = useParams();

  // TODO Phase 1/3: fetch the real shortlist + explanation for this session.
  return (
    <main className="mx-auto flex max-w-md flex-col gap-4 p-8">
      <h1 className="text-xl font-bold">Your shortlist</h1>
      <p className="text-sm text-gray-500">Session {sessionId}</p>
    </main>
  );
}
