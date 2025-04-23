import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE + "/api",
  timeout: 45_000
});

export const uploadVideo = async (title, file) => {
  const fd = new FormData();
  fd.append("title", title);
  fd.append("file", file);
  return api.post("/upload/", fd);
};

export const runASR           = pid => api.post(`/asr/process/${pid}`);
export const runScriptProcess = (pid, langs) =>
  api.post(`/script_process/process/${pid}`, { target_languages: langs });
export const runTTS           = psid => api.post(`/tts/generate/${psid}`, { voice_name: "local_coqui_default" });
export const runLipSync       = ttsid => api.post(`/lip_sync/process/${ttsid}`);
export const runMixing        = lsid  => api.post(`/mixing/process/${lsid}`);
export const runFinalOutput   = mixid => api.post(`/final_output/generate/${mixid}`, {
  include_subtitles: true,
  subtitle_language_codes: ["en"]
});

// simple listings
export const listProjects = () => api.get("/upload/projects"); // implement in backend if needed
export default api;
