import { Link } from "react-router-dom";
import { ROUTES } from "../routes";

/** Terms and Privacy links, shown at the bottom of every page. */
export default function LegalLinks() {
  return (
    <nav aria-label="Legal" className="mt-4 flex justify-center gap-4 text-xs text-muted">
      <Link to={ROUTES.terms} className="underline">
        Terms
      </Link>
      <Link to={ROUTES.privacy} className="underline">
        Privacy
      </Link>
    </nav>
  );
}
