import { Composition, type CalculateMetadataFunction } from "remotion";
import { Captions, type CaptionsProps } from "./Captions";
import { Title, type TitleProps } from "./Title";

// Every composition takes its size, fps and length from props, so the same
// plan.json values drive both the FFmpeg assembly and these overlays.
type Frame = { width: number; height: number; fps: number; durationInSeconds: number };

function fromProps<T extends Frame>(): CalculateMetadataFunction<T> {
  return ({ props }) => ({
    width: props.width,
    height: props.height,
    fps: props.fps,
    durationInFrames: Math.max(1, Math.round(props.durationInSeconds * props.fps)),
  });
}

const frame: Frame = { width: 1080, height: 1920, fps: 30, durationInSeconds: 3 };

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Captions"
      component={Captions}
      calculateMetadata={fromProps<CaptionsProps>()}
      durationInFrames={90}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        ...frame,
        wordsPerPageMs: 1200,
        captions: [
          { text: "Cut", startMs: 0, endMs: 400, timestampMs: null, confidence: null },
          { text: " on", startMs: 400, endMs: 700, timestampMs: null, confidence: null },
          { text: " the", startMs: 700, endMs: 900, timestampMs: null, confidence: null },
          { text: " beat", startMs: 900, endMs: 1600, timestampMs: null, confidence: null },
        ],
      }}
    />
    <Composition
      id="Title"
      component={Title}
      calculateMetadata={fromProps<TitleProps>()}
      durationInFrames={60}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{ ...frame, durationInSeconds: 2, title: "TITLE", subtitle: "subtitle here", background: "#0d0d10" }}
    />
  </>
);
