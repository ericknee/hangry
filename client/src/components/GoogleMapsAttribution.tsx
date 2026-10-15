import logoDark from "../assets/googleMaps/GoogleMaps_Logo_DarkGray/GoogleMaps_Logo_DarkGray.svg";
import logoWhite from "../assets/googleMaps/GoogleMaps_Logo_White/GoogleMaps_Logo_White.svg";

/**
 * Google Maps logo that Google requires wherever Places data is shown without a Google map.
 * Both plain-background variants are 18px tall (Google allows 16-19px); don't resize, recolor or
 * stretch them. Use the dark-gray one on light surfaces and the white one on dark surfaces; on a
 * busy background (e.g. over a photo) use the WithLightOutline / WithDarkOutline assets instead.
 * Keep it visible and unobscured, near the top or bottom of the content it describes.
 * https://developers.google.com/maps/documentation/places/web-service/policies
 */
export default function GoogleMapsAttribution({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex shrink-0 ${className}`}>
      <img src={logoDark} alt="Google Maps" width={98} height={18} className="block dark:hidden" />
      <img src={logoWhite} alt="Google Maps" width={98} height={18} className="hidden dark:block" />
    </span>
  );
}
