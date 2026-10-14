import Page from "./Page";

/** Full-page spinner with one line of text, on the same background as the question pages. */
export default function LoadingScreen({ message }: { message: string }) {
  return (
    <Page className="items-center">
      <div
        role="status"
        aria-label={message}
        className="h-10 w-10 animate-spin rounded-full border-4 border-line border-t-accent"
      />
      <p className="text-ink">{message}</p>
    </Page>
  );
}
