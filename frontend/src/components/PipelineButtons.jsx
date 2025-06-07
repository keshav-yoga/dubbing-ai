import { useState } from "react";
import {
  runASR, runScriptProcess, runTTS,
  runLipSync, runMixing, runFinalOutput
} from "../api.jsx";

export default function PipelineButtons({ project }) {
  const [log, setLog] = useState("");

  const step = async (fn, label, arg) => {
    setLog(`Running ${label} …`);
    const res = await fn(arg);
    setLog(`${label} OK`);
    return res.data;
  };

  const runAll = async () => {
    try {
      const asr   = await step(runASR, "ASR", project.id);
      const sp    = await step(runScriptProcess, "Script→Translate", [project.id, ["en"]]);
      const psid  = sp.processed_scripts[0].id;
      const tts   = await step(runTTS, "TTS", psid);
      const lip   = await step(runLipSync, "Lip‑Sync", tts.tts_generation_id);
      const mix   = await step(runMixing, "Mixing", lip.lip_sync_job_id);
      const final = await step(runFinalOutput, "Final Output", mix.audio_mix_job_id);
      setLog(`DONE → ${final.final_video_path}`);
    } catch (e) {
      setLog("Pipeline error: " + e.message);
    }
  };

  return (
    <div>
      <button onClick={runAll}>Run Full Pipeline</button>
      <pre>{log}</pre>
    </div>
  );
}
