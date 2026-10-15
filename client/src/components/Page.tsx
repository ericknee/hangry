import type { ReactNode } from "react";
import LegalLinks from "./LegalLinks";

interface PageProps {
  children: ReactNode;
  /** Gap between children; the setup questions use a roomier one. */
  gap?: "gap-4" | "gap-6";
  /** Extra classes for the content column (e.g. `items-center`). */
  className?: string;
}

/** Full-screen themed page with one centered, phone-width column. */
export default function Page({ children, gap = "gap-4", className = "" }: PageProps) {
  return (
    <main className="page">
      <div className={`flex w-full max-w-md flex-col ${gap} ${className}`}>
        {children}
        <LegalLinks />
      </div>
    </main>
  );
}
