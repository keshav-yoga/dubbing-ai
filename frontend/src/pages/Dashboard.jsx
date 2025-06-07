import { useEffect, useState } from "react";
import { listProjects } from "../api.jsx";
import UploadPage from "../components/UploadPage.jsx";
import ProjectCard from "../components/ProjectCard.jsx";

export default function Dashboard() {
  const [projects, setProjects] = useState([]);

  const refresh = async () => {
    const res = await listProjects();
    setProjects(res.data);
  };
  useEffect(()=>{ refresh(); }, []);

  return (
    <div>
      <h2>Dubbing AI Dashboard</h2>
      <UploadPage onUploaded={refresh}/>
      <hr/>
      <h3>Your Projects</h3>
      {projects.map(p => <ProjectCard key={p.id} p={p}/>)}
    </div>
  );
}
