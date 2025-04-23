export default function VideoPlayer({ src, subs }) {
  return (
    <video controls width="640">
      <source src={src} type="video/mp4"/>
      {subs?.map((s,i)=>(
        <track key={i} label={s.language_code} srcLang={s.language_code}
               src={s.file_path} kind="subtitles" default={i===0}/>
      ))}
      Your browser does not support the video tag.
    </video>
  );
}
