/** Fixed ambient layer behind the app shell: drifting lava blobs, a dark vignette and film grain.
 *  Purely decorative; animations stop under prefers-reduced-motion. */
export function Backdrop() {
  return (
    <div className="backdrop" aria-hidden="true">
      <div className="lava">
        <span className="blob b1" />
        <span className="blob b2" />
        <span className="blob b3" />
        <span className="blob b4" />
        <span className="blob b5" />
      </div>
      <div className="lava-shade" />
      <svg className="grain">
        <filter id="grainf">
          <feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves={2} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grainf)" />
      </svg>
    </div>
  );
}
