import test, { describe } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { validateRetinalImageFile } from "../lib/validation.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REAL_IMAGES_DIR = path.resolve(__dirname, "../../data/real_retinal_images");

describe("Real Retinal Images Validation", () => {
  test("verifies all 9 real retinal images pass client validation", () => {
    assert.ok(fs.existsSync(REAL_IMAGES_DIR), `Directory not found: ${REAL_IMAGES_DIR}`);

    const files = fs
      .readdirSync(REAL_IMAGES_DIR)
      .filter((f) => /\.(png|jpe?g)$/i.test(f));

    assert.equal(files.length, 9, `Expected 9 real retinal images, found ${files.length}`);

    for (const filename of files) {
      const filePath = path.join(REAL_IMAGES_DIR, filename);
      const stat = fs.statSync(filePath);

      const mimeType = filename.endsWith(".png") ? "image/png" : "image/jpeg";
      const simulatedFile = {
        name: filename,
        size: stat.size,
        type: mimeType,
      } as unknown as File;

      const result = validateRetinalImageFile(simulatedFile);
      assert.equal(
        result.isValid,
        true,
        `Real image ${filename} failed validation: ${result.errorMessage}`
      );
      assert.equal(result.errorMessage, undefined);
    }
  });
});
