import { BrowserRouter, Route, Routes } from "react-router-dom";
import LocationPage from "./pages/LocationPage";
import SearchPage from "./pages/SearchPage";
import AfterPage from "./pages/setup/AfterPage";
import DietaryPage from "./pages/setup/DietaryPage";
import PricePage from "./pages/setup/PricePage";
import TravelPage from "./pages/setup/TravelPage";
import ShortlistPage from "./pages/ShortlistPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LocationPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/session/:sessionId/setup/after" element={<AfterPage />} />
        <Route path="/session/:sessionId/setup/price" element={<PricePage />} />
        <Route path="/session/:sessionId/setup/dietary" element={<DietaryPage />} />
        <Route path="/session/:sessionId/setup/travel" element={<TravelPage />} />
        <Route path="/session/:sessionId/shortlist" element={<ShortlistPage />} />
      </Routes>
    </BrowserRouter>
  );
}
