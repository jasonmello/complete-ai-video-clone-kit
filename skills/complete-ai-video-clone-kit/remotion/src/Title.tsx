import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export type TitleProps = {
  width: number;
  height: number;
  fps: number;
  durationInSeconds: number;
  title: string;
  subtitle: string;
  background: string; // "transparent" to render as an overlay
};

// Same look and timing as scripts/motion_example.html (DESIGN.md), in Remotion.
export const Title: React.FC<TitleProps> = ({ title, subtitle, background }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ease = (startS: number) =>
    interpolate(frame, [startS * fps, (startS + 0.5) * fps], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.out(Easing.cubic),
    });
  const a = ease(0), c = ease(0.35), d = ease(0.6);
  return (
    <AbsoluteFill
      style={{
        background,
        justifyContent: "center",
        alignItems: "center",
        gap: "2vh",
        flexDirection: "column",
        fontFamily: "-apple-system, Helvetica, sans-serif",
      }}
    >
      <h1 style={{ color: "#fff", fontSize: "11vw", margin: 0, letterSpacing: "-.03em", opacity: a, transform: `translateY(${(1 - a) * 8}vh)` }}>
        {title}
      </h1>
      <div style={{ height: "1.2vh", background: "#ff4d2e", width: `${c * 60}vw` }} />
      <p style={{ color: "#bbb", fontSize: "4.5vw", margin: 0, opacity: d, transform: `translateY(${(1 - d) * 3}vh)` }}>
        {subtitle}
      </p>
    </AbsoluteFill>
  );
};
