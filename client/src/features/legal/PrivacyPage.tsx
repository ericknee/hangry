import LegalPage, { Bullets, Contact, ExtLink, Section } from "./LegalPage";

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" effective="October 14, 2026">
      <p className="text-ink">
        Hangry helps you pick a restaurant. It is run by an individual in California and is meant for
        people in the United States. This page explains what it collects and what happens to it.
      </p>

      <Section title="What we collect">
        <Bullets>
          <li>
            <strong>Your location.</strong> If you choose &quot;Current location&quot;, your browser
            asks permission and sends your coordinates to our server. If you type a city, we look up
            that city&apos;s coordinates. We store the location rounded to about 110 meters (about 360
            feet) with a random session ID, and use it to run your search.
          </li>
          <li>
            <strong>Your answers.</strong> Meal, price, dietary choice and how far you will travel,
            stored with the session ID.
          </li>
          <li>
            <strong>What you type.</strong> City text is sent to Google to get suggestions and is
            not stored by us. The craving you type (for example, &quot;sushi&quot;) is stored with the
            session ID and sent to Google as part of the search. Please do not type personal
            information into it.
          </li>
          <li>
            <strong>Technical logs.</strong> Our hosting provider&apos;s logs record your IP address,
            the time, and the address requested. That address can include the city text you typed.
          </li>
        </Bullets>
        <p>
          There are no accounts, no cookies, no analytics and no ads. We do not ask for your name or
          email.
        </p>
      </Section>

      <Section title="How we use it">
        <p>Only to find restaurants for you and to run and protect the service.</p>
      </Section>

      <Section title="Who receives it">
        <Bullets>
          <li>
            <strong>Google.</strong> Our server sends your search to Google Maps Platform, including
            your location and search terms. Google may use and keep that data under the{" "}
            <ExtLink href="https://policies.google.com/privacy">Google Privacy Policy</ExtLink>.
            Restaurant photos are fetched by our server, so Google does not see your IP address for
            them. Links to Google Maps are only followed when you click them.
          </li>
          <li>
            <strong>Our hosting providers.</strong> Hangry runs on Google Cloud, and our database is
            kept by Supabase. They handle the data for us.
          </li>
        </Bullets>
        <p>
          We do not sell your information or share it for advertising. We may disclose it if the law
          requires.
        </p>
      </Section>

      <Section title="How long we keep it">
        <Bullets>
          <li>
            Sessions (rounded location, answers and the craving you typed) are deleted automatically
            after 30 days.
          </li>
          <li>Restaurant results are held in server memory for up to 30 minutes.</li>
          <li>Hosting logs are kept for up to 30 days.</li>
          <li>
            Your browser keeps your location choice and answers in session storage until you close
            the tab. This is not a cookie and is not sent anywhere on its own.
          </li>
        </Bullets>
      </Section>

      <Section title="Your choices">
        <p>
          To ask what we hold about you or to have it deleted, email <Contact />. Include the session
          ID, which is the long code in the address bar after /session/. We do not sell personal
          information.
        </p>
      </Section>

      <Section title="Do Not Track">
        <p>
          We do not track you across websites and use no third-party tracking, so there is nothing
          for a Do Not Track signal to change.
        </p>
      </Section>

      <Section title="Children">
        <p>
          Hangry is not directed to children under 13, and we do not knowingly collect their
          information.
        </p>
      </Section>

      <Section title="United States only">
        <p>Hangry is meant for use in the United States.</p>
      </Section>

      <Section title="Changes and contact">
        <p>
          If we change this policy we will update the effective date above. Questions: <Contact />
        </p>
      </Section>
    </LegalPage>
  );
}
