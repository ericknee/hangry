const token = (name) => `rgb(var(--${name}) / <alpha-value>)`;

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "media",
  future: {
    // Wrap hover: styles in @media (hover: hover) so taps don't leave a sticky hover state on touch screens.
    hoverOnlyWhenSupported: true,
  },
  theme: {
    extend: {
      colors: {
        canvas: token("canvas"),
        surface: token("surface"),
        ink: token("ink"),
        muted: token("muted"),
        accent: token("accent"),
        "accent-hover": token("accent-hover"),
        "on-accent": token("on-accent"),
        danger: token("danger"),
        line: token("line"),
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
