type SkeletonProps = {
  count?: number;
};

export function Skeleton({ count = 3 }: SkeletonProps) {
  return (
    <div className="space-y-3" aria-hidden="true">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="rounded-2xl border border-line bg-surface p-4">
          <div className="h-4 w-2/5 animate-pulse rounded bg-raised" />
          <div className="mt-3 h-3 w-3/5 animate-pulse rounded bg-raised" />
        </div>
      ))}
    </div>
  );
}
