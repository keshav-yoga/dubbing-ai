import { RouterProvider } from "react-router-dom";
import routes from "./routers.jsx";

export default function App() {
  return <RouterProvider router={routes} />;
}
