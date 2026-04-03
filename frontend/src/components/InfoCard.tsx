type StatCardProps = {
  label: string;
  value: string | number;
  hint: string;
};

type ModuleCardProps = {
  title: string;
  text: string;
};

export function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{hint}</small>
    </div>
  );
}

export function ModuleCard({ title, text }: ModuleCardProps) {
  return (
    <article className="module-card">
      <h3>{title}</h3>
      <p>{text}</p>
    </article>
  );
}