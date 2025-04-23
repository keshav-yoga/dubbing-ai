import { useState } from "react";
import { uploadVideo } from "../api.js";

export default function UploadPage({ onUploaded }) {
  const [title, setTitle] = useState("");
  const [file, setFile]   = useState();
  const [msg, setMsg]     = useState("");

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      setMsg("Uploading …");
      const res = await uploadVideo(title, file);
      setMsg("Uploaded!");
      onUploaded(res.data.project_id);
    } catch (err) {
      setMsg(err.message);
    }
  };

  return (
    <div>
      <h3>New Project</h3>
      <form onSubmit={handleSubmit}>
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Project Title" required/>
        <input type="file" accept="video/*" onChange={e => setFile(e.target.files[0])} required/>
        <button>Upload</button>
      </form>
      {msg && <p>{msg}</p>}
    </div>
  );
}
