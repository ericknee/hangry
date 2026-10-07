import { BrowserRouter, Route, Routes } from "react-router-dom";
import LocationPage from "./features/location/LocationPage";
import AfterPage from "./features/setup/AfterPage";
import DietaryPage from "./features/setup/DietaryPage";
import PricePage from "./features/setup/PricePage";
import SearchPage from "./features/setup/SearchPage";
import TravelPage from "./features/setup/TravelPage";
import ShortlistPage from "./features/shortlist/ShortlistPage";
import ToastProvider from "./components/Toast";
import { ROUTES } from "./routes";

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
          <Routes>
          <Route path={ROUTES.home} element={<LocationPage />} />
          <Route path={ROUTES.search} element={<SearchPage />} />
          <Route path={ROUTES.setupAfter} element={<AfterPage />} />
          <Route path={ROUTES.setupPrice} element={<PricePage />} />
          <Route path={ROUTES.setupDietary} element={<DietaryPage />} />
          <Route path={ROUTES.setupTravel} element={<TravelPage />} />
          <Route path={ROUTES.shortlist} element={<ShortlistPage />} />
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}
