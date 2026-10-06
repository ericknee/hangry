/** Full-page spinner with one line of text, on the same background as the question pages. */
export default function LoadingScreen({ message }: { message: string }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gradient-to-b from-blue-50 via-blue-100 to-blue-200 p-6">
      <div
        role="status"
        aria-label={message}
        className="h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-500"
      />
      <p className="text-blue-900">{message}</p>
    </main>
  );
}
