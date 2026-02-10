interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.toLowerCase();

  let classes = 'px-2.5 py-0.5 rounded-full text-xs font-medium inline-block';

  if (normalized === 'in stock' || normalized === 'ok') {
    classes += ' bg-green-100 text-green-800';
  } else if (normalized === 'low' || normalized === 'low stock') {
    classes += ' bg-red-100 text-red-800';
  } else if (normalized === 'archived') {
    classes += ' bg-gray-100 text-gray-600';
  } else {
    classes += ' bg-yellow-100 text-yellow-800';
  }

  return <span className={classes}>{status}</span>;
}
