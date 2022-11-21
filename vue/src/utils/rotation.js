export default function rotateFix(rotation) {
  let rotationDegree = rotation;
  while (rotationDegree < 0) {
    rotationDegree += 360;
  }
  while (rotationDegree > 360) {
    rotationDegree -= 360;
  }
  switch (rotationDegree) {
    case 90:
    case 180:
    case 270:
      return rotationDegree;
    default:
      return 0;
  }
}
