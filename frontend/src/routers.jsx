import { lazy } from "react";
import { createBrowserRouter } from "react-router-dom";
import Dashboard     from "./pages/Dashboard.jsx";
import ProjectDetail from "./pages/ProjectDetail.jsx";

const routes = createBrowserRouter([
  { path: "/", element: <Dashboard /> },
  { path: "/project/:id", element: <ProjectDetail /> }
]);

export default routes;
