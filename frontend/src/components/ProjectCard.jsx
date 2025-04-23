import { Link } from "react-router-dom";

export default function ProjectCard({ p }) {
  return (
    <div className="card">
      <h4>{p.title}</h4>
      <p>ID: {p.id}</p>
      <Link to={`/project/${p.id}`}>Open</Link>
    </div>
  );
}
