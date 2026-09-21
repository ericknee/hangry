import { BrowserRouter, Route, Routes } from "react-router-dom";
import ElicitationPage from "./pages/ElicitationPage";
import HomePage from "./pages/HomePage";
import ShortlistPage from "./pages/ShortlistPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/session/:sessionId" element={<ElicitationPage />} />
        <Route path="/session/:sessionId/shortlist" element={<ShortlistPage />} />
      </Routes>
    </BrowserRouter>
  );
}
