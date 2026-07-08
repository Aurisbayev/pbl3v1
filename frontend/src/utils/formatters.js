export function formatTime(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return "Unknown time";
  }

  const minutes = Number(value);

  if (minutes < 60) {
    return `${Math.round(minutes)} min`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = Math.round(minutes % 60);

  if (remainingMinutes === 0) {
    return `${hours} hr`;
  }

  return `${hours} hr ${remainingMinutes} min`;
}

export function formatDistance(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return "Unknown distance";
  }

  const kilometers = Number(value);

  if (kilometers >= 1) {
    return `${kilometers.toFixed(1)} km`;
  }

  return `${Math.round(kilometers * 1000)} m`;
}

export function formatScenicScore(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return "Unknown score";
  }

  return `${Math.round(Number(value) * 100)}%`;
}