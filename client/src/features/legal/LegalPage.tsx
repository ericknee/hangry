import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ROUTES } from "../../routes";

export const CONTACT_EMAIL = "hungrymf7@gmail.com";

/** Readable long-form page for the Terms and Privacy Policy. */
export default function LegalPage({
  title,
  effective,
  children,
}: {
  title: string;
  effective: string;
  children: ReactNode;
}) {
  return (
    <main className="page items-start">
      <article className="flex w-full max-w-prose flex-col gap-3 pb-8">
        <Link to={ROUTES.home} className="text-sm font-semibold text-accent underline">
          ← Back to Hangry
        </Link>
        <h1 className="title-lg">{title}</h1>
        <p className="text-sm text-muted">Effective {effective}</p>
        {children}
      </article>
    </main>
  );
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-4 flex flex-col gap-2 text-ink">
      <h2 className="title">{title}</h2>
      {children}
    </section>
  );
}

export function Bullets({ children }: { children: ReactNode }) {
  return <ul className="list-disc space-y-1 pl-5">{children}</ul>;
}

export function ExtLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="font-semibold text-accent underline">
      {children}
    </a>
  );
}

export function Contact() {
  return <ExtLink href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</ExtLink>;
}
