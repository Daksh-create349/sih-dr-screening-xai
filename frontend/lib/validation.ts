import { ValidationResult } from "@/types/screening";

export const ALLOWED_MIME_TYPES = [
  "image/png",
  "image/jpeg",
  "image/jpg",
];

export const ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg"];

// Maximum acceptable fundus photography upload size (25 MB)
export const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024;

export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export function validateRetinalImageFile(file?: File | null): ValidationResult {
  if (!file) {
    return {
      isValid: false,
      errorMessage: "No image file selected. Please select a retinal photograph.",
    };
  }

  // Check file extension
  const lowerName = file.name.toLowerCase();
  const hasValidExt = ALLOWED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));

  // Check MIME type
  const hasValidMime = ALLOWED_MIME_TYPES.includes(file.type.toLowerCase());

  if (!hasValidExt && !hasValidMime) {
    return {
      isValid: false,
      errorMessage:
        "Unsupported file format. Please upload a standard color retinal fundus image in PNG or JPG/JPEG format.",
    };
  }

  // Check file size bounds
  if (file.size <= 0) {
    return {
      isValid: false,
      errorMessage: "The selected file is empty (0 bytes).",
    };
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return {
      isValid: false,
      errorMessage: `File size exceeds the 25 MB limit (${formatBytes(file.size)}). Please upload a compressed or standard resolution fundus image.`,
    };
  }

  return { isValid: true };
}

/**
 * Loads image into an HTMLImageElement to verify decodeability and extract dimensions.
 */
export function extractImageDimensions(
  file: File
): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
      const dimensions = {
        width: img.naturalWidth || img.width,
        height: img.naturalHeight || img.height,
      };
      URL.revokeObjectURL(objectUrl);
      resolve(dimensions);
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(
        new Error(
          "Corrupted or unreadable image file. Unable to decode retinal fundus photograph."
        )
      );
    };

    img.src = objectUrl;
  });
}
