import { Routes, Route } from "react-router-dom";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/upload" element={<UploadPage />} />
      {/* add more routes here */}
    </Routes>
  );
}
