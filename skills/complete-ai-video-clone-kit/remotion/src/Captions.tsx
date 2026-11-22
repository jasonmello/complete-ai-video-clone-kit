import { createTikTokStyleCaptions, type Caption } from "@remotion/captions";
import { AbsoluteFill, Sequence, spring, useCurrentFrame, useVideoConfig } from "remotion";

export type CaptionsProps = {
  width: number;
  height: number;
  fps: number;
  durationInSeconds: number;
  captions: Caption[];
  wordsPerPageMs: number; // higher = more words per page, lower = word by word
};

const ACCENT = "#ff4d2e"; // DESIGN.md accent

// Transparent layer: assemble.py composites it over the video as an overlay.
export const Captions: React.FC<CaptionsProps> = ({ captions, wordsPerPageMs }) => {
  const { fps } = useVideoConfig();
  const { pages } = createTikTokStyleCaptions({ captions, combineTokensWithinMilliseconds: wordsPerPageMs });
  return (
    <AbsoluteFill>
      {pages.map((page, i) => {
        const from = Math.round((page.startMs / 1000) * fps);
        const nextStart = pages[i + 1]?.startMs ?? page.startMs + page.durationMs;
        const length = Math.max(1, Math.round(((nextStart - page.startMs) / 1000) * fps));
        return (
          <Sequence key={i} from={from} durationInFrames={length} layout="none">
            <Page tokens={page.tokens} pageStartMs={page.startMs} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const Page: React.FC<{ tokens: { text: string; fromMs: number; toMs: number }[]; pageStartMs: number }> = ({
  tokens,
  pageStartMs,
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const nowMs = pageStartMs + (frame / fps) * 1000;
  const pop = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 6 });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: "22%" }}>
      <div
        style={{
          width: width * 0.86,
          textAlign: "center",
          fontFamily: "-apple-system, Helvetica, Arial, sans-serif",
          fontWeight: 800,
          fontSize: width * 0.085,
          lineHeight: 1.15,
          whiteSpace: "pre-wrap",
          transform: `scale(${0.9 + 0.1 * pop})`,
          WebkitTextStroke: `${width * 0.006}px #000`,
          paintOrder: "stroke fill",
          textShadow: "0 4px 18px rgba(0,0,0,.55)",
        }}
      >
        {tokens.map((t, i) => (
          <span key={i} style={{ color: nowMs >= t.fromMs && nowMs < t.toMs ? ACCENT : "#fff" }}>
            {t.text}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};
