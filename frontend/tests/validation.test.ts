import test, { describe } from "node:test";
import assert from "node:assert/strict";
import {
  validateRetinalImageFile,
  formatBytes,
  MAX_FILE_SIZE_BYTES,
  ALLOWED_EXTENSIONS,
  ALLOWED_MIME_TYPES,
} from "../lib/validation.js";

describe("Retinal Image Upload Validation", () => {
  test("rejects null or undefined file input", () => {
    const res1 = validateRetinalImageFile(null);
    assert.equal(res1.isValid, false);
    assert.match(res1.errorMessage || "", /No image file selected/i);

    const res2 = validateRetinalImageFile(undefined);
    assert.equal(res2.isValid, false);
    assert.match(res2.errorMessage || "", /No image file selected/i);
  });

  test("accepts valid PNG retinal images within size limit", () => {
    const mockFile = {
      name: "retina_sample_01.png",
      type: "image/png",
      size: 250 * 1024, // 250 KB
    } as unknown as File;

    const res = validateRetinalImageFile(mockFile);
    assert.equal(res.isValid, true);
    assert.equal(res.errorMessage, undefined);
  });

  test("accepts valid JPG and JPEG retinal images within size limit", () => {
    const mockJpg = {
      name: "fundus_scan.jpg",
      type: "image/jpeg",
      size: 500 * 1024, // 500 KB
    } as unknown as File;

    const resJpg = validateRetinalImageFile(mockJpg);
    assert.equal(resJpg.isValid, true);

    const mockJpeg = {
      name: "macula_view.JPEG",
      type: "image/jpeg",
      size: 1.2 * 1024 * 1024, // 1.2 MB
    } as unknown as File;

    const resJpeg = validateRetinalImageFile(mockJpeg);
    assert.equal(resJpeg.isValid, true);
  });

  test("rejects unsupported file formats and MIME types", () => {
    const badFiles = [
      { name: "document.pdf", type: "application/pdf", size: 1024 },
      { name: "scan.bmp", type: "image/bmp", size: 1024 },
      { name: "notes.txt", type: "text/plain", size: 500 },
      { name: "retina.gif", type: "image/gif", size: 2048 },
    ];

    for (const f of badFiles) {
      const res = validateRetinalImageFile(f as unknown as File);
      assert.equal(res.isValid, false, `Expected ${f.name} to be rejected`);
      assert.match(res.errorMessage || "", /Unsupported file format/i);
    }
  });

  test("rejects empty 0-byte files", () => {
    const emptyFile = {
      name: "empty_fundus.png",
      type: "image/png",
      size: 0,
    } as unknown as File;

    const res = validateRetinalImageFile(emptyFile);
    assert.equal(res.isValid, false);
    assert.match(res.errorMessage || "", /empty \(0 bytes\)/i);
  });

  test("rejects oversized files exceeding 25 MB", () => {
    const giantFile = {
      name: "huge_raw_retina.png",
      type: "image/png",
      size: MAX_FILE_SIZE_BYTES + 1024, // > 25 MB
    } as unknown as File;

    const res = validateRetinalImageFile(giantFile);
    assert.equal(res.isValid, false);
    assert.match(res.errorMessage || "", /exceeds the 25 MB limit/i);
  });

  test("formatBytes converts sizes correctly", () => {
    assert.equal(formatBytes(0), "0 Bytes");
    assert.equal(formatBytes(1024), "1 KB");
    assert.equal(formatBytes(1024 * 1024), "1 MB");
    assert.equal(formatBytes(1.5 * 1024 * 1024), "1.5 MB");
  });

  test("allowed types and extensions contain standard fundus formats", () => {
    assert.ok(ALLOWED_EXTENSIONS.includes(".png"));
    assert.ok(ALLOWED_EXTENSIONS.includes(".jpg"));
    assert.ok(ALLOWED_EXTENSIONS.includes(".jpeg"));
    assert.ok(ALLOWED_MIME_TYPES.includes("image/png"));
    assert.ok(ALLOWED_MIME_TYPES.includes("image/jpeg"));
  });
});
