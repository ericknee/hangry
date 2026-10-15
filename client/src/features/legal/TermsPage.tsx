import { Link } from "react-router-dom";
import { ROUTES } from "../../routes";
import LegalPage, { Bullets, Contact, ExtLink, Section } from "./LegalPage";

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Use" effective="October 14, 2026">
      <p className="text-ink">
        Hangry helps you pick a restaurant. It is run by an individual in California and is meant for
        people in the United States. By using it you agree to these terms.
      </p>

      <Section title="Using Hangry">
        <p>
          You may use Hangry for your own personal, non-commercial use. It is provided as is, and we
          may change it or stop it at any time.
        </p>
      </Section>

      <Section title="Restaurant information">
        <p>
          Restaurant details, ratings, prices, hours and photos come from Google Maps and may be
          wrong or out of date. Check with the restaurant before you go. Photos belong to the people
          who took them. The dietary options (vegetarian, vegan, halal) are search filters, not a
          promise about what a restaurant serves, so do not rely on them for allergies or religious
          requirements.
        </p>
      </Section>

      <Section title="Google Maps">
        <p>
          Hangry includes Google Maps features and content. Your use of those features and content
          is subject to the then-current{" "}
          <ExtLink href="https://maps.google.com/help/terms_maps/">
            Google Maps/Google Earth Additional Terms of Service
          </ExtLink>{" "}
          and the <ExtLink href="https://policies.google.com/privacy">Google Privacy Policy</ExtLink>.
          Hangry is not affiliated with or endorsed by Google.
        </p>
      </Section>

      <Section title="Acceptable use">
        <p>Do not:</p>
        <Bullets>
          <li>scrape or copy Hangry or the Google content it shows, or build a database from it;</li>
          <li>send automated or excessive requests, or try to get around limits on use;</li>
          <li>use Hangry for anything illegal.</li>
        </Bullets>
      </Section>

      <Section title="Your location">
        <p>
          You choose whether to share your location. How we handle it is explained in the{" "}
          <Link to={ROUTES.privacy} className="font-semibold text-accent underline">
            Privacy Policy
          </Link>
          .
        </p>
      </Section>

      <Section title="No warranty and limits on liability">
        <p>
          Hangry is provided without warranties of any kind. To the extent the law allows, we are not
          liable for any loss or harm from using it, including a closed restaurant, a bad meal or a
          dietary or allergy problem.
        </p>
      </Section>

      <Section title="Changes and governing law">
        <p>
          We may update these terms and will change the effective date at the top when we do. These
          terms are governed by the laws of the State of California.
        </p>
      </Section>

      <Section title="Contact">
        <p>
          Questions: <Contact />
        </p>
      </Section>
    </LegalPage>
  );
}
