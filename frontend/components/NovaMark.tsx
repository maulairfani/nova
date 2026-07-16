export function NovaMark({ size = 18 }: { size?: number }) {
  return (
    <div
      className="nova-serif"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        fontStyle: "italic",
        fontWeight: 600,
        fontSize: size,
        lineHeight: 1,
        color: "var(--nova-ink)",
      }}
    >
      <span
        style={{
          width: size * 0.47,
          height: size * 0.47,
          borderRadius: 2,
          background: "var(--nova-accent)",
          display: "inline-block",
          transform: "rotate(8deg)",
          flex: "none",
        }}
      />
      Nova
    </div>
  );
}
