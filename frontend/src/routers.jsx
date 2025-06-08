import { lazy } from "react";
import { createBrowserRouter } from "react-router-dom";
// Pages live one directory up from `src/`.
import Dashboard     from "../Pages/Dashboard.jsx";
import ProjectDetail from "../Pages/ProjectDetail.jsx";

const routes = createBrowserRouter([
  { path: "/", element: <Dashboard /> },
  { path: "/project/:id", element: <ProjectDetail /> }
]);

export default routes;
