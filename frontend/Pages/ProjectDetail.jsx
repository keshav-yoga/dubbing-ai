import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import api from "../src/api.jsx";
// Components live under the `src/` directory
import PipelineButtons from "../src/components/PipelineButtons.jsx";
import VideoPlayer from "../src/components/VideoPlayer.jsx";

export default function ProjectDetail() {
  const { id } = useParams();
  const [project, setProject] = useState();
  const [finalVid, setFinalVid] = useState();
  const [subs, setSubs] = useState([]);

  useEffect(()=>{
    (async()=>{
      const res = await api.get(`/upload/project/${id}`);   // implement in backend
      setProject(res.data);
      if(res.data.final){
        setFinalVid(res.data.final.final_video_path);
        setSubs(res.data.final.subtitle_files);
      }
    })();
  }, [id]);

  if(!project) return <p>Loading …</p>;

  return (
    <div>
      <h2>{project.title}</h2>
      <PipelineButtons project={project}/>
      {finalVid && <VideoPlayer src={finalVid} subs={subs}/>}
    </div>
  );
}
