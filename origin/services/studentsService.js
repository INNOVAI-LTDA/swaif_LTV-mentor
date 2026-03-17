import {
  listCommandCenterStudents,
  getCommandCenterStudentDetail,
} from "./commandCenterService.js";
import { getRenewalMatrix } from "./matrixService.js";
import { mergeCenterAndMatrix, adaptStudentDetail } from "../adapters/studentAdapter.js";

export async function getUnifiedStudents() {
  const [centerItems, matrixPayload] = await Promise.all([
    listCommandCenterStudents(),
    getRenewalMatrix("all"),
  ]);

  return mergeCenterAndMatrix(centerItems, matrixPayload.items);
}

export async function getUnifiedStudentDetail(studentId) {
  const [detail, matrixPayload] = await Promise.all([
    getCommandCenterStudentDetail(studentId),
    getRenewalMatrix("all"),
  ]);

  const matrixItem =
    matrixPayload.items.find((item) => String(item.id) === String(studentId)) ||
    null;

  return adaptStudentDetail(detail, matrixItem);
}

